"""Analyse the champion logistic-regression fraud model.

All data is synthetic. This script:
1. reloads the saved Logistic Regression pipeline,
2. extracts model coefficients for explainability,
3. selects score thresholds from the November validation set at fixed review
   capacities, and
4. applies those validation-derived thresholds unchanged to the untouched
   December test set.

The goal is to describe operational trade-offs (review volume, precision,
recall and fraud capture) rather than present the F1-maximising threshold as a
production recommendation.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from google.cloud import bigquery
from sklearn.metrics import precision_score, recall_score

PROJECT_ID = "global-payments-intelligence"
VIEW = f"`{PROJECT_ID}.payments_intelligence.vw_fraud_model_features`"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
MODEL_PATH = OUTPUT_DIR / "logistic_fraud_pipeline.joblib"

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
REVIEW_CAPACITIES = [0.005, 0.01, 0.02, 0.05, 0.10]


def load_split(client: bigquery.Client, split: str) -> pd.DataFrame:
    if split == "validation":
        where = """
        transaction_date >= DATE '2025-11-01'
        AND transaction_date < DATE '2025-12-01'
        """
    elif split == "test":
        where = "transaction_date >= DATE '2025-12-01'"
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
    df = client.query(query).to_dataframe()
    print(
        f"{split}: {len(df):,} rows | "
        f"fraud={int(df[TARGET].sum()):,} | "
        f"rate={df[TARGET].mean():.4%}"
    )
    return df


def extract_coefficients(pipeline) -> pd.DataFrame:
    preprocessor = pipeline.named_steps["preprocessor"]
    model = pipeline.named_steps["model"]

    feature_names = preprocessor.get_feature_names_out()
    coefficients = model.coef_.ravel()

    if len(feature_names) != len(coefficients):
        raise RuntimeError("Feature-name and coefficient counts do not match.")

    df = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": coefficients,
            "odds_ratio": np.exp(coefficients),
            "absolute_coefficient": np.abs(coefficients),
        }
    )
    return df.sort_values("absolute_coefficient", ascending=False).reset_index(drop=True)


def threshold_for_capacity(scores: np.ndarray, capacity: float) -> float:
    """Return the validation score cutoff that flags approximately capacity."""
    if not 0 < capacity < 1:
        raise ValueError("capacity must be between 0 and 1")
    return float(np.quantile(scores, 1.0 - capacity, method="higher"))


def evaluate_operating_point(
    y_true: np.ndarray,
    scores: np.ndarray,
    threshold: float,
    requested_capacity: float,
) -> dict[str, float | int]:
    pred = scores >= threshold
    flagged = int(pred.sum())
    fraud_total = int(y_true.sum())
    fraud_captured = int(y_true[pred].sum())

    return {
        "requested_review_capacity": float(requested_capacity),
        "threshold": float(threshold),
        "rows": int(len(y_true)),
        "flagged_transactions": flagged,
        "actual_flag_rate": float(pred.mean()),
        "fraud_transactions": fraud_total,
        "fraud_captured": fraud_captured,
        "fraud_capture_rate": float(fraud_captured / fraud_total) if fraud_total else 0.0,
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "lift_vs_random": (
            float((fraud_captured / fraud_total) / pred.mean())
            if fraud_total and pred.mean() > 0
            else 0.0
        ),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Saved Logistic Regression pipeline not found: {MODEL_PATH}. "
            "Run models/train_logistic_baseline.py first."
        )

    print(f"Loading model: {MODEL_PATH}")
    pipeline = joblib.load(MODEL_PATH)

    coefficient_table = extract_coefficients(pipeline)
    coefficient_table.to_csv(
        OUTPUT_DIR / "logistic_feature_coefficients.csv",
        index=False,
    )

    client = bigquery.Client(project=PROJECT_ID)
    validation = load_split(client, "validation")
    test = load_split(client, "test")

    validation_scores = pipeline.predict_proba(validation[FEATURES])[:, 1]
    test_scores = pipeline.predict_proba(test[FEATURES])[:, 1]
    validation_y = validation[TARGET].astype(bool).to_numpy()
    test_y = test[TARGET].astype(bool).to_numpy()

    validation_rows: list[dict[str, float | int]] = []
    test_rows: list[dict[str, float | int]] = []

    for capacity in REVIEW_CAPACITIES:
        threshold = threshold_for_capacity(validation_scores, capacity)
        validation_rows.append(
            evaluate_operating_point(
                validation_y,
                validation_scores,
                threshold,
                capacity,
            )
        )
        test_rows.append(
            evaluate_operating_point(
                test_y,
                test_scores,
                threshold,
                capacity,
            )
        )

    validation_table = pd.DataFrame(validation_rows)
    test_table = pd.DataFrame(test_rows)

    validation_table.to_csv(
        OUTPUT_DIR / "logistic_operating_points_validation.csv",
        index=False,
    )
    test_table.to_csv(
        OUTPUT_DIR / "logistic_operating_points_test.csv",
        index=False,
    )

    top_positive = (
        coefficient_table.sort_values("coefficient", ascending=False)
        .head(15)[["feature", "coefficient", "odds_ratio"]]
        .to_dict(orient="records")
    )
    top_negative = (
        coefficient_table.sort_values("coefficient", ascending=True)
        .head(15)[["feature", "coefficient", "odds_ratio"]]
        .to_dict(orient="records")
    )

    summary = {
        "model": "LogisticRegression",
        "threshold_selection": (
            "Each operating threshold is selected only from November validation "
            "scores at a fixed review capacity, then applied unchanged to December."
        ),
        "review_capacities": REVIEW_CAPACITIES,
        "validation_operating_points": validation_rows,
        "test_operating_points": test_rows,
        "top_positive_coefficients": top_positive,
        "top_negative_coefficients": top_negative,
        "interpretation_note": (
            "Coefficients describe the fitted synthetic-data model. Categorical "
            "coefficients are relative to the omitted one-hot reference category; "
            "numeric coefficients are on standardized inputs. They are associations "
            "within the simulated generator, not causal or real-world estimates."
        ),
    }

    with (OUTPUT_DIR / "logistic_operational_summary.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2)

    print("\nValidation-derived operating points applied to December test")
    print(
        test_table[
            [
                "requested_review_capacity",
                "threshold",
                "actual_flag_rate",
                "fraud_captured",
                "fraud_capture_rate",
                "precision",
                "lift_vs_random",
            ]
        ].to_string(index=False)
    )

    print("\nTop positive Logistic Regression coefficients")
    print(
        coefficient_table.sort_values("coefficient", ascending=False)
        .head(10)[["feature", "coefficient", "odds_ratio"]]
        .to_string(index=False)
    )

    print("\nTop negative Logistic Regression coefficients")
    print(
        coefficient_table.sort_values("coefficient", ascending=True)
        .head(10)[["feature", "coefficient", "odds_ratio"]]
        .to_string(index=False)
    )

    print(f"\nOutputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
