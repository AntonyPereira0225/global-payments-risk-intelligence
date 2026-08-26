"""Validate generated dimensions and transaction Parquet files.

The validator produces a machine-readable JSON report and fails with a non-zero
exit code when critical quality rules are broken. It intentionally checks both
schema integrity and business logic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    DATA_DIR,
    DIMENSION_DIR,
    N_CUSTOMERS,
    N_DEVICES,
    N_MERCHANTS,
    N_TRANSACTIONS,
    TRANSACTION_DIR,
)


REQUIRED_TRANSACTION_COLUMNS = [
    "transaction_id",
    "transaction_timestamp",
    "customer_id",
    "merchant_id",
    "device_id",
    "country_id",
    "payment_method",
    "channel",
    "currency",
    "transaction_amount",
    "transaction_amount_usd",
    "transaction_status",
    "decline_reason",
    "is_cross_border",
    "is_fraud",
    "fraud_loss_amount_usd",
    "processing_time_ms",
]


class ValidationReport:
    def __init__(self) -> None:
        self.checks: list[dict[str, object]] = []

    def add(self, name: str, passed: bool, detail: str, severity: str = "critical") -> None:
        self.checks.append(
            {
                "check": name,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    @property
    def critical_failures(self) -> list[dict[str, object]]:
        return [
            c for c in self.checks
            if c["severity"] == "critical" and not c["passed"]
        ]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "PASS" if not self.critical_failures else "FAIL",
            "critical_failures": len(self.critical_failures),
            "checks": self.checks,
        }


def _read_dimension(name: str) -> pd.DataFrame:
    path = DIMENSION_DIR / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_parquet(path)


def validate_dimensions(report: ValidationReport) -> dict[str, pd.DataFrame]:
    expected = {
        "dim_customer": ("customer_id", N_CUSTOMERS),
        "dim_merchant": ("merchant_id", N_MERCHANTS),
        "dim_device": ("device_id", N_DEVICES),
        "dim_country": ("country_id", None),
        "dim_date": ("date_id", None),
    }

    dimensions: dict[str, pd.DataFrame] = {}
    for table, (pk, expected_rows) in expected.items():
        try:
            df = _read_dimension(table)
            dimensions[table] = df
        except FileNotFoundError:
            report.add(f"{table}: file exists", False, f"Missing {table}.parquet")
            continue

        report.add(
            f"{table}: primary key non-null",
            df[pk].notna().all(),
            f"null {pk} values={int(df[pk].isna().sum())}",
        )
        report.add(
            f"{table}: primary key unique",
            not df[pk].duplicated().any(),
            f"duplicate {pk} values={int(df[pk].duplicated().sum())}",
        )
        if expected_rows is not None:
            report.add(
                f"{table}: expected row count",
                len(df) == expected_rows,
                f"rows={len(df):,}; expected={expected_rows:,}",
            )

    return dimensions


def validate_transactions(
    report: ValidationReport,
    dimensions: dict[str, pd.DataFrame],
) -> dict[str, float | int]:
    files = sorted(TRANSACTION_DIR.glob("fact_transactions_part_*.parquet"))
    report.add(
        "fact_transactions: parquet parts exist",
        bool(files),
        f"parts={len(files)}",
    )
    if not files:
        return {}

    customer_ids = set(dimensions.get("dim_customer", pd.DataFrame()).get("customer_id", []))
    merchant_ids = set(dimensions.get("dim_merchant", pd.DataFrame()).get("merchant_id", []))
    device_ids = set(dimensions.get("dim_device", pd.DataFrame()).get("device_id", []))
    country_ids = set(dimensions.get("dim_country", pd.DataFrame()).get("country_id", []))

    total_rows = 0
    approved_rows = 0
    fraud_rows = 0
    cross_border_rows = 0
    total_amount_usd = 0.0
    total_fraud_loss_usd = 0.0
    min_id: int | None = None
    max_id: int | None = None
    previous_max_id = 0

    for path in files:
        df = pd.read_parquet(path)
        total_rows += len(df)

        missing_columns = [c for c in REQUIRED_TRANSACTION_COLUMNS if c not in df.columns]
        report.add(
            f"{path.name}: required columns",
            not missing_columns,
            "missing=" + (", ".join(missing_columns) if missing_columns else "none"),
        )
        if missing_columns:
            continue

        required_non_null = [
            c for c in REQUIRED_TRANSACTION_COLUMNS
            if c != "decline_reason"
        ]
        null_count = int(df[required_non_null].isna().sum().sum())
        report.add(
            f"{path.name}: required fields non-null",
            null_count == 0,
            f"null required values={null_count}",
        )

        duplicate_ids = int(df["transaction_id"].duplicated().sum())
        report.add(
            f"{path.name}: transaction_id unique within part",
            duplicate_ids == 0,
            f"duplicates={duplicate_ids}",
        )

        part_min = int(df["transaction_id"].min())
        part_max = int(df["transaction_id"].max())
        report.add(
            f"{path.name}: transaction_id sequence does not overlap prior part",
            part_min > previous_max_id,
            f"range={part_min:,}-{part_max:,}; prior_max={previous_max_id:,}",
        )
        previous_max_id = max(previous_max_id, part_max)
        min_id = part_min if min_id is None else min(min_id, part_min)
        max_id = part_max if max_id is None else max(max_id, part_max)

        valid_status = df["transaction_status"].isin(["approved", "declined"]).all()
        report.add(
            f"{path.name}: transaction_status domain",
            valid_status,
            "allowed=approved, declined",
        )

        decline_logic = (
            (df["transaction_status"].eq("approved") & df["decline_reason"].isna())
            | (df["transaction_status"].eq("declined") & df["decline_reason"].notna())
        ).all()
        report.add(
            f"{path.name}: decline reason logic",
            bool(decline_logic),
            "approved rows require no decline reason; declined rows require one",
        )

        amount_logic = (
            (df["transaction_amount"] > 0)
            & (df["transaction_amount_usd"] > 0)
        ).all()
        report.add(
            f"{path.name}: positive transaction amounts",
            bool(amount_logic),
            f"min_local={df['transaction_amount'].min():.2f}; min_usd={df['transaction_amount_usd'].min():.2f}",
        )

        loss_logic = (
            (df["fraud_loss_amount_usd"] >= 0)
            & np.where(
                df["is_fraud"] & df["transaction_status"].eq("approved"),
                df["fraud_loss_amount_usd"] > 0,
                df["fraud_loss_amount_usd"] == 0,
            )
        ).all()
        report.add(
            f"{path.name}: fraud loss logic",
            bool(loss_logic),
            "loss > 0 only for approved fraudulent transactions",
        )

        processing_logic = df["processing_time_ms"].between(90, 5000).all()
        report.add(
            f"{path.name}: processing time range",
            bool(processing_logic),
            f"min={int(df['processing_time_ms'].min())}; max={int(df['processing_time_ms'].max())}",
        )

        if customer_ids:
            invalid = int((~df["customer_id"].isin(customer_ids)).sum())
            report.add(
                f"{path.name}: customer foreign key",
                invalid == 0,
                f"invalid customer_id rows={invalid}",
            )
        if merchant_ids:
            invalid = int((~df["merchant_id"].isin(merchant_ids)).sum())
            report.add(
                f"{path.name}: merchant foreign key",
                invalid == 0,
                f"invalid merchant_id rows={invalid}",
            )
        if device_ids:
            invalid = int((~df["device_id"].isin(device_ids)).sum())
            report.add(
                f"{path.name}: device foreign key",
                invalid == 0,
                f"invalid device_id rows={invalid}",
            )
        if country_ids:
            invalid = int((~df["country_id"].isin(country_ids)).sum())
            report.add(
                f"{path.name}: country foreign key",
                invalid == 0,
                f"invalid country_id rows={invalid}",
            )

        approved_rows += int(df["transaction_status"].eq("approved").sum())
        fraud_rows += int(df["is_fraud"].sum())
        cross_border_rows += int(df["is_cross_border"].sum())
        total_amount_usd += float(df["transaction_amount_usd"].sum())
        total_fraud_loss_usd += float(df["fraud_loss_amount_usd"].sum())

    report.add(
        "fact_transactions: expected total row count",
        total_rows == N_TRANSACTIONS,
        f"rows={total_rows:,}; expected={N_TRANSACTIONS:,}",
    )
    report.add(
        "fact_transactions: global transaction_id range",
        min_id == 1 and max_id == N_TRANSACTIONS,
        f"min={min_id}; max={max_id}; expected=1-{N_TRANSACTIONS:,}",
    )

    if total_rows == 0:
        return {}

    metrics = {
        "transaction_rows": total_rows,
        "approval_rate": approved_rows / total_rows,
        "decline_rate": 1 - (approved_rows / total_rows),
        "fraud_rate": fraud_rows / total_rows,
        "cross_border_rate": cross_border_rows / total_rows,
        "transaction_value_usd": round(total_amount_usd, 2),
        "average_transaction_value_usd": round(total_amount_usd / total_rows, 2),
        "fraud_loss_usd": round(total_fraud_loss_usd, 2),
    }

    # Plausibility checks are warnings: they protect against accidental model
    # drift without pretending synthetic thresholds are real industry targets.
    report.add(
        "plausibility: approval rate",
        0.80 <= metrics["approval_rate"] <= 0.99,
        f"approval_rate={metrics['approval_rate']:.4%}",
        severity="warning",
    )
    report.add(
        "plausibility: fraud rate",
        0.0002 <= metrics["fraud_rate"] <= 0.03,
        f"fraud_rate={metrics['fraud_rate']:.4%}",
        severity="warning",
    )
    report.add(
        "plausibility: cross-border rate",
        0.03 <= metrics["cross_border_rate"] <= 0.45,
        f"cross_border_rate={metrics['cross_border_rate']:.4%}",
        severity="warning",
    )

    return metrics


def main() -> None:
    report = ValidationReport()
    dimensions = validate_dimensions(report)
    metrics = validate_transactions(report, dimensions)

    output = report.as_dict()
    output["summary_metrics"] = metrics
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    report_path = DATA_DIR / "validation_report.json"
    report_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"Validation status: {output['status']}")
    if metrics:
        print(f"Transactions: {metrics['transaction_rows']:,}")
        print(f"Approval rate: {metrics['approval_rate']:.2%}")
        print(f"Fraud rate: {metrics['fraud_rate']:.3%}")
        print(f"Cross-border rate: {metrics['cross_border_rate']:.2%}")
        print(f"Transaction value (USD): ${metrics['transaction_value_usd']:,.2f}")
        print(f"Fraud loss (USD): ${metrics['fraud_loss_usd']:,.2f}")
    print(f"Report: {report_path}")

    if report.critical_failures:
        print("Critical failures:")
        for check in report.critical_failures:
            print(f"  - {check['check']}: {check['detail']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
