# Data Quality Notes

## Currency-normalisation issue caught by validation

During the first full 5,000,000-row pipeline run, the validation layer correctly failed the transaction amount check because some `transaction_amount_usd` values rounded to `0.00`.

### Root cause

Merchant-category spend profiles were configured using USD-like median values, but the first generator version treated those values as local-currency amounts and then multiplied them by the currency-to-USD factor. For low-value currencies such as NGN, KES, INR and JPY, small local values could therefore convert to less than one cent and round to zero.

This was not a validator defect. It exposed a modelling inconsistency in the synthetic-data generator.

### Fix

The generator now:

1. creates a category-sensitive transaction amount in USD-equivalent terms;
2. assigns the merchant's local currency from its country;
3. converts the USD-equivalent amount into the local transaction amount using illustrative static FX factors;
4. retains the original USD-equivalent amount as `transaction_amount_usd` for globally comparable analysis;
5. calculates fraud and approval behaviour using the corrected USD-equivalent value.

This approach preserves comparable transaction-value distributions across countries while still exposing a realistic local-currency transaction field.

## Why this matters

The failed validation run is intentionally documented because it demonstrates the role of automated data-quality gates in catching modelling errors before warehouse loading or dashboard development. The corrected pipeline must pass validation before downstream BigQuery and Power BI work is treated as trustworthy.

> Note: the FX factors are illustrative static conversion factors for this synthetic portfolio project. They are not live or historical market rates.
