-- Payment performance reporting view
-- BigQuery Standard SQL

CREATE OR REPLACE VIEW `global-payments-intelligence.payments_intelligence.vw_payment_performance_daily` AS
WITH daily AS (
  SELECT
    DATE(t.transaction_timestamp) AS transaction_date,
    t.country_id,
    c.country_name,
    c.region,
    t.channel,
    t.payment_method,
    COUNT(*) AS transaction_count,
    SUM(t.transaction_amount_usd) AS transaction_value_usd,
    AVG(t.transaction_amount_usd) AS average_transaction_value_usd,
    COUNTIF(t.transaction_status = 'approved') AS approved_transactions,
    COUNTIF(t.transaction_status = 'declined') AS declined_transactions,
    COUNTIF(t.is_fraud) AS fraud_transactions,
    SUM(t.fraud_loss_amount_usd) AS fraud_loss_usd,
    COUNTIF(t.is_cross_border) AS cross_border_transactions,
    AVG(t.processing_time_ms) AS average_processing_time_ms
  FROM `global-payments-intelligence.payments_intelligence.fact_transactions` AS t
  LEFT JOIN `global-payments-intelligence.payments_intelligence.dim_country` AS c
    ON t.country_id = c.country_id
  GROUP BY 1,2,3,4,5,6
)
SELECT
  *,
  SAFE_DIVIDE(approved_transactions, transaction_count) AS approval_rate,
  SAFE_DIVIDE(declined_transactions, transaction_count) AS decline_rate,
  SAFE_DIVIDE(fraud_transactions, transaction_count) AS fraud_rate,
  SAFE_DIVIDE(cross_border_transactions, transaction_count) AS cross_border_rate
FROM daily;
