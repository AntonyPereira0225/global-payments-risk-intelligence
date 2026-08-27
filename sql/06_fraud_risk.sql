-- Fraud-risk segmentation view
-- BigQuery Standard SQL

CREATE OR REPLACE VIEW `global-payments-intelligence.payments_intelligence.vw_fraud_risk_segments` AS
SELECT
  m.merchant_category,
  m.merchant_risk_rating,
  c.risk_segment AS customer_risk_segment,
  t.channel,
  t.payment_method,
  t.is_cross_border,
  COUNT(*) AS transaction_count,
  SUM(t.transaction_amount_usd) AS transaction_value_usd,
  COUNTIF(t.is_fraud) AS fraud_transactions,
  SAFE_DIVIDE(COUNTIF(t.is_fraud), COUNT(*)) AS fraud_rate,
  SUM(t.fraud_loss_amount_usd) AS fraud_loss_usd,
  SAFE_DIVIDE(SUM(t.fraud_loss_amount_usd), SUM(t.transaction_amount_usd)) AS fraud_loss_rate,
  SAFE_DIVIDE(COUNTIF(t.transaction_status = 'declined'), COUNT(*)) AS decline_rate,
  AVG(t.processing_time_ms) AS average_processing_time_ms
FROM `global-payments-intelligence.payments_intelligence.fact_transactions` AS t
JOIN `global-payments-intelligence.payments_intelligence.dim_merchant` AS m
  ON t.merchant_id = m.merchant_id
JOIN `global-payments-intelligence.payments_intelligence.dim_customer` AS c
  ON t.customer_id = c.customer_id
GROUP BY 1,2,3,4,5,6;
