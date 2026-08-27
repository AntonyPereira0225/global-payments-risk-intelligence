-- Merchant intelligence view combining commercial value and risk indicators
-- BigQuery Standard SQL

CREATE OR REPLACE VIEW `global-payments-intelligence.payments_intelligence.vw_merchant_intelligence` AS
WITH merchant_agg AS (
  SELECT
    t.merchant_id,
    m.merchant_name,
    m.merchant_category,
    m.merchant_country,
    m.merchant_size,
    m.merchant_tier,
    m.merchant_risk_rating,
    COUNT(*) AS transaction_count,
    SUM(t.transaction_amount_usd) AS transaction_value_usd,
    AVG(t.transaction_amount_usd) AS average_transaction_value_usd,
    SAFE_DIVIDE(COUNTIF(t.transaction_status = 'approved'), COUNT(*)) AS approval_rate,
    SAFE_DIVIDE(COUNTIF(t.transaction_status = 'declined'), COUNT(*)) AS decline_rate,
    SAFE_DIVIDE(COUNTIF(t.is_fraud), COUNT(*)) AS fraud_rate,
    SUM(t.fraud_loss_amount_usd) AS fraud_loss_usd,
    SAFE_DIVIDE(COUNTIF(t.is_cross_border), COUNT(*)) AS cross_border_rate,
    AVG(t.processing_time_ms) AS average_processing_time_ms
  FROM `global-payments-intelligence.payments_intelligence.fact_transactions` AS t
  JOIN `global-payments-intelligence.payments_intelligence.dim_merchant` AS m
    ON t.merchant_id = m.merchant_id
  GROUP BY 1,2,3,4,5,6,7
),
ranked AS (
  SELECT
    *,
    PERCENT_RANK() OVER (ORDER BY transaction_value_usd) AS value_percentile,
    PERCENT_RANK() OVER (ORDER BY fraud_loss_usd) AS fraud_loss_percentile,
    PERCENT_RANK() OVER (ORDER BY decline_rate) AS decline_percentile
  FROM merchant_agg
)
SELECT
  *,
  CASE
    WHEN value_percentile >= 0.75
      AND (merchant_risk_rating = 'High' OR fraud_loss_percentile >= 0.75 OR decline_percentile >= 0.75)
      THEN 'High Value / Elevated Risk'
    WHEN value_percentile >= 0.75 THEN 'High Value'
    WHEN merchant_risk_rating = 'High' OR fraud_loss_percentile >= 0.75 OR decline_percentile >= 0.75
      THEN 'Elevated Risk'
    ELSE 'Core Portfolio'
  END AS merchant_priority_segment
FROM ranked;
