-- Merchant daily anomaly-detection view using rolling baselines
-- BigQuery Standard SQL

CREATE OR REPLACE VIEW `global-payments-intelligence.payments_intelligence.vw_merchant_daily_anomalies` AS
WITH merchant_day AS (
  SELECT
    merchant_id,
    DATE(transaction_timestamp) AS transaction_date,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount_usd) AS transaction_value_usd,
    SAFE_DIVIDE(COUNTIF(transaction_status = 'approved'), COUNT(*)) AS approval_rate,
    SAFE_DIVIDE(COUNTIF(is_fraud), COUNT(*)) AS fraud_rate,
    SUM(fraud_loss_amount_usd) AS fraud_loss_usd,
    AVG(processing_time_ms) AS average_processing_time_ms
  FROM `global-payments-intelligence.payments_intelligence.fact_transactions`
  GROUP BY 1,2
),
with_baseline AS (
  SELECT
    *,
    COUNT(*) OVER (
      PARTITION BY merchant_id
      ORDER BY transaction_date
      ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING
    ) AS baseline_observations,
    AVG(transaction_count) OVER (
      PARTITION BY merchant_id
      ORDER BY transaction_date
      ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING
    ) AS baseline_transaction_count,
    STDDEV_SAMP(transaction_count) OVER (
      PARTITION BY merchant_id
      ORDER BY transaction_date
      ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING
    ) AS baseline_transaction_count_sd,
    AVG(transaction_value_usd) OVER (
      PARTITION BY merchant_id
      ORDER BY transaction_date
      ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING
    ) AS baseline_transaction_value_usd,
    STDDEV_SAMP(transaction_value_usd) OVER (
      PARTITION BY merchant_id
      ORDER BY transaction_date
      ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING
    ) AS baseline_transaction_value_sd,
    AVG(approval_rate) OVER (
      PARTITION BY merchant_id
      ORDER BY transaction_date
      ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING
    ) AS baseline_approval_rate,
    STDDEV_SAMP(approval_rate) OVER (
      PARTITION BY merchant_id
      ORDER BY transaction_date
      ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING
    ) AS baseline_approval_rate_sd
  FROM merchant_day
),
scored AS (
  SELECT
    *,
    SAFE_DIVIDE(transaction_count - baseline_transaction_count, baseline_transaction_count_sd) AS transaction_count_zscore,
    SAFE_DIVIDE(transaction_value_usd - baseline_transaction_value_usd, baseline_transaction_value_sd) AS transaction_value_zscore,
    SAFE_DIVIDE(approval_rate - baseline_approval_rate, baseline_approval_rate_sd) AS approval_rate_zscore
  FROM with_baseline
)
SELECT
  *,
  (
    baseline_observations >= 7
    AND (
      ABS(COALESCE(transaction_count_zscore, 0)) >= 3
      OR ABS(COALESCE(transaction_value_zscore, 0)) >= 3
      OR COALESCE(approval_rate_zscore, 0) <= -3
    )
  ) AS anomaly_flag
FROM scored;
