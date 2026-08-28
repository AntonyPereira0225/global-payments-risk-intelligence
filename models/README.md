# Models

This folder contains the optional Phase 5 fraud-risk modelling layer built after the analytical platform, SQL views and Power BI dashboards were completed and validated.

> All modelling data and labels are synthetic. Model performance describes the simulated environment only and must not be interpreted as real payment-network or industry performance.

## Modelling Objective

Build a transaction-level fraud-risk classifier that demonstrates a disciplined imbalanced-classification workflow rather than optimising headline accuracy.

The modelling layer will compare a transparent baseline with a stronger nonlinear model and evaluate whether transaction, customer, merchant, channel, device and cross-border features can rank synthetic fraud risk.

## Leakage Controls

The modelling feature view is defined in [`sql/10_fraud_model_features.sql`](../sql/10_fraud_model_features.sql).

The following fields are deliberately excluded from predictive features:

- `transaction_status` — generated partly from the fraud outcome and therefore post-outcome leakage
- `decline_reason` — populated after approval/decline logic and can directly reveal suspected fraud
- `fraud_loss_amount_usd` — only exists after the fraud outcome
- customer, merchant and device IDs — high-cardinality identifiers that encourage memorisation rather than generalisable behaviour
- `age_band` — unnecessary for the business objective and excluded from the risk model

`transaction_id` is retained only for row traceability and must never be passed to the model.

## Validation Design

Use a chronological split to mimic forward-looking scoring:

- Train: January–October 2025
- Validation: November 2025
- Test: December 2025

The untouched December test set must preserve the natural synthetic fraud prevalence.

## Candidate Models

1. Logistic Regression — interpretable baseline with class weighting.
2. Gradient-boosted trees — nonlinear benchmark using the same leakage-safe feature set.

Training may use a reproducible sample of the training period if required for local-memory efficiency, but validation and final test metrics should use the natural class distribution.

## Evaluation

Primary evaluation should include:

- PR-AUC / Average Precision
- ROC-AUC
- precision, recall and F1
- confusion matrix
- threshold analysis
- capture rate within the highest-risk scored transactions
- feature importance / explainability where supported

Accuracy alone is not an appropriate success metric because fraud prevalence is very low.

## Limitations

The synthetic fraud label is probabilistically generated from known simulated risk factors. A model can therefore recover relationships intentionally embedded in the generator. The exercise demonstrates modelling workflow, leakage prevention, imbalance handling, validation and explainability; it does not demonstrate real-world fraud-detection effectiveness.
