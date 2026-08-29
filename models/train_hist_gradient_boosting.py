"""Train and evaluate a nonlinear histogram gradient-boosting fraud model.

All data is synthetic. This script deliberately reuses the exact chronological
splits, deterministic Jan-Oct training sample, leakage-safe feature list and
evaluation helpers from ``train_logistic_baseline.py`` so the model comparison
is like-for-like.
"""

from __future__ import annotations

import json

import joblib
import numpy as np
from google.cloud import bigquery
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

from train_logistic_baseline import (
    CATEGORICAL_FEATURES,
    FEATURES,
    NUMERIC_FEATURES,
    OUTPUT_DIR,
    PROJECT_ID,
    SEED,
    TARGET,
    TRAIN_SAMPLE_MODULUS,
    choose_threshold,
    evaluate,
    load_split,
)


def build_pipeline() -> Pipeline:
    """Build a memory-conscious nonlinear model with native categorical splits."""
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "ordinal",
                OrdinalEncoder(
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                    encoded_missing_value=-1,
                    dtype=np.float64,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        sparse_threshold=0.0,
    )

    # ColumnTransformer outputs numeric columns first, followed by encoded
    # categorical columns. HistGradientBoosting can therefore treat the latter
    # as categorical rather than imposing a false numeric ordering.
    categorical_mask = [False] * len(NUMERIC_FEATURES) + [True] * len(
        CATEGORICAL_FEATURES
    )

    model = HistGradientBoostingClassifier(
        loss="log_loss",
        learning_rate=0.08,
        max_iter=250,
        max_leaf_nodes=31,
        min_samples_leaf=50,
        l2_regularization=1.0,
        class_weight="balanced",
        categorical_features=categorical_mask,
        early_stopping=True,
        validation_fraction=0.10,
        n_iter_no_change=20,
        random_state=SEED,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = bigquery.Client(project=PROJECT_ID)

    train = load_split(client, "train")
    validation = load_split(client, "validation")
    test = load_split(client, "test")

    pipeline = build_pipeline()
    print("Training histogram gradient-boosting model...")
    pipeline.fit(train[FEATURES], train[TARGET].astype(bool))

    validation_scores = pipeline.predict_proba(validation[FEATURES])[:, 1]
    best_threshold, threshold_table = choose_threshold(
        validation[TARGET].astype(bool).to_numpy(),
        validation_scores,
    )

    validation_metrics = evaluate(
        validation[TARGET].astype(bool).to_numpy(),
        validation_scores,
        best_threshold,
    )

    test_scores = pipeline.predict_proba(test[FEATURES])[:, 1]
    test_metrics = evaluate(
        test[TARGET].astype(bool).to_numpy(),
        test_scores,
        best_threshold,
    )

    fitted_model = pipeline.named_steps["model"]
    metadata = {
        "model": "HistGradientBoostingClassifier",
        "train_sampling": f"deterministic 1/{TRAIN_SAMPLE_MODULUS} sample of Jan-Oct",
        "train_rows": int(len(train)),
        "validation_rows": int(len(validation)),
        "test_rows": int(len(test)),
        "iterations_fitted": int(fitted_model.n_iter_),
        "validation_selected_threshold": float(best_threshold),
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
    }

    threshold_table.to_csv(
        OUTPUT_DIR / "hist_gradient_boosting_threshold_analysis.csv",
        index=False,
    )
    with (OUTPUT_DIR / "hist_gradient_boosting_metrics.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(metadata, f, indent=2)
    joblib.dump(
        pipeline,
        OUTPUT_DIR / "hist_gradient_boosting_fraud_pipeline.joblib",
    )

    print("\nValidation metrics")
    print(json.dumps(validation_metrics, indent=2))
    print("\nUntouched December test metrics")
    print(json.dumps(test_metrics, indent=2))
    print(f"\nIterations fitted: {fitted_model.n_iter_}")
    print(f"Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
