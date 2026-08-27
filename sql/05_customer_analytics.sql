-- Customer analytics view with spend/activity ranking
-- BigQuery Standard SQL

CREATE OR REPLACE VIEW `global-payments-intelligence.payments_intelligence.vw_customer_analytics` AS
WITH customer_agg AS (
  SELECT
    t.customer_id,
    c.customer_segment,
    c.home_country,
    c.account_tenure_months,
    c.risk_segment,
    MIN(DATE(t.transaction_timestamp)) AS first_transaction_date,
    MAX(DATE(t.transaction_timestamp)) AS last_transaction_date,
    COUNT(DISTINCT DATE_TRUNC(DATE(t.transaction_timestamp), MONTH)) AS active_months,
    COUNT(*) AS transaction_count,
    SUM(t.transaction_amount_usd) AS transaction_value_usd,
    AVG(t.transaction_amount_usd) AS average_transaction_value_usd,
    SAFE_DIVIDE(COUNTIF(t.transaction_status = 'approved'), COUNT(*)) AS approval_rate,
    SAFE_DIVIDE(COUNTIF(t.is_cross_border), COUNT(*)) AS cross_border_rate,
    SAFE_DIVIDE(COUNTIF(t.is_fraud), COUNT(*)) AS fraud_rate,
    SUM(t.fraud_loss_amount_usd) AS fraud_loss_usd
  FROM `global-payments-intelligence.payments_intelligence.fact_transactions` AS t
  JOIN `global-payments-intelligence.payments_intelligence.dim_customer` AS c
    ON t.customer_id = c.customer_id
  GROUP BY 1,2,3,4,5
),
ranked AS (
  SELECT
    *,
    NTILE(5) OVER (ORDER BY transaction_value_usd DESC) AS spend_quintile,
    NTILE(5) OVER (ORDER BY transaction_count DESC) AS activity_quintile
  FROM customer_agg
)
SELECT
  *,
  CASE
    WHEN spend_quintile = 1 AND activity_quintile = 1 THEN 'High Value / High Activity'
    WHEN spend_quintile = 1 THEN 'High Value'
    WHEN activity_quintile = 1 THEN 'High Activity'
    WHEN active_months <= 3 THEN 'Low Engagement'
    ELSE 'Core Customer'
  END AS behavioural_segment
FROM ranked;
