-- Decline analysis view with reason-level share and overall decline rate
-- BigQuery Standard SQL

CREATE OR REPLACE VIEW `global-payments-intelligence.payments_intelligence.vw_decline_analysis_monthly` AS
WITH base AS (
  SELECT
    DATE_TRUNC(DATE(t.transaction_timestamp), MONTH) AS month,
    t.country_id,
    c.country_name,
    c.region,
    t.channel,
    t.payment_method,
    t.transaction_status,
    t.decline_reason
  FROM `global-payments-intelligence.payments_intelligence.fact_transactions` AS t
  LEFT JOIN `global-payments-intelligence.payments_intelligence.dim_country` AS c
    ON t.country_id = c.country_id
),
segment_totals AS (
  SELECT
    month,
    country_id,
    country_name,
    region,
    channel,
    payment_method,
    COUNT(*) AS transaction_count,
    COUNTIF(transaction_status = 'declined') AS declined_transactions
  FROM base
  GROUP BY 1,2,3,4,5,6
),
reason_totals AS (
  SELECT
    month,
    country_id,
    country_name,
    region,
    channel,
    payment_method,
    decline_reason,
    COUNT(*) AS decline_reason_count
  FROM base
  WHERE transaction_status = 'declined'
  GROUP BY 1,2,3,4,5,6,7
)
SELECT
  r.month,
  r.country_id,
  r.country_name,
  r.region,
  r.channel,
  r.payment_method,
  r.decline_reason,
  s.transaction_count,
  s.declined_transactions,
  r.decline_reason_count,
  SAFE_DIVIDE(s.declined_transactions, s.transaction_count) AS decline_rate,
  SAFE_DIVIDE(r.decline_reason_count, s.declined_transactions) AS share_of_declines
FROM reason_totals AS r
JOIN segment_totals AS s
  USING (month, country_id, country_name, region, channel, payment_method);
