# Data Model

## Modelling Approach

The analytical warehouse uses a star-schema design. The central grain is one row per payment transaction in `fact_transactions`, with reusable dimensions for customer, merchant, device, geography and date.

## Fact Table: `fact_transactions`

**Grain:** one row per payment transaction.

| Field | Description |
|---|---|
| transaction_id | Unique transaction identifier |
| transaction_timestamp | Transaction date and time |
| customer_id | Foreign key to `dim_customer` |
| merchant_id | Foreign key to `dim_merchant` |
| device_id | Foreign key to `dim_device` |
| country_id | Transaction-country key |
| payment_method | Card / wallet / bank-linked payment type |
| channel | E-commerce, mobile app, point-of-sale or recurring |
| currency | Transaction currency |
| transaction_amount | Gross transaction amount in local currency |
| transaction_status | Approved or declined |
| decline_reason | Reason populated for declined transactions |
| is_cross_border | Whether transaction country differs from customer home country |
| is_fraud | Confirmed synthetic fraud indicator |
| fraud_loss_amount | Synthetic confirmed loss for fraudulent approved transactions |
| processing_time_ms | Simulated end-to-end processing duration |

## Dimension: `dim_customer`

**Grain:** one row per synthetic customer.

| Field | Description |
|---|---|
| customer_id | Unique customer key |
| customer_segment | Retail behavioural / value segment |
| signup_date | Synthetic account opening date |
| home_country | Customer home market |
| age_band | Non-identifying synthetic age band |
| account_tenure_months | Tenure at analysis reference date |
| risk_segment | Synthetic low / medium / high risk classification |

## Dimension: `dim_merchant`

**Grain:** one row per synthetic merchant.

| Field | Description |
|---|---|
| merchant_id | Unique merchant key |
| merchant_name | Fictional merchant label |
| merchant_category | Merchant category / industry |
| merchant_country | Merchant home market |
| merchant_size | Small / medium / large |
| merchant_tier | Commercial tier |
| onboarding_date | Synthetic onboarding date |

## Dimension: `dim_device`

**Grain:** one row per synthetic device profile.

| Field | Description |
|---|---|
| device_id | Unique device key |
| device_type | Mobile, desktop, tablet or terminal |
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

## Dimension: `dim_date`

**Grain:** one row per calendar date.

| Field | Description |
|---|---|
| date | Calendar date |
| day | Day of month |
| week | ISO week |
| month | Month number |
| month_name | Month label |
| quarter | Calendar quarter |
| year | Calendar year |
| day_of_week | Day name / number |
| is_weekend | Weekend flag |

## Relationship Rules

- Every transaction must map to exactly one valid customer and merchant.
- Transaction geography must exist in `dim_country`.
- Transaction dates must exist in `dim_date`.
- A declined transaction should normally have a decline reason.
- A non-fraud transaction must have zero fraud loss.
- Cross-border status is derived from transaction country versus customer home country.
- Dimension attributes describe the entity; transaction-level measures remain in the fact table.

## BigQuery Design Intent

When implemented in BigQuery, the transaction fact will be partitioned by transaction date and may be clustered by frequently filtered dimensions such as merchant, customer or transaction status after query patterns are validated. The portfolio will document the final design rather than claiming optimisation before it is measured.
