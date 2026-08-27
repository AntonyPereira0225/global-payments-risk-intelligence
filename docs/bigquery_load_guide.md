# BigQuery Load Guide

Project ID: `global-payments-intelligence`  
Dataset: `payments_intelligence`  
Location: `EU`

## Source files

The validated local dataset is generated under `data/generated/` and contains:

- `dimensions/dim_country.parquet`
- `dimensions/dim_date.parquet`
- `dimensions/dim_customer.parquet`
- `dimensions/dim_merchant.parquet`
- `dimensions/dim_device.parquet`
- `transactions/fact_transactions_part_001.parquet` through `fact_transactions_part_020.parquet`

The generated data itself is intentionally excluded from GitHub. Only the reproducible Python generator, small samples and documentation belong in the repository.

## Recommended load path

Use Google Cloud Storage as a staging layer before BigQuery:

1. Create a Cloud Storage bucket in the `EU` location.
2. Upload the `dimensions` and `transactions` folders from `data/generated/`.
3. In BigQuery, load each dimension Parquet file into its matching table.
4. Load all transaction parts into a single `fact_transactions` table with a wildcard URI such as:
   `gs://YOUR_BUCKET/transactions/fact_transactions_part_*.parquet`
5. Use Parquet schema autodetection.
6. Partition `fact_transactions` by `transaction_timestamp` using daily time-unit partitioning.
7. Cluster the fact table by `merchant_id`, `customer_id`, and `transaction_status`.
8. Run `sql/01_warehouse_validation.sql` and reconcile results to the local Python validation report.

## Expected row counts

| Table | Expected rows |
|---|---:|
| fact_transactions | 5,000,000 |
| dim_customer | 150,000 |
| dim_merchant | 8,000 |
| dim_device | 75,000 |
| dim_country | 25 |
| dim_date | 365 |

## Expected core metrics

The BigQuery warehouse should reconcile to the passed Python validation run:

- Approval rate: 93.95%
- Decline rate: 6.05%
- Fraud rate: 0.203%
- Cross-border rate: 15.51%
- Transaction value: $496,439,922.54
- Average transaction value: $99.29
- Fraud loss: $766,088.56

Do not continue to downstream analytical views or Power BI until row counts, foreign keys and business-rule checks reconcile.
