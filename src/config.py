"""Configuration for the synthetic global payments data generator.

The project uses deterministic synthetic data only. No real customer, merchant,
or payment-card data is used.
"""

from pathlib import Path

SEED = 20260826

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "generated"
DIMENSION_DIR = DATA_DIR / "dimensions"
TRANSACTION_DIR = DATA_DIR / "transactions"
SAMPLE_DIR = DATA_DIR / "sample"

N_CUSTOMERS = 150_000
N_MERCHANTS = 8_000
N_DEVICES = 75_000
N_TRANSACTIONS = 5_000_000
TRANSACTION_CHUNK_SIZE = 250_000
SAMPLE_TRANSACTION_ROWS = 25_000

DATE_START = "2025-01-01"
DATE_END = "2025-12-31"

COUNTRIES = [
    {"country_id": "IRL", "country_name": "Ireland", "region": "Europe", "currency": "EUR", "weight": 0.065, "risk_multiplier": 0.85},
    {"country_id": "GBR", "country_name": "United Kingdom", "region": "Europe", "currency": "GBP", "weight": 0.090, "risk_multiplier": 0.90},
    {"country_id": "USA", "country_name": "United States", "region": "North America", "currency": "USD", "weight": 0.170, "risk_multiplier": 0.95},
    {"country_id": "CAN", "country_name": "Canada", "region": "North America", "currency": "CAD", "weight": 0.045, "risk_multiplier": 0.90},
    {"country_id": "DEU", "country_name": "Germany", "region": "Europe", "currency": "EUR", "weight": 0.060, "risk_multiplier": 0.85},
    {"country_id": "FRA", "country_name": "France", "region": "Europe", "currency": "EUR", "weight": 0.055, "risk_multiplier": 0.90},
    {"country_id": "ESP", "country_name": "Spain", "region": "Europe", "currency": "EUR", "weight": 0.040, "risk_multiplier": 0.95},
    {"country_id": "ITA", "country_name": "Italy", "region": "Europe", "currency": "EUR", "weight": 0.040, "risk_multiplier": 1.00},
    {"country_id": "NLD", "country_name": "Netherlands", "region": "Europe", "currency": "EUR", "weight": 0.025, "risk_multiplier": 0.85},
    {"country_id": "SWE", "country_name": "Sweden", "region": "Europe", "currency": "SEK", "weight": 0.018, "risk_multiplier": 0.80},
    {"country_id": "POL", "country_name": "Poland", "region": "Europe", "currency": "PLN", "weight": 0.025, "risk_multiplier": 0.95},
    {"country_id": "AUS", "country_name": "Australia", "region": "Oceania", "currency": "AUD", "weight": 0.035, "risk_multiplier": 0.90},
    {"country_id": "NZL", "country_name": "New Zealand", "region": "Oceania", "currency": "NZD", "weight": 0.010, "risk_multiplier": 0.85},
    {"country_id": "JPN", "country_name": "Japan", "region": "Asia Pacific", "currency": "JPY", "weight": 0.040, "risk_multiplier": 0.80},
    {"country_id": "SGP", "country_name": "Singapore", "region": "Asia Pacific", "currency": "SGD", "weight": 0.020, "risk_multiplier": 0.80},
    {"country_id": "IND", "country_name": "India", "region": "Asia Pacific", "currency": "INR", "weight": 0.070, "risk_multiplier": 1.05},
    {"country_id": "ARE", "country_name": "United Arab Emirates", "region": "Middle East", "currency": "AED", "weight": 0.030, "risk_multiplier": 0.95},
    {"country_id": "SAU", "country_name": "Saudi Arabia", "region": "Middle East", "currency": "SAR", "weight": 0.020, "risk_multiplier": 1.00},
    {"country_id": "BRA", "country_name": "Brazil", "region": "Latin America", "currency": "BRL", "weight": 0.035, "risk_multiplier": 1.20},
    {"country_id": "MEX", "country_name": "Mexico", "region": "Latin America", "currency": "MXN", "weight": 0.025, "risk_multiplier": 1.15},
    {"country_id": "ZAF", "country_name": "South Africa", "region": "Africa", "currency": "ZAR", "weight": 0.020, "risk_multiplier": 1.15},
    {"country_id": "KEN", "country_name": "Kenya", "region": "Africa", "currency": "KES", "weight": 0.010, "risk_multiplier": 1.20},
    {"country_id": "NGA", "country_name": "Nigeria", "region": "Africa", "currency": "NGN", "weight": 0.012, "risk_multiplier": 1.30},
    {"country_id": "CHE", "country_name": "Switzerland", "region": "Europe", "currency": "CHF", "weight": 0.015, "risk_multiplier": 0.80},
    {"country_id": "NOR", "country_name": "Norway", "region": "Europe", "currency": "NOK", "weight": 0.010, "risk_multiplier": 0.80},
]

