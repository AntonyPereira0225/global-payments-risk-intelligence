-- Customer transaction velocity view using rolling time windows
-- BigQuery Standard SQL

CREATE OR REPLACE VIEW `global-payments-intelligence.payments_intelligence.vw_transaction_velocity` AS
WITH velocity AS (
  SELECT
    t.*,
    COUNT(*) OVER (
      PARTITION BY customer_id
      ORDER BY UNIX_SECONDS(transaction_timestamp)
      RANGE BETWEEN 3600 PRECEDING AND CURRENT ROW
    ) AS customer_transactions_1h,
    SUM(transaction_amount_usd) OVER (
      PARTITION BY customer_id
      ORDER BY UNIX_SECONDS(transaction_timestamp)
      RANGE BETWEEN 3600 PRECEDING AND CURRENT ROW
    ) AS customer_value_usd_1h,
    COUNT(*) OVER (
      PARTITION BY customer_id
      ORDER BY UNIX_SECONDS(transaction_timestamp)
      RANGE BETWEEN 86400 PRECEDING AND CURRENT ROW
    ) AS customer_transactions_24h,
    SUM(transaction_amount_usd) OVER (
      PARTITION BY customer_id
      ORDER BY UNIX_SECONDS(transaction_timestamp)
      RANGE BETWEEN 86400 PRECEDING AND CURRENT ROW
    ) AS customer_value_usd_24h
  FROM `global-payments-intelligence.payments_intelligence.fact_transactions` AS t
)
SELECT
  *,
  CASE
    WHEN customer_transactions_1h >= 8 OR customer_value_usd_1h >= 1500 THEN 'High Velocity'
    WHEN customer_transactions_1h >= 5 OR customer_value_usd_1h >= 750 THEN 'Elevated Velocity'
    ELSE 'Normal Velocity'
  END AS velocity_band,
  (customer_transactions_1h >= 8 OR customer_value_usd_1h >= 1500) AS velocity_alert
FROM velocity;
