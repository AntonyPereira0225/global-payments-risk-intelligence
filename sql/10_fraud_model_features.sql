-- Fraud modelling feature view
-- BigQuery Standard SQL
--
-- Purpose:
-- Create a leakage-aware feature set for the Python fraud-risk model.
-- All data is synthetic. The label is `is_fraud`.
--
-- Explicitly excluded from predictive features because they are identifiers
-- or post-outcome fields:
--   transaction_status, decline_reason, fraud_loss_amount_usd,
--   customer_id, merchant_id, device_id.
-- The cleaned customer schema intentionally stores no age or demographic
-- attribute for this portfolio objective.
-- transaction_id is retained only as a row identifier and must not be used as
-- a predictive feature.

CREATE OR REPLACE VIEW `global-payments-intelligence.payments_intelligence.vw_fraud_model_features` AS
SELECT
  f.transaction_id,
  f.transaction_timestamp,
  DATE(f.transaction_timestamp) AS transaction_date,
  EXTRACT(HOUR FROM f.transaction_timestamp) AS transaction_hour,
  EXTRACT(DAYOFWEEK FROM f.transaction_timestamp) AS day_of_week_num,
  EXTRACT(MONTH FROM f.transaction_timestamp) AS transaction_month,

  f.transaction_amount_usd,
  f.payment_method,
  f.channel,
  f.is_cross_border,
  f.processing_time_ms,

  c.customer_segment,
  c.account_tenure_months,
  c.risk_segment AS customer_risk_segment,

  m.merchant_category,
  m.merchant_size,
  m.merchant_tier,
  m.merchant_risk_rating,

  d.device_type,
  d.operating_system,

  co.region AS transaction_region,

  f.is_fraud
FROM `global-payments-intelligence.payments_intelligence.fact_transactions` AS f
LEFT JOIN `global-payments-intelligence.payments_intelligence.dim_customer` AS c
  ON f.customer_id = c.customer_id
LEFT JOIN `global-payments-intelligence.payments_intelligence.dim_merchant` AS m
  ON f.merchant_id = m.merchant_id
LEFT JOIN `global-payments-intelligence.payments_intelligence.dim_device` AS d
  ON f.device_id = d.device_id
LEFT JOIN `global-payments-intelligence.payments_intelligence.dim_country` AS co
  ON f.country_id = co.country_id;