MERCHANT_CATEGORIES = {
    "Grocery": {"weight": 0.18, "median_amount": 42.0, "sigma": 0.55, "fraud_multiplier": 0.70, "approval_delta": 0.010},
    "Restaurants": {"weight": 0.13, "median_amount": 35.0, "sigma": 0.60, "fraud_multiplier": 0.75, "approval_delta": 0.005},
    "Retail": {"weight": 0.14, "median_amount": 70.0, "sigma": 0.75, "fraud_multiplier": 1.00, "approval_delta": 0.000},
    "Travel": {"weight": 0.07, "median_amount": 260.0, "sigma": 0.85, "fraud_multiplier": 1.45, "approval_delta": -0.020},
    "Hotels": {"weight": 0.06, "median_amount": 180.0, "sigma": 0.80, "fraud_multiplier": 1.25, "approval_delta": -0.010},
    "Digital Goods": {"weight": 0.07, "median_amount": 28.0, "sigma": 0.90, "fraud_multiplier": 1.75, "approval_delta": -0.025},
    "Electronics": {"weight": 0.07, "median_amount": 220.0, "sigma": 0.90, "fraud_multiplier": 1.55, "approval_delta": -0.020},
    "Subscription Services": {"weight": 0.06, "median_amount": 18.0, "sigma": 0.45, "fraud_multiplier": 0.90, "approval_delta": 0.005},
    "Fuel": {"weight": 0.07, "median_amount": 58.0, "sigma": 0.45, "fraud_multiplier": 0.80, "approval_delta": 0.010},
    "Healthcare": {"weight": 0.05, "median_amount": 95.0, "sigma": 0.70, "fraud_multiplier": 0.65, "approval_delta": 0.010},
    "Entertainment": {"weight": 0.05, "median_amount": 45.0, "sigma": 0.75, "fraud_multiplier": 1.10, "approval_delta": -0.005},
    "Professional Services": {"weight": 0.05, "median_amount": 150.0, "sigma": 0.85, "fraud_multiplier": 1.00, "approval_delta": -0.005},
}

CUSTOMER_SEGMENTS = {
    "Mass": {"weight": 0.58, "transaction_multiplier": 0.90, "cross_border_rate": 0.08},
    "Affluent": {"weight": 0.22, "transaction_multiplier": 1.25, "cross_border_rate": 0.18},
    "Digital Native": {"weight": 0.15, "transaction_multiplier": 1.35, "cross_border_rate": 0.14},
    "Frequent Traveller": {"weight": 0.05, "transaction_multiplier": 1.55, "cross_border_rate": 0.42},
}

CUSTOMER_RISK_WEIGHTS = {"Low": 0.79, "Medium": 0.19, "High": 0.02}
MERCHANT_SIZE_WEIGHTS = {"Small": 0.62, "Medium": 0.27, "Large": 0.09, "Enterprise": 0.02}
MERCHANT_TIER_BY_SIZE = {"Small": "Standard", "Medium": "Growth", "Large": "Strategic", "Enterprise": "Strategic"}

CHANNELS = ["card_present", "web", "in_app"]
PAYMENT_METHODS = ["credit_card", "debit_card", "digital_wallet", "bank_transfer"]
DECLINE_REASONS = [
    "insufficient_funds",
    "do_not_honor",
    "suspected_fraud",
    "expired_card",
    "issuer_unavailable",
    "limit_exceeded",
]

BASE_APPROVAL_RATE = 0.945
BASE_FRAUD_RATE = 0.0018

# Relative hourly activity profile. Values are normalized before sampling.
HOURLY_ACTIVITY = [
    0.35, 0.25, 0.20, 0.18, 0.20, 0.30,
    0.55, 0.80, 1.00, 1.15, 1.25, 1.30,
    1.35, 1.30, 1.25, 1.30, 1.45, 1.60,
    1.70, 1.65, 1.50, 1.25, 0.90, 0.60,
]
