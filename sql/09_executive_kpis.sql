-- Executive monthly KPI view with month-on-month movement
-- BigQuery Standard SQL

CREATE OR REPLACE VIEW `global-payments-intelligence.payments_intelligence.vw_executive_kpis_monthly` AS
WITH monthly AS (
  SELECT
    DATE_TRUNC(DATE(transaction_timestamp), MONTH) AS month,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount_usd) AS transaction_value_usd,
    AVG(transaction_amount_usd) AS average_transaction_value_usd,
    SAFE_DIVIDE(COUNTIF(transaction_status = 'approved'), COUNT(*)) AS approval_rate,
    SAFE_DIVIDE(COUNTIF(transaction_status = 'declined'), COUNT(*)) AS decline_rate,
    SAFE_DIVIDE(COUNTIF(is_fraud), COUNT(*)) AS fraud_rate,
    SUM(fraud_loss_amount_usd) AS fraud_loss_usd,
    SAFE_DIVIDE(COUNTIF(is_cross_border), COUNT(*)) AS cross_border_rate,
    COUNT(DISTINCT customer_id) AS active_customers,
    COUNT(DISTINCT merchant_id) AS active_merchants,
    AVG(processing_time_ms) AS average_processing_time_ms
  FROM `global-payments-intelligence.payments_intelligence.fact_transactions`
  GROUP BY 1
),
lagged AS (
  SELECT
    *,
    LAG(transaction_count) OVER (ORDER BY month) AS prior_transaction_count,
    LAG(transaction_value_usd) OVER (ORDER BY month) AS prior_transaction_value_usd,
    LAG(approval_rate) OVER (ORDER BY month) AS prior_approval_rate,
    LAG(fraud_loss_usd) OVER (ORDER BY month) AS prior_fraud_loss_usd
  FROM monthly
)
SELECT
  *,
  SAFE_DIVIDE(transaction_count - prior_transaction_count, prior_transaction_count) AS transaction_count_mom_change,
  SAFE_DIVIDE(transaction_value_usd - prior_transaction_value_usd, prior_transaction_value_usd) AS transaction_value_mom_change,
  approval_rate - prior_approval_rate AS approval_rate_mom_point_change,
  SAFE_DIVIDE(fraud_loss_usd - prior_fraud_loss_usd, prior_fraud_loss_usd) AS fraud_loss_mom_change
FROM lagged;
