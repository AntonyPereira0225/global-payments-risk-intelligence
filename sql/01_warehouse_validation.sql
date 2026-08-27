-- Post-load validation for the BigQuery warehouse.
-- Run after all six source tables are loaded.

-- 1. Row-count checks
SELECT 'fact_transactions' AS table_name, COUNT(*) AS row_count
FROM `global-payments-intelligence.payments_intelligence.fact_transactions`
UNION ALL
SELECT 'dim_customer', COUNT(*)
FROM `global-payments-intelligence.payments_intelligence.dim_customer`
UNION ALL
SELECT 'dim_merchant', COUNT(*)
FROM `global-payments-intelligence.payments_intelligence.dim_merchant`
UNION ALL
SELECT 'dim_device', COUNT(*)
FROM `global-payments-intelligence.payments_intelligence.dim_device`
UNION ALL
SELECT 'dim_country', COUNT(*)
FROM `global-payments-intelligence.payments_intelligence.dim_country`
UNION ALL
SELECT 'dim_date', COUNT(*)
FROM `global-payments-intelligence.payments_intelligence.dim_date`
ORDER BY table_name;

-- Expected validated counts:
-- fact_transactions = 5,000,000
-- dim_customer      = 150,000
-- dim_merchant      = 8,000
-- dim_device        = 75,000
-- dim_country       = 25
-- dim_date          = 365

-- 2. Core KPI reconciliation with the Python validation layer
SELECT
  COUNT(*) AS transactions,
  ROUND(100 * SAFE_DIVIDE(COUNTIF(transaction_status = 'approved'), COUNT(*)), 2) AS approval_rate_pct,
  ROUND(100 * SAFE_DIVIDE(COUNTIF(transaction_status = 'declined'), COUNT(*)), 2) AS decline_rate_pct,
  ROUND(100 * SAFE_DIVIDE(COUNTIF(is_fraud), COUNT(*)), 3) AS fraud_rate_pct,
  ROUND(100 * SAFE_DIVIDE(COUNTIF(is_cross_border), COUNT(*)), 2) AS cross_border_rate_pct,
  ROUND(SUM(transaction_amount_usd), 2) AS transaction_value_usd,
  ROUND(AVG(transaction_amount_usd), 2) AS average_transaction_value_usd,
  ROUND(SUM(fraud_loss_amount_usd), 2) AS fraud_loss_usd
FROM `global-payments-intelligence.payments_intelligence.fact_transactions`;

-- Expected values from the passed local validation run:
-- transactions                 5,000,000
-- approval_rate_pct            93.95
-- decline_rate_pct              6.05
-- fraud_rate_pct                0.203
-- cross_border_rate_pct        15.51
-- transaction_value_usd   496,439,922.54
-- average_transaction_value_usd 99.29
-- fraud_loss_usd              766,088.56

-- 3. Referential-integrity checks. Each result should be zero.
SELECT
  COUNTIF(c.customer_id IS NULL) AS invalid_customer_fk,
  COUNTIF(m.merchant_id IS NULL) AS invalid_merchant_fk,
  COUNTIF(d.device_id IS NULL) AS invalid_device_fk,
  COUNTIF(g.country_id IS NULL) AS invalid_country_fk
FROM `global-payments-intelligence.payments_intelligence.fact_transactions` f
LEFT JOIN `global-payments-intelligence.payments_intelligence.dim_customer` c
  USING (customer_id)
LEFT JOIN `global-payments-intelligence.payments_intelligence.dim_merchant` m
  USING (merchant_id)
LEFT JOIN `global-payments-intelligence.payments_intelligence.dim_device` d
  USING (device_id)
LEFT JOIN `global-payments-intelligence.payments_intelligence.dim_country` g
  USING (country_id);

-- 4. Business-rule checks. Each result should be zero.
SELECT
  COUNTIF(transaction_amount <= 0 OR transaction_amount_usd <= 0) AS non_positive_amounts,
  COUNTIF(transaction_status = 'approved' AND decline_reason IS NOT NULL) AS approved_with_decline_reason,
  COUNTIF(transaction_status = 'declined' AND decline_reason IS NULL) AS declined_without_reason,
  COUNTIF(NOT is_fraud AND fraud_loss_amount_usd != 0) AS non_fraud_with_loss,
  COUNTIF(is_fraud AND transaction_status = 'declined' AND fraud_loss_amount_usd != 0) AS declined_fraud_with_loss
FROM `global-payments-intelligence.payments_intelligence.fact_transactions`;
