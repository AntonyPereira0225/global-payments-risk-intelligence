"""Generate deterministic synthetic dimension tables for the payments platform."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    COUNTRIES,
    CUSTOMER_RISK_WEIGHTS,
    CUSTOMER_SEGMENTS,
    DATE_END,
    DATE_START,
    DIMENSION_DIR,
    MERCHANT_CATEGORIES,
    MERCHANT_SIZE_WEIGHTS,
    MERCHANT_TIER_BY_SIZE,
    N_CUSTOMERS,
    N_DEVICES,
    N_MERCHANTS,
    SAMPLE_DIR,
    SEED,
)


def _normalise(weights: list[float] | np.ndarray) -> np.ndarray:
    values = np.asarray(weights, dtype=float)
    return values / values.sum()


def _random_dates(
    rng: np.random.Generator,
    n: int,
    start: str,
    end: str,
) -> pd.DatetimeIndex:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    span_days = (end_ts - start_ts).days
    offsets = rng.integers(0, span_days + 1, size=n)
    return pd.DatetimeIndex(start_ts + pd.to_timedelta(offsets, unit="D"))


def build_country_dimension() -> pd.DataFrame:
    country = pd.DataFrame(COUNTRIES).copy()
    country["market_weight"] = _normalise(country.pop("weight").to_numpy())
    return country[
        [
            "country_id",
            "country_name",
            "region",
            "currency",
            "market_weight",
            "risk_multiplier",
        ]
    ]


def build_date_dimension() -> pd.DataFrame:
    dates = pd.date_range(DATE_START, DATE_END, freq="D")
    df = pd.DataFrame({"date": dates})
    df["date_id"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["day"] = df["date"].dt.day
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.month_name().str[:3]
    df["quarter"] = "Q" + df["date"].dt.quarter.astype(str)
    df["year"] = df["date"].dt.year
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6])

    # Used by the transaction generator to create realistic seasonality.
    month_factor = df["month"].map(
        {1: 0.90, 2: 0.92, 3: 0.98, 4: 1.00, 5: 1.02, 6: 1.05,
         7: 1.08, 8: 1.07, 9: 1.00, 10: 1.06, 11: 1.18, 12: 1.28}
    )
    weekday_factor = np.where(df["is_weekend"], 1.08, 1.00)
    df["transaction_weight"] = month_factor * weekday_factor
    df["transaction_weight"] = df["transaction_weight"] / df["transaction_weight"].sum()

    return df[
        [
            "date_id",
            "date",
            "day",
            "week",
            "month",
            "month_name",
            "quarter",
            "year",
            "day_of_week",
            "is_weekend",
            "transaction_weight",
        ]
    ]


def build_customer_dimension(
    rng: np.random.Generator,
    country: pd.DataFrame,
) -> pd.DataFrame:
    country_ids = country["country_id"].to_numpy()
    country_p = country["market_weight"].to_numpy()

    segment_names = np.array(list(CUSTOMER_SEGMENTS))
    segment_p = _normalise([CUSTOMER_SEGMENTS[s]["weight"] for s in segment_names])

    risk_names = np.array(list(CUSTOMER_RISK_WEIGHTS))
    risk_p = _normalise(list(CUSTOMER_RISK_WEIGHTS.values()))

    signup_dates = _random_dates(rng, N_CUSTOMERS, "2019-01-01", DATE_END)
    reference_date = pd.Timestamp(DATE_END)
    tenure_months = np.maximum(
        0,
        ((reference_date - signup_dates).days / 30.4375).astype(int),
    )

    # Preserve the original random-number sequence used for the validated
    # portfolio dataset while no longer storing or using a demographic field.
    # This legacy draw is intentionally discarded.
    rng.choice(
        ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
        size=N_CUSTOMERS,
        p=[0.12, 0.28, 0.24, 0.18, 0.12, 0.06],
    )

    df = pd.DataFrame(
        {
            "customer_id": [f"C{i:07d}" for i in range(1, N_CUSTOMERS + 1)],
            "customer_segment": rng.choice(segment_names, size=N_CUSTOMERS, p=segment_p),
            "signup_date": signup_dates,
            "home_country": rng.choice(country_ids, size=N_CUSTOMERS, p=country_p),
            "account_tenure_months": tenure_months,
            "risk_segment": rng.choice(risk_names, size=N_CUSTOMERS, p=risk_p),
        }
    )

    # Transaction sampling weight is intentionally stored for reproducibility,
    # but is a synthetic modelling helper rather than a business KPI.
    df["transaction_propensity"] = df["customer_segment"].map(
        {k: v["transaction_multiplier"] for k, v in CUSTOMER_SEGMENTS.items()}
    )
    df["transaction_propensity"] = (
        df["transaction_propensity"] / df["transaction_propensity"].sum()
    )
    return df


def build_merchant_dimension(
    rng: np.random.Generator,
    country: pd.DataFrame,
) -> pd.DataFrame:
    country_ids = country["country_id"].to_numpy()
    country_p = country["market_weight"].to_numpy()

    categories = np.array(list(MERCHANT_CATEGORIES))
    category_p = _normalise([MERCHANT_CATEGORIES[c]["weight"] for c in categories])

    sizes = np.array(list(MERCHANT_SIZE_WEIGHTS))
    size_p = _normalise(list(MERCHANT_SIZE_WEIGHTS.values()))

    merchant_size = rng.choice(sizes, size=N_MERCHANTS, p=size_p)
    merchant_category = rng.choice(categories, size=N_MERCHANTS, p=category_p)
    merchant_country = rng.choice(country_ids, size=N_MERCHANTS, p=country_p)

    category_risk = pd.Series(merchant_category).map(
        {k: v["fraud_multiplier"] for k, v in MERCHANT_CATEGORIES.items()}
    ).to_numpy()
    country_risk_map = country.set_index("country_id")["risk_multiplier"].to_dict()
    country_risk = pd.Series(merchant_country).map(country_risk_map).to_numpy()
    risk_score = category_risk * country_risk * rng.lognormal(0.0, 0.12, N_MERCHANTS)
    risk_rating = np.select(
        [risk_score >= 1.45, risk_score >= 1.10],
        ["High", "Medium"],
        default="Low",
    )

    onboarding = _random_dates(rng, N_MERCHANTS, "2017-01-01", DATE_END)

    df = pd.DataFrame(
        {
            "merchant_id": [f"M{i:06d}" for i in range(1, N_MERCHANTS + 1)],
            "merchant_name": [f"Synthetic Merchant {i:04d}" for i in range(1, N_MERCHANTS + 1)],
            "merchant_category": merchant_category,
            "merchant_country": merchant_country,
            "merchant_size": merchant_size,
            "merchant_tier": pd.Series(merchant_size).map(MERCHANT_TIER_BY_SIZE).to_numpy(),
            "onboarding_date": onboarding,
            "merchant_risk_rating": risk_rating,
        }
    )

    size_multiplier = pd.Series(merchant_size).map(
        {"Small": 0.65, "Medium": 1.15, "Large": 2.0, "Enterprise": 3.4}
    ).to_numpy()
    category_multiplier = pd.Series(merchant_category).map(
        {k: max(0.55, v["weight"] * 8.0) for k, v in MERCHANT_CATEGORIES.items()}
    ).to_numpy()
    propensity = size_multiplier * category_multiplier * rng.lognormal(0.0, 0.35, N_MERCHANTS)
    df["transaction_propensity"] = propensity / propensity.sum()
    return df


def build_device_dimension(rng: np.random.Generator) -> pd.DataFrame:
    device_type = rng.choice(
        ["mobile", "desktop", "tablet", "point_of_sale"],
        size=N_DEVICES,
        p=[0.42, 0.25, 0.08, 0.25],
    )

    operating_system = np.empty(N_DEVICES, dtype=object)
    browser = np.empty(N_DEVICES, dtype=object)

    for dtype in np.unique(device_type):
        mask = device_type == dtype
        n = int(mask.sum())
        if dtype == "mobile":
            operating_system[mask] = rng.choice(["Android", "iOS"], n, p=[0.58, 0.42])
            browser[mask] = rng.choice(["App", "Chrome", "Safari"], n, p=[0.58, 0.25, 0.17])
        elif dtype == "desktop":
            operating_system[mask] = rng.choice(["Windows", "macOS", "Linux"], n, p=[0.62, 0.30, 0.08])
            browser[mask] = rng.choice(["Chrome", "Safari", "Edge", "Firefox"], n, p=[0.55, 0.18, 0.20, 0.07])
        elif dtype == "tablet":
            operating_system[mask] = rng.choice(["iPadOS", "Android"], n, p=[0.58, 0.42])
            browser[mask] = rng.choice(["App", "Safari", "Chrome"], n, p=[0.42, 0.35, 0.23])
        else:
            operating_system[mask] = "Embedded"
            browser[mask] = "Terminal"

    return pd.DataFrame(
        {
            "device_id": [f"D{i:07d}" for i in range(1, N_DEVICES + 1)],
            "device_type": device_type,
            "operating_system": operating_system,
            "browser": browser,
        }
    )


def _write_table(df: pd.DataFrame, name: str, sample_rows: int = 500) -> dict[str, int]:
    DIMENSION_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    parquet_path = DIMENSION_DIR / f"{name}.parquet"
    sample_path = SAMPLE_DIR / f"{name}_sample.csv"
    df.to_parquet(parquet_path, index=False)
    df.head(sample_rows).to_csv(sample_path, index=False)
    return {"rows": len(df), "columns": len(df.columns)}


def main() -> None:
    rng = np.random.default_rng(SEED)

    country = build_country_dimension()
    date = build_date_dimension()
    customer = build_customer_dimension(rng, country)
    merchant = build_merchant_dimension(rng, country)
    device = build_device_dimension(rng)

    manifest = {
        "dim_country": _write_table(country, "dim_country", len(country)),
        "dim_date": _write_table(date, "dim_date", len(date)),
        "dim_customer": _write_table(customer, "dim_customer"),
        "dim_merchant": _write_table(merchant, "dim_merchant"),
        "dim_device": _write_table(device, "dim_device"),
    }

    manifest_path = Path(DIMENSION_DIR).parent / "dimension_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Synthetic dimensions generated successfully.")
    for table, metadata in manifest.items():
        print(f"  {table}: {metadata['rows']:,} rows x {metadata['columns']} columns")
    print(f"Output: {DIMENSION_DIR}")


if __name__ == "__main__":
    main()
