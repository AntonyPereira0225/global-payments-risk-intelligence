# SQL

BigQuery SQL used to build the analytical warehouse and reporting layer will live here.

Planned sequence:

```text
sql/
|-- 01_create_dimensions.sql
|-- 02_create_fact_transactions.sql
|-- 03_data_quality_checks.sql
|-- 04_payment_performance.sql
|-- 05_decline_analysis.sql
|-- 06_merchant_intelligence.sql
|-- 07_customer_segments.sql
|-- 08_fraud_risk.sql
`-- 09_anomaly_detection.sql
```

Queries will favour documented, reusable logic using CTEs, window functions, conditional aggregation and appropriate BigQuery partition/filter patterns. Performance claims will only be added after measured query comparisons.
