-- Final customer-schema cleanup
-- BigQuery Standard SQL
--
-- Purpose:
-- Remove the legacy synthetic age_band column from the stored customer
-- dimension. The attribute is not required for the portfolio's business,
-- BI or fraud-risk modelling objectives.
--
-- This change does not affect the existing modelling feature view because
-- age_band is not referenced there.

ALTER TABLE `global-payments-intelligence.payments_intelligence.dim_customer`
DROP COLUMN IF EXISTS age_band;

-- Validation: should return zero rows after the ALTER TABLE succeeds.
SELECT
  column_name,
  data_type
FROM `global-payments-intelligence.payments_intelligence.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'dim_customer'
  AND column_name = 'age_band';
