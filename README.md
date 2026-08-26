# Global Payments Risk & Merchant Intelligence Platform

An end-to-end analytics engineering and business intelligence portfolio project that models a fictional global payments company processing millions of transactions across customers, merchants, countries, payment channels and devices.

The project is designed to demonstrate scalable SQL analytics, dimensional modelling, data quality, business intelligence, risk analysis and stakeholder-focused reporting using Python, BigQuery and Power BI.

> **Portfolio note:** All transaction, customer, merchant and fraud data in this repository will be synthetic. The project is not affiliated with any real payment network or financial institution.

## Business Objective

Build a trusted analytical platform that enables business, operations and risk stakeholders to answer questions such as:

- Where are payment approval rates deteriorating?
- What are the main drivers of payment declines?
- Which merchants combine high commercial value with elevated operational or fraud risk?
- How do customer behaviour and cross-border activity vary by segment and market?
- Where are fraud exposure and fraud losses increasing?
- Which unusual transaction patterns require investigation?
- Are KPI definitions and reporting outputs consistent across teams?

## Stakeholders

| Stakeholder | Primary questions |
|---|---|
| Executive Management | How are transaction value, approval rate, decline rate and fraud losses changing? |
| Merchant Operations | Which merchants show deteriorating payment performance or operational exceptions? |
| Risk & Fraud | Where are suspicious velocity, amount or geographic patterns emerging? |
| Commercial | Which merchants and customer segments are growing, valuable or underperforming? |
| Data & BI | Are metrics reproducible, documented and built from validated data? |

## Planned Technology Stack

- Python
- pandas
- NumPy
- BigQuery
- SQL
- Power BI
- DAX
- Git / GitHub

## Target Scale

The synthetic analytical environment is planned around approximately:

- **5,000,000 payment transactions**
- **150,000 customers**
- **8,000 merchants**
- **25–30 countries**
- **12 months of activity**

The generated data will intentionally include realistic seasonality, payment declines, cross-border behaviour, merchant variation, rare fraud events and operational anomalies so the analysis is not based on purely random distributions.

## Analytical Architecture

```text
Synthetic payment data
        |
        v
Python generation and validation
        |
        v
BigQuery analytical warehouse
        |
        v
Dimensional / star schema
        |
        v
SQL analytics and KPI layer
        |
        v
Power BI semantic model
        |
        v
Executive, merchant and risk dashboards
```

## Planned Data Model

The core warehouse will use a star-schema design centred on `fact_transactions`.

### Fact table

`fact_transactions`

Key fields will include transaction ID, timestamp, customer, merchant, device, geography, payment method, channel, amount, currency, transaction status, decline reason, cross-border indicator, fraud indicator, fraud loss and processing time.

### Dimensions

- `dim_customer`
- `dim_merchant`
- `dim_device`
- `dim_country`
- `dim_date`

Detailed field definitions are maintained in [`docs/data_model.md`](docs/data_model.md).

## KPI Layer

Initial business metrics include:

- Transaction Volume
- Transaction Value
- Approved Transactions
- Approval Rate
- Decline Rate
- Average Transaction Value
- Fraud Transaction Rate
- Fraud Loss
- Cross-Border Transaction Rate
- Active Customers
- Active Merchants
- Transactions per Customer

Formal definitions are maintained in [`docs/metric_definitions.md`](docs/metric_definitions.md).

## Planned Analytical Modules

### 1. Payment Performance
Approval and decline trends by time, geography, channel, payment method and merchant.

### 2. Merchant Intelligence
Merchant value, growth, approval performance, decline behaviour and risk segmentation.

### 3. Customer Analytics
Customer activity, transaction frequency, spending behaviour, tenure and cross-border usage.

### 4. Fraud & Risk Analytics
Fraud exposure, fraud loss, transaction velocity, unusual values, geographic anomalies and suspicious behavioural changes.

### 5. Operational Analytics
Processing time, operational exceptions, decline reasons and emerging performance deterioration.

## Repository Structure

```text
global-payments-risk-intelligence/
|
|-- README.md
|-- architecture/
|   `-- README.md
|-- data/
|   `-- README.md
|-- dashboard/
|   `-- README.md
|-- docs/
|   |-- business_requirements.md
|   |-- data_model.md
|   `-- metric_definitions.md
|-- models/
|   `-- README.md
|-- sql/
|   `-- README.md
`-- src/
    `-- README.md
```

The repository will be expanded incrementally as each layer is implemented and validated.

## Project Status

**Phase 1 — Business and data architecture: in progress**

Next milestone: design and implement the reproducible synthetic payments data generator before loading the warehouse.

## Author

**Antony Pereira George**  
Data Analyst | SQL | Power BI | Python | Business Intelligence
