# SQL

BigQuery SQL used to build, validate and analyse the payments warehouse lives here.

Current / planned sequence:

```text
sql/
|-- 00_dataset_setup.sql
|-- 01_warehouse_validation.sql
|-- 02_payment_performance.sql
|-- 03_decline_analysis.sql
|-- 04_merchant_intelligence.sql
|-- 05_customer_analytics.sql
|-- 06_fraud_risk.sql
|-- 07_transaction_velocity.sql
|-- 08_anomaly_detection.sql
`-- 09_executive_kpis.sql
```

The project uses BigQuery Standard SQL and will favour reusable logic using CTEs, window functions, conditional aggregation, `LAG`, ranking functions, rolling metrics, percentiles and partition-aware filters.

The source warehouse is `global-payments-intelligence.payments_intelligence`. Downstream analytics should only be treated as valid after `01_warehouse_validation.sql` reconciles BigQuery to the passed local Python validation results.

Performance or optimisation claims will only be documented after measured query comparisons.
