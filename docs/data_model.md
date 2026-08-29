# Data Model

## Modelling Approach

The analytical warehouse uses a star-schema design. The central grain is one row per payment transaction in `fact_transactions`, with reusable dimensions for customer, merchant, device, geography and date.

## Fact Table: `fact_transactions`

**Grain:** one row per payment transaction.

| Field | Description |
|---|---|
| transaction_id | Unique synthetic transaction identifier |
| transaction_timestamp | Transaction date and time |
| customer_id | Foreign key to `dim_customer` |
| merchant_id | Foreign key to `dim_merchant` |
| device_id | Foreign key to `dim_device` |
| country_id | Transaction / merchant-country key |
| payment_method | Synthetic payment-method category |
| channel | Card-present, web or in-app channel |
| currency | Merchant local transaction currency |
| transaction_amount | Gross transaction amount in local currency |
| transaction_amount_usd | Illustrative USD-equivalent reporting amount using static synthetic FX factors |
| transaction_status | Approved or declined |
| decline_reason | Reason populated for declined transactions |
| is_cross_border | Whether merchant country differs from customer home country |
| is_fraud | Confirmed synthetic fraud indicator |
| fraud_loss_amount_usd | Synthetic confirmed USD-equivalent loss for approved fraudulent transactions |
| processing_time_ms | Simulated end-to-end processing duration |

## Dimension: `dim_customer`

**Grain:** one row per synthetic customer.

| Field | Description |
|---|---|
| customer_id | Unique customer key |
| customer_segment | Retail behavioural / value segment |
| signup_date | Synthetic account opening date |
| home_country | Customer home market |
| account_tenure_months | Tenure at analysis reference date |
| risk_segment | Synthetic low / medium / high risk classification |
| transaction_propensity | Synthetic sampling weight used only by the data generator |

The stored customer dimension intentionally excludes age and other demographic attributes because they are unnecessary for the stated analytics and fraud-risk objectives.

## Dimension: `dim_merchant`

**Grain:** one row per synthetic merchant.

| Field | Description |
|---|---|
| merchant_id | Unique merchant key |
| merchant_name | Fictional merchant label |
| merchant_category | Merchant category / industry |
| merchant_country | Merchant home market |
| merchant_size | Small / medium / large / enterprise |
| merchant_tier | Commercial tier |
| onboarding_date | Synthetic onboarding date |
| merchant_risk_rating | Synthetic low / medium / high merchant-risk classification |
| transaction_propensity | Synthetic sampling weight used only by the data generator |

## Dimension: `dim_device`

**Grain:** one row per synthetic device profile.

| Field | Description |
|---|---|
| device_id | Unique device key |
| device_type | Mobile, desktop, tablet or point-of-sale terminal |
| operating_system | Synthetic operating-system category |
| browser | Browser / application category where applicable |

## Dimension: `dim_country`

**Grain:** one row per country represented in the platform.

| Field | Description |
|---|---|
| country_id | Surrogate geography key |
| country_name | Country name |
| region | High-level geographic region |
| currency | Primary synthetic transaction currency |
| market_weight | Synthetic market sampling weight |
| risk_multiplier | Synthetic country-level risk multiplier used by the generator |

## Dimension: `dim_date`

**Grain:** one row per calendar date.

| Field | Description |
|---|---|
| date_id | Integer date key |
| date | Calendar date |
| day | Day of month |
| week | ISO week |
| month | Month number |
| month_name | Month label |
| quarter | Calendar quarter |
| year | Calendar year |
| day_of_week | Day name |
| is_weekend | Weekend flag |
| transaction_weight | Synthetic seasonality weight used by the generator |

## Relationship Rules

- Every transaction must map to exactly one valid customer, merchant, device and country.
- Transaction dates must fall within the implemented date dimension period.
- Approved transactions have no decline reason; declined transactions require one.
- Fraud loss is positive only for approved fraudulent transactions and zero otherwise.
- Cross-border status is derived from merchant country versus customer home country.
- Dimension attributes describe reusable entities; transaction-level measures remain in the fact table.

## BigQuery and Consumption Design

The transaction fact is stored in BigQuery and consumed through curated analytical views rather than importing the full 5-million-row fact into Power BI. The portfolio prioritises validated query patterns and compact semantic-model inputs over claiming unmeasured physical optimisations.

The fraud model consumes the dedicated `vw_fraud_model_features` view, which excludes post-outcome leakage fields and high-cardinality entity identifiers.

The final customer-schema cleanup is captured in [`sql/11_schema_cleanup.sql`](../sql/11_schema_cleanup.sql).
