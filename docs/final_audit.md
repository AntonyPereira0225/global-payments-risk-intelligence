# Final Portfolio Audit

This audit records the final repository and implementation review for the Global Payments Risk & Merchant Intelligence Platform.

> All data, fraud labels and model results in this project are synthetic. The project is not affiliated with a real payment network, merchant acquirer or financial institution.

## Audit Status

**Status: Complete**

The repository now contains an end-to-end, internally consistent analytics workflow covering synthetic data generation, quality validation, cloud warehousing, SQL analytics, Power BI reporting and leakage-aware fraud-risk modelling.

## Data and Quality Controls

- 5,000,000 synthetic transactions validated.
- 150,000 customers, 8,000 merchants, 75,000 devices and 25 countries represented.
- Generated Parquet outputs remain excluded from Git because they are reproducible.
- The original currency-normalisation defect is documented and the corrected dataset passed validation.
- Transaction, fraud, cross-border and value metrics reconcile between local validation and BigQuery.
- The stored customer schema excludes age and other unnecessary demographic attributes.
- The final BigQuery customer-schema cleanup is captured in `sql/11_schema_cleanup.sql` and was executed successfully.

## Warehouse and SQL

- BigQuery project and dataset are documented.
- Star-schema documentation matches the implemented fact and dimension fields.
- Curated SQL views cover payment performance, declines, merchant intelligence, customer analytics, fraud risk, transaction velocity, anomaly detection and executive KPIs.
- The fraud-modelling feature view excludes post-outcome leakage fields and high-cardinality customer, merchant and device identifiers.
- The exploratory merchant anomaly detector is documented as intentionally requiring recalibration rather than being presented as production-ready.

## Power BI

The repository contains the completed `.pbix` file and screenshots for:

1. Global Payments Executive Overview
2. Global Payments Merchant Intelligence
3. Global Payments Fraud & Risk Intelligence

Power BI consumes curated BigQuery views rather than importing the full transaction fact table.

## Fraud-Risk Modelling

Two models were evaluated using the same leakage-safe feature set and chronological design:

- **Champion:** Logistic Regression
- **Challenger:** Histogram Gradient Boosting

The December test set remained untouched during training and threshold selection. Model comparison uses PR-AUC, ROC-AUC and risk-ranking capture rather than accuracy alone.

The champion Logistic Regression achieved:

- PR-AUC / Average Precision: **0.007505**
- ROC-AUC: **0.722953**
- top-0.5% fraud capture: **4.44%**
- top-1% fraud capture: **6.90%**
- top-5% fraud capture: **23.25%**

Operational thresholds were selected on November validation data and applied unchanged to December. At an intended 0.5% review capacity, the December result delivered approximately **9.25x lift versus random review**.

Model coefficients are interpreted as directional predictive signals within the synthetic environment, not causal effects or classical reference-category odds ratios.

## Repository Hygiene

- Multi-million-row generated data is not committed.
- Local model artefacts are excluded through `models/outputs/.gitignore`.
- The Power BI file and portfolio screenshots are intentionally versioned.
- Documentation clearly distinguishes synthetic results from real-world industry performance.
- The architecture folder now documents the implemented end-to-end flow rather than future planned artefacts.

## Final Positioning

The project demonstrates an end-to-end analytics workflow across:

**Python → data quality → Parquet → Google Cloud Storage → BigQuery → dimensional modelling → advanced SQL → Power BI → fraud-risk modelling → business interpretation**

The repository is considered portfolio-ready. Future additions should be treated as optional enhancements rather than required completion work.
