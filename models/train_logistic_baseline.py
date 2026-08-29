"""Train and evaluate a leakage-aware logistic-regression fraud baseline.

All data is synthetic. This script reads the curated BigQuery modelling view,
uses a chronological split, trains only on a deterministic sample of the
Jan-Oct period for local-memory efficiency, tunes a decision threshold on
November, and evaluates the untouched December test period.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from google.cloud import bigquery
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ID = "global-payments-intelligence"
VIEW = f"`{PROJECT_ID}.payments_intelligence.vw_fraud_model_features`"
SEED = 20260826
TRAIN_SAMPLE_MODULUS = 4  # ~25% of Jan-Oct rows, deterministic by transaction_id
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

NUMERIC_FEATURES = [
    "transaction_hour",
    "day_of_week_num",
    "transaction_month",
    "transaction_amount_usd",
    "processing_time_ms",
    "account_tenure_months",
]

CATEGORICAL_FEATURES = [
    "payment_method",
    "channel",
    "is_cross_border",
    "customer_segment",
    "customer_risk_segment",
    "merchant_category",
    "merchant_size",
    "merchant_tier",
    "merchant_risk_rating",
    "device_type",
    "operating_system",
    "transaction_region",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "is_fraud"


def load_split(client: bigquery.Client, split: str) -> pd.DataFrame:
    if split == "train":
        where = """
        transaction_date < DATE '2025-11-01'
        AND MOD(
          FARM_FINGERPRINT(CAST(transaction_id AS STRING)),
          @sample_modulus
        ) = 0
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "sample_modulus", "INT64", TRAIN_SAMPLE_MODULUS
                )
            ]
        )
    elif split == "validation":
        where = """
        transaction_date >= DATE '2025-11-01'
        AND transaction_date < DATE '2025-12-01'
        """
        job_config = None
    elif split == "test":
        where = "transaction_date >= DATE '2025-12-01'"
        job_config = None
    else:
        raise ValueError(f"Unknown split: {split}")

    selected = ",\n  ".join(["transaction_id", *FEATURES, TARGET])
    query = f"""
    SELECT
      {selected}
    FROM {VIEW}
    WHERE {where}
    """

    print(f"Loading {split} data from BigQuery...")
    df = client.query(query, job_config=job_config).to_dataframe()
    print(
        f"{split}: {len(df):,} rows | "
        f"fraud={int(df[TARGET].sum()):,} | "
        f"rate={df[TARGET].mean():.4%}"
    )
    return df


def build_pipeline() -> Pipeline:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=True),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ]
    )

    model = LogisticRegression(
        class_weight="balanced",
        solver="saga",
        max_iter=300,
        random_state=SEED,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def choose_threshold(y_true: np.ndarray, scores: np.ndarray) -> tuple[float, pd.DataFrame]:
    rows: list[dict[str, float]] = []
    for threshold in np.arange(0.05, 0.951, 0.01):
        pred = scores >= threshold
        rows.append(
            {
                "threshold": round(float(threshold), 2),
                "precision": precision_score(y_true, pred, zero_division=0),
                "recall": recall_score(y_true, pred, zero_division=0),
                "f1": f1_score(y_true, pred, zero_division=0),
                "flag_rate": float(pred.mean()),
            }
        )

    table = pd.DataFrame(rows)
    best = table.loc[table["f1"].idxmax()]
    return float(best["threshold"]), table


def capture_at_percent(y_true: np.ndarray, scores: np.ndarray, pct: float) -> float:
    n = max(1, int(len(scores) * pct))
    top_idx = np.argpartition(scores, -n)[-n:]
    total_fraud = int(y_true.sum())
    if total_fraud == 0:
        return 0.0
    return float(y_true[top_idx].sum() / total_fraud)


def evaluate(
    y_true: np.ndarray,
    scores: np.ndarray,
    threshold: float,
) -> dict[str, object]:
    pred = scores >= threshold
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[False, True]).ravel()

    return {
        "average_precision_pr_auc": float(average_precision_score(y_true, scores)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "threshold": float(threshold),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "flag_rate": float(pred.mean()),
        "capture_at_top_0_5_pct": capture_at_percent(y_true, scores, 0.005),
        "capture_at_top_1_pct": capture_at_percent(y_true, scores, 0.01),
        "capture_at_top_5_pct": capture_at_percent(y_true, scores, 0.05),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = bigquery.Client(project=PROJECT_ID)

    train = load_split(client, "train")
    validation = load_split(client, "validation")
    test = load_split(client, "test")

    pipeline = build_pipeline()
    print("Training logistic-regression baseline...")
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

    metadata = {
        "model": "LogisticRegression",
        "train_sampling": f"deterministic 1/{TRAIN_SAMPLE_MODULUS} sample of Jan-Oct",
        "train_rows": int(len(train)),
        "validation_rows": int(len(validation)),
        "test_rows": int(len(test)),
        "validation_selected_threshold": float(best_threshold),
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
    }

    threshold_table.to_csv(OUTPUT_DIR / "logistic_threshold_analysis.csv", index=False)
    with (OUTPUT_DIR / "logistic_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    joblib.dump(pipeline, OUTPUT_DIR / "logistic_fraud_pipeline.joblib")

    print("\nValidation metrics")
    print(json.dumps(validation_metrics, indent=2))
    print("\nUntouched December test metrics")
    print(json.dumps(test_metrics, indent=2))
    print(f"\nOutputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
