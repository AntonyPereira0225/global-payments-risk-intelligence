# Global Payments Risk & Merchant Intelligence Platform

An end-to-end analytics engineering and business intelligence portfolio project modelling a fictional global payments company processing millions of transactions across customers, merchants, countries, payment channels and devices.

The project demonstrates reproducible synthetic-data generation, automated data-quality controls, BigQuery warehousing, dimensional modelling, advanced SQL analytics and Power BI reporting.

> **Portfolio note:** All transaction, customer, merchant and fraud data is synthetic. The project is not affiliated with any real payment network or financial institution.

## Business Objective

Build a trusted analytical platform that helps executive, commercial, merchant-operations, risk and BI stakeholders understand payment performance, declines, merchant value, customer behaviour, cross-border activity, fraud exposure and operational anomalies.

## Technology Stack

Python · pandas · NumPy · Parquet · Google Cloud Storage · BigQuery · SQL · Power BI · DAX · Git/GitHub

## Validated Dataset

| Metric | Result |
|---|---:|
| Payment transactions | **5,000,000** |
| Customers | **150,000** |
| Merchants | **8,000** |
| Devices | **75,000** |
| Countries | **25** |
| Analysis period | **365 days** |
| Approval rate | **93.95%** |
| Decline rate | **6.05%** |
| Fraud transaction rate | **0.203%** |
| Cross-border transaction rate | **15.51%** |
| Transaction value | **$496,439,922.54** |
| Average transaction value | **$99.29** |
| Fraud loss | **$766,088.56** |

The first full pipeline run failed a currency-normalisation quality check. The modelling issue was corrected and the complete 5,000,000-row dataset subsequently passed validation. The incident is documented in [`docs/data_quality_notes.md`](docs/data_quality_notes.md).

## BigQuery Warehouse

The validated data has been loaded to:

- Project: `global-payments-intelligence`
- Dataset: `payments_intelligence`
- Fact table: `fact_transactions`
- Dimensions: `dim_customer`, `dim_merchant`, `dim_device`, `dim_country`, `dim_date`

The warehouse reconciled exactly to the validated local metrics, including 5,000,000 transactions, 93.95% approval rate, 0.203% fraud rate, 15.51% cross-border rate, $496.44M transaction value and $766.09K fraud loss. See [`docs/warehouse_validation.md`](docs/warehouse_validation.md).

## Analytical Architecture

```text
Synthetic payment data
        ↓
Python generation & validation
        ↓
Google Cloud Storage staging
        ↓
BigQuery analytical warehouse
        ↓
Star schema / dimensional model
        ↓
Advanced SQL & KPI views
        ↓
Power BI semantic model
        ↓
Executive, merchant & risk dashboards
```

## Data Model

The warehouse uses a star schema centred on `fact_transactions`, with reusable customer, merchant, device, country and date dimensions. Detailed definitions are maintained in [`docs/data_model.md`](docs/data_model.md).

## SQL Analytics Layer

The executed and validated BigQuery SQL layer includes:

- warehouse validation
- daily payment performance
- decline-reason analysis
- merchant value/risk segmentation
- customer behavioural segmentation
- fraud-risk segmentation
- rolling customer transaction velocity
- merchant anomaly detection with rolling baselines and z-scores
- executive monthly KPIs with `LAG` and month-on-month movement

Validated analytical findings are documented in [`docs/analytical_findings.md`](docs/analytical_findings.md).

## Repository Structure

```text
global-payments-risk-intelligence/
├── README.md
├── architecture/
├── data/
├── dashboard/
├── docs/
├── models/
├── sql/
└── src/
```

## Project Status

- **Phase 1 — Business and data architecture: complete**
- **Phase 2 — Synthetic data generation and validation: complete**
- **Phase 3A — BigQuery warehouse load and reconciliation: complete**
- **Phase 3B — Advanced SQL analytics and validation: complete**
- Phase 4 — Power BI semantic model and dashboards
- Phase 5 — Fraud-risk modelling and final portfolio polish

## Author

**Antony Pereira George**  
Data Analyst | SQL | Power BI | Python | Business Intelligence
