# Models

This folder contains the Phase 5 fraud-risk modelling layer built after the analytical platform, SQL views and Power BI dashboards were completed and validated.

> All modelling data and labels are synthetic. Model performance describes the simulated environment only and must not be interpreted as real payment-network or industry performance.

## Modelling Objective

Build a transaction-level fraud-risk classifier that demonstrates a disciplined imbalanced-classification workflow rather than optimising headline accuracy.

The modelling layer compares a transparent Logistic Regression baseline with a nonlinear Histogram Gradient Boosting challenger using the same leakage-safe feature set and chronological validation design.

## Leakage Controls

The modelling feature view is defined in [`sql/10_fraud_model_features.sql`](../sql/10_fraud_model_features.sql).

The following fields are deliberately excluded from predictive features:

- `transaction_status` — generated partly from the fraud outcome and therefore post-outcome leakage
- `decline_reason` — populated after approval/decline logic and can directly reveal suspected fraud
- `fraud_loss_amount_usd` — only exists after the fraud outcome
- customer, merchant and device IDs — high-cardinality identifiers that encourage memorisation rather than generalisable behaviour

The cleaned customer schema intentionally stores no age or other demographic attribute for this portfolio objective. `transaction_id` is retained only for row traceability and deterministic sampling and is never passed to the model.

## Validation Design

The model uses a chronological split to mimic forward-looking scoring:

- Train: January–October 2025
- Validation: November 2025
- Test: December 2025

A deterministic 1/4 sample of the training period was used locally for memory efficiency, giving 1,003,085 training rows. November and December retained their natural synthetic fraud prevalence.

## Models Tested

1. **Logistic Regression** — interpretable baseline with class weighting.
2. **Histogram Gradient Boosting** — nonlinear challenger using the same leakage-safe inputs.

## Final Model Selection

The Logistic Regression is retained as the **champion model**. On the untouched December test set it achieved:

- PR-AUC / Average Precision: **0.007505**
- ROC-AUC: **0.722953**
- fraud capture in top 0.5% of scores: **4.44%**
- fraud capture in top 1%: **6.90%**
- fraud capture in top 5%: **23.25%**

The Histogram Gradient Boosting challenger achieved PR-AUC 0.006813 and ROC-AUC 0.709423. It slightly improved top-1% capture to 7.28%, but did not outperform the simpler model overall.

## Operational Thresholding

The maximum-F1 threshold is kept only as a benchmark. The project instead evaluates fixed review-capacity scenarios using thresholds selected on November and applied unchanged to December.

At an intended 0.5% review capacity, the December flag rate was about 0.46%, capturing 4.25% of fraud at approximately **9.25x lift versus random review**. At an intended 5% review capacity, the model captured 22.21% of fraud at about **4.79x lift**.

Full model comparison, operating points and explainability notes are documented in [`docs/model_results.md`](../docs/model_results.md).

## Explainability

The strongest positive coefficients include high customer risk, high merchant risk, cross-border status, Digital Goods, Travel, Electronics and web-channel activity. Strong negative coefficients include low customer risk, low merchant risk, Healthcare, Grocery and domestic activity.

These are predictive associations within the synthetic generator, not causal findings. Because the model uses regularised one-hot encoded features without a dropped reference category, exponentiated coefficients are not presented as classical reference-category odds ratios.

## Evaluation Principles

The modelling layer uses:

- PR-AUC / Average Precision
- ROC-AUC
- precision, recall and F1
- confusion matrices
- threshold analysis
- capture rate within the highest-risk scored transactions
- fixed review-capacity operating points
- coefficient-based explainability for the champion model

Accuracy alone is not an appropriate success metric because fraud prevalence is very low.

## Limitations

The synthetic fraud label is probabilistically generated from known simulated risk factors. A model can therefore recover relationships intentionally embedded in the generator. The exercise demonstrates modelling workflow, leakage prevention, imbalance handling, validation, operational thresholding and explainability; it does not demonstrate real-world fraud-detection effectiveness.
