# Data

This project uses **synthetic payment data only**. No real customer, cardholder, merchant or payment-network records are used.

The full synthetic dataset is reproducible from the Python code in `src/` using a fixed random seed and explicit configuration. Multi-million-row generated outputs are intentionally excluded from GitHub.

## Local generated structure

```text
data/
`-- generated/
    |-- dimensions/
    |   |-- dim_country.parquet
    |   |-- dim_date.parquet
    |   |-- dim_customer.parquet
    |   |-- dim_merchant.parquet
    |   `-- dim_device.parquet
    |-- transactions/
    |   |-- fact_transactions_part_001.parquet
    |   |-- ...
    |   `-- fact_transactions_part_020.parquet
    |-- sample/
    |   |-- fact_transactions_sample.csv
    |   `-- dimension samples
    |-- dimension_manifest.json
    |-- transaction_manifest.json
    `-- validation_report.json
```

## Default scale

- 150,000 customers
- 8,000 merchants
- 75,000 devices
- 25 countries
- 5,000,000 transactions
- 12 months of activity

Transactions are written in 250,000-row Parquet chunks with Zstandard compression so the complete fact table never needs to be held in memory at once.

## Data design

The synthetic generator intentionally creates business relationships rather than independent random columns. Customer segment influences channel usage and cross-border behaviour; merchant category influences amount distribution and risk; fraud probability responds to customer, merchant, channel, geography, time and amount risk factors; approval probability responds to transaction context and fraud status.

The stored synthetic customer schema is deliberately limited to attributes needed for the stated analytics objectives. It does not store age or other demographic attributes. Customer, merchant and device identifiers are synthetic surrogate keys rather than real-world identities.

`transaction_amount` represents the transaction in its local merchant currency. `transaction_amount_usd` is an illustrative standardized reporting value generated using static synthetic conversion factors. These factors are not live market rates and are included only to support comparable global analytics.

## Version-control policy

`data/generated/.gitignore` excludes generated output from Git. The code and documentation are the source of truth. Small curated samples may be added later only when they materially improve portfolio review or testing.
