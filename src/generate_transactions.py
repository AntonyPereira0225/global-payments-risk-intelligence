"""Generate a large synthetic global payments fact table in Parquet chunks.

The behavioural relationships in this generator are intentional: customer
segment influences channel/cross-border usage, merchant category influences
amounts, and fraud/approval probabilities respond to risk factors. This makes
later SQL and BI analysis meaningful rather than purely random.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    BASE_APPROVAL_RATE,
    BASE_FRAUD_RATE,
    CUSTOMER_SEGMENTS,
    DATE_END,
    DIMENSION_DIR,
    HOURLY_ACTIVITY,
    MERCHANT_CATEGORIES,
    N_TRANSACTIONS,
    SAMPLE_DIR,
    SAMPLE_TRANSACTION_ROWS,
    SEED,
    TRANSACTION_CHUNK_SIZE,
    TRANSACTION_DIR,
)

# Illustrative static conversion factors used only to make global synthetic
# transaction values comparable in one reporting currency. They are not
# intended to represent live or historical FX rates.
FX_TO_USD = {
    "USD": 1.0000, "EUR": 1.1000, "GBP": 1.2700, "CAD": 0.7400,
    "SEK": 0.0950, "PLN": 0.2500, "AUD": 0.6600, "NZD": 0.6100,
    "JPY": 0.0067, "SGD": 0.7400, "INR": 0.0120, "AED": 0.2723,
    "SAR": 0.2667, "BRL": 0.2000, "MXN": 0.0580, "ZAR": 0.0550,
    "KES": 0.0077, "NGN": 0.00065, "CHF": 1.1300, "NOK": 0.0940,
}


def _normalise(values: np.ndarray) -> np.ndarray:
    values = values.astype(float)
    return values / values.sum()


def _load_dimensions() -> tuple[pd.DataFrame, ...]:
    required = [
        "dim_country.parquet",
        "dim_date.parquet",
        "dim_customer.parquet",
        "dim_merchant.parquet",
        "dim_device.parquet",
    ]
    missing = [name for name in required if not (DIMENSION_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Missing dimension files: " + ", ".join(missing) +
            ". Run `python src/generate_dimensions.py` first."
        )

    return tuple(pd.read_parquet(DIMENSION_DIR / name) for name in required)


def _channel_for_customers(
    rng: np.random.Generator,
    segments: np.ndarray,
) -> np.ndarray:
    channel = np.empty(len(segments), dtype=object)
    profiles = {
        "Mass": (["card_present", "web", "in_app"], [0.54, 0.28, 0.18]),
        "Affluent": (["card_present", "web", "in_app"], [0.44, 0.32, 0.24]),
        "Digital Native": (["card_present", "web", "in_app"], [0.20, 0.34, 0.46]),
        "Frequent Traveller": (["card_present", "web", "in_app"], [0.34, 0.35, 0.31]),
    }
    for segment, (choices, probs) in profiles.items():
        mask = segments == segment
        channel[mask] = rng.choice(choices, size=int(mask.sum()), p=probs)
    return channel


def _payment_method_for_channel(
    rng: np.random.Generator,
    channel: np.ndarray,
) -> np.ndarray:
    method = np.empty(len(channel), dtype=object)
    profiles = {
        "card_present": (
            ["credit_card", "debit_card", "digital_wallet"],
            [0.40, 0.45, 0.15],
        ),
        "web": (
            ["credit_card", "debit_card", "digital_wallet", "bank_transfer"],
            [0.45, 0.25, 0.20, 0.10],
        ),
        "in_app": (
            ["credit_card", "debit_card", "digital_wallet", "bank_transfer"],
            [0.30, 0.18, 0.50, 0.02],
        ),
    }
    for value, (choices, probs) in profiles.items():
        mask = channel == value
        method[mask] = rng.choice(choices, size=int(mask.sum()), p=probs)
    return method


def _select_devices(
    rng: np.random.Generator,
    channel: np.ndarray,
    device: pd.DataFrame,
) -> np.ndarray:
    pools = {
        "card_present": device.index[device["device_type"] == "point_of_sale"].to_numpy(),
        "web": device.index[device["device_type"].isin(["desktop", "mobile", "tablet"])].to_numpy(),
        "in_app": device.index[device["device_type"].isin(["mobile", "tablet"])].to_numpy(),
    }
    selected = np.empty(len(channel), dtype=np.int64)
    for value, pool in pools.items():
        mask = channel == value
        selected[mask] = rng.choice(pool, size=int(mask.sum()))
    return selected


def _select_merchants(
    rng: np.random.Generator,
    customer_country: np.ndarray,
    cross_border_requested: np.ndarray,
    merchant: pd.DataFrame,
) -> np.ndarray:
    """Select local or foreign merchants while preserving merchant propensity."""
    n = len(customer_country)
    selected = np.empty(n, dtype=np.int64)
    merchant_country = merchant["merchant_country"].to_numpy()
    global_p = _normalise(merchant["transaction_propensity"].to_numpy())
    all_idx = merchant.index.to_numpy()

    # Local transactions are sampled from merchants in the customer's country.
    for country in np.unique(customer_country):
        local_tx_mask = (customer_country == country) & (~cross_border_requested)
        local_n = int(local_tx_mask.sum())
        if local_n == 0:
            continue
        pool = merchant.index[merchant["merchant_country"] == country].to_numpy()
        if len(pool) == 0:
            selected[local_tx_mask] = rng.choice(all_idx, size=local_n, p=global_p)
            continue
        p = _normalise(merchant.loc[pool, "transaction_propensity"].to_numpy())
        selected[local_tx_mask] = rng.choice(pool, size=local_n, p=p)

    # Cross-border transactions use the global merchant distribution and are
    # re-sampled only when the merchant happens to share the customer country.
    cross_mask = cross_border_requested
    cross_n = int(cross_mask.sum())
    if cross_n:
        positions = np.flatnonzero(cross_mask)
        picks = rng.choice(all_idx, size=cross_n, p=global_p)
        same_country = merchant_country[picks] == customer_country[positions]
        while same_country.any():
            picks[same_country] = rng.choice(all_idx, size=int(same_country.sum()), p=global_p)
            same_country = merchant_country[picks] == customer_country[positions]
        selected[positions] = picks

    return selected


def _transaction_amounts(
    rng: np.random.Generator,
    categories: np.ndarray,
) -> np.ndarray:
    amounts = np.empty(len(categories), dtype=float)
    for category, cfg in MERCHANT_CATEGORIES.items():
        mask = categories == category
        n = int(mask.sum())
        if n:
            amounts[mask] = rng.lognormal(
                mean=math.log(cfg["median_amount"]),
                sigma=cfg["sigma"],
                size=n,
            )
    return np.clip(amounts, 1.0, 10_000.0).round(2)


def _decline_reasons(
    rng: np.random.Generator,
    approved: np.ndarray,
    is_fraud: np.ndarray,
) -> np.ndarray:
    reasons = np.full(len(approved), None, dtype=object)
    declined = ~approved
    fraud_declined = declined & is_fraud
    normal_declined = declined & (~is_fraud)

    if fraud_declined.any():
        reasons[fraud_declined] = rng.choice(
            ["suspected_fraud", "do_not_honor", "limit_exceeded"],
            size=int(fraud_declined.sum()),
            p=[0.78, 0.17, 0.05],
        )
    if normal_declined.any():
        reasons[normal_declined] = rng.choice(
            [
                "insufficient_funds",
                "do_not_honor",
                "suspected_fraud",
                "expired_card",
                "issuer_unavailable",
                "limit_exceeded",
            ],
            size=int(normal_declined.sum()),
            p=[0.38, 0.24, 0.08, 0.08, 0.12, 0.10],
        )
    return reasons


def _build_chunk(
    rng: np.random.Generator,
    start_id: int,
    n: int,
    country: pd.DataFrame,
    date: pd.DataFrame,
    customer: pd.DataFrame,
    merchant: pd.DataFrame,
    device: pd.DataFrame,
) -> pd.DataFrame:
    customer_p = _normalise(customer["transaction_propensity"].to_numpy())
    customer_idx = rng.choice(customer.index.to_numpy(), size=n, p=customer_p)

    customer_id = customer.loc[customer_idx, "customer_id"].to_numpy()
    customer_country = customer.loc[customer_idx, "home_country"].to_numpy()
    customer_segment = customer.loc[customer_idx, "customer_segment"].to_numpy()
    customer_risk = customer.loc[customer_idx, "risk_segment"].to_numpy()

    channel = _channel_for_customers(rng, customer_segment)
    payment_method = _payment_method_for_channel(rng, channel)

    segment_cross_rate = pd.Series(customer_segment).map(
        {k: v["cross_border_rate"] for k, v in CUSTOMER_SEGMENTS.items()}
    ).to_numpy()
    digital_uplift = np.where(np.isin(channel, ["web", "in_app"]), 0.025, 0.0)
    cross_probability = np.clip(segment_cross_rate + digital_uplift, 0.02, 0.60)
    cross_requested = rng.random(n) < cross_probability

    merchant_idx = _select_merchants(
        rng, customer_country, cross_requested, merchant
    )
    merchant_id = merchant.loc[merchant_idx, "merchant_id"].to_numpy()
    merchant_country = merchant.loc[merchant_idx, "merchant_country"].to_numpy()
    merchant_category = merchant.loc[merchant_idx, "merchant_category"].to_numpy()
    merchant_risk = merchant.loc[merchant_idx, "merchant_risk_rating"].to_numpy()
    is_cross_border = merchant_country != customer_country

    device_idx = _select_devices(rng, channel, device)
    device_id = device.loc[device_idx, "device_id"].to_numpy()

    date_p = _normalise(date["transaction_weight"].to_numpy())
    date_idx = rng.choice(date.index.to_numpy(), size=n, p=date_p)
    base_dates = pd.to_datetime(date.loc[date_idx, "date"].to_numpy())

    hour_p = _normalise(np.asarray(HOURLY_ACTIVITY, dtype=float))
    hours = rng.choice(np.arange(24), size=n, p=hour_p)
    minutes = rng.integers(0, 60, size=n)
    seconds = rng.integers(0, 60, size=n)
    timestamps = (
        base_dates
        + pd.to_timedelta(hours, unit="h")
        + pd.to_timedelta(minutes, unit="m")
        + pd.to_timedelta(seconds, unit="s")
    )

    amount = _transaction_amounts(rng, merchant_category)
    country_currency = country.set_index("country_id")["currency"].to_dict()
    currency = pd.Series(merchant_country).map(country_currency).to_numpy()
    fx = pd.Series(currency).map(FX_TO_USD).fillna(1.0).to_numpy()
    amount_usd = np.round(amount * fx, 2)

    category_fraud = pd.Series(merchant_category).map(
        {k: v["fraud_multiplier"] for k, v in MERCHANT_CATEGORIES.items()}
    ).to_numpy()
    customer_risk_factor = pd.Series(customer_risk).map(
        {"Low": 0.75, "Medium": 1.45, "High": 3.00}
    ).to_numpy()
    merchant_risk_factor = pd.Series(merchant_risk).map(
        {"Low": 0.80, "Medium": 1.25, "High": 1.90}
    ).to_numpy()
    night_factor = np.where((hours <= 5) | (hours >= 23), 1.45, 1.0)
    cross_factor = np.where(is_cross_border, 1.75, 1.0)
    channel_factor = np.where(channel == "card_present", 0.72, 1.28)
    amount_factor = np.where(amount_usd >= 750, 1.65, np.where(amount_usd >= 300, 1.25, 1.0))

    fraud_probability = (
        BASE_FRAUD_RATE
        * category_fraud
        * customer_risk_factor
        * merchant_risk_factor
        * night_factor
        * cross_factor
        * channel_factor
        * amount_factor
    )
    fraud_probability = np.clip(fraud_probability, 0.00015, 0.08)
    is_fraud = rng.random(n) < fraud_probability

    category_approval_delta = pd.Series(merchant_category).map(
        {k: v["approval_delta"] for k, v in MERCHANT_CATEGORIES.items()}
    ).to_numpy()
    approval_probability = np.full(n, BASE_APPROVAL_RATE, dtype=float)
    approval_probability += category_approval_delta
    approval_probability += np.where(channel == "card_present", 0.012, -0.004)
    approval_probability += np.where(is_cross_border, -0.030, 0.0)
    approval_probability += np.where(customer_risk == "High", -0.050, 0.0)
    approval_probability += np.where(merchant_risk == "High", -0.035, 0.0)
    approval_probability += np.where(amount_usd >= 750, -0.025, 0.0)
    approval_probability += np.where(is_fraud, -0.30, 0.0)
    approval_probability = np.clip(approval_probability, 0.45, 0.995)

    approved = rng.random(n) < approval_probability
    transaction_status = np.where(approved, "approved", "declined")
    decline_reason = _decline_reasons(rng, approved, is_fraud)

    loss_fraction = rng.uniform(0.55, 1.00, size=n)
    fraud_loss_amount_usd = np.where(
        is_fraud & approved,
        amount_usd * loss_fraction,
        0.0,
    ).round(2)

    processing_time_ms = rng.lognormal(mean=math.log(420), sigma=0.38, size=n)
    processing_time_ms *= np.where(is_cross_border, 1.20, 1.0)
    processing_time_ms *= np.where(payment_method == "bank_transfer", 1.45, 1.0)
    processing_time_ms *= np.where(channel == "web", 1.08, 1.0)
    processing_time_ms = np.clip(processing_time_ms, 90, 5_000).round().astype(int)

    return pd.DataFrame(
        {
            "transaction_id": np.arange(start_id, start_id + n, dtype=np.int64),
            "transaction_timestamp": timestamps,
            "customer_id": customer_id,
            "merchant_id": merchant_id,
            "device_id": device_id,
            "country_id": merchant_country,
            "payment_method": payment_method,
            "channel": channel,
            "currency": currency,
            "transaction_amount": amount,
            "transaction_amount_usd": amount_usd,
            "transaction_status": transaction_status,
            "decline_reason": decline_reason,
            "is_cross_border": is_cross_border,
            "is_fraud": is_fraud,
            "fraud_loss_amount_usd": fraud_loss_amount_usd,
            "processing_time_ms": processing_time_ms,
        }
    )


def main() -> None:
    rng = np.random.default_rng(SEED + 1)
    country, date, customer, merchant, device = _load_dimensions()

    TRANSACTION_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    # Remove only prior generated transaction parts so reruns are deterministic.
    for old_file in TRANSACTION_DIR.glob("fact_transactions_part_*.parquet"):
        old_file.unlink()

    n_chunks = math.ceil(N_TRANSACTIONS / TRANSACTION_CHUNK_SIZE)
    generated = 0
    sample_written = False
    parts: list[dict[str, int | str]] = []

    for part in range(n_chunks):
        n = min(TRANSACTION_CHUNK_SIZE, N_TRANSACTIONS - generated)
        start_id = generated + 1
        chunk = _build_chunk(
            rng,
            start_id,
            n,
            country,
            date,
            customer,
            merchant,
            device,
        )

        filename = f"fact_transactions_part_{part + 1:03d}.parquet"
        path = TRANSACTION_DIR / filename
        chunk.to_parquet(path, index=False, compression="zstd")

        if not sample_written:
            chunk.head(SAMPLE_TRANSACTION_ROWS).to_csv(
                SAMPLE_DIR / "fact_transactions_sample.csv",
                index=False,
            )
            sample_written = True

        generated += n
        parts.append({"file": filename, "rows": n, "start_transaction_id": start_id})
        print(f"Generated {generated:,}/{N_TRANSACTIONS:,} transactions")

    manifest = {
        "seed": SEED + 1,
        "date_end": DATE_END,
        "expected_rows": N_TRANSACTIONS,
        "chunk_size": TRANSACTION_CHUNK_SIZE,
        "parts": parts,
    }
    (TRANSACTION_DIR.parent / "transaction_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(f"Completed: {generated:,} synthetic transactions")
    print(f"Parquet output: {TRANSACTION_DIR}")
    print(f"Sample CSV: {SAMPLE_DIR / 'fact_transactions_sample.csv'}")


if __name__ == "__main__":
    main()
