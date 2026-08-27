# BigQuery Load Guide

Project ID: `global-payments-intelligence`  
Dataset: `payments_intelligence`  
Location: `EU`  
Cloud Storage bucket: `global-payments-intelligence-data-antony0225`

## Source files

The validated local dataset is generated under `data/generated/` and contains:

- `dimensions/dim_country.parquet`
- `dimensions/dim_date.parquet`
- `dimensions/dim_customer.parquet`
- `dimensions/dim_merchant.parquet`
- `dimensions/dim_device.parquet`
- `transactions/fact_transactions_part_001.parquet` through `fact_transactions_part_020.parquet`

The generated data itself is intentionally excluded from GitHub. Only the reproducible Python generator, small samples and documentation belong in the repository.

## Cloud Storage staging path

The validated Parquet files are staged in:

- `gs://global-payments-intelligence-data-antony0225/dimensions/`
- `gs://global-payments-intelligence-data-antony0225/transactions/`

The transaction fact is loaded from:

`gs://global-payments-intelligence-data-antony0225/transactions/fact_transactions_part_*.parquet`

## Recommended load path

1. In BigQuery, load all transaction Parquet parts into a single native table named `fact_transactions`.
2. Use Parquet schema inference.
3. Partition `fact_transactions` by `transaction_timestamp` using daily time-unit partitioning.
4. Cluster the fact table by `merchant_id`, `customer_id`, and `transaction_status`.
5. Load each dimension Parquet file into its matching native table: `dim_customer`, `dim_merchant`, `dim_device`, `dim_country`, and `dim_date`.
6. Run `sql/01_warehouse_validation.sql` and reconcile results to the local Python validation report.

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
