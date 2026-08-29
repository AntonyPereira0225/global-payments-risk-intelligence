# Fraud-Risk Modelling Results

> **Important:** All transactions, labels and model results in this project are synthetic. The results demonstrate modelling workflow and analytical judgement only; they are not real payment-network or industry fraud-detection performance.

## Experimental Design

The modelling layer uses the leakage-aware BigQuery view `vw_fraud_model_features` and a chronological evaluation design:

- Training period: January-October 2025
- Training rows used locally: 1,003,085 (deterministic 1/4 sample)
- Validation period: November 2025 — 466,293 transactions, 966 fraud transactions
- Untouched test period: December 2025 — 518,745 transactions, 1,058 fraud transactions

The natural fraud prevalence remains close to 0.20% across all periods, so accuracy is not used as the primary success metric.

## Champion vs Challenger

| Test metric | Logistic Regression | HistGradientBoosting |
|---|---:|---:|
| PR-AUC / Average Precision | **0.007505** | 0.006813 |
| ROC-AUC | **0.722953** | 0.709423 |
| Capture in top 0.5% | **4.44%** | 4.16% |
| Capture in top 1% | 6.90% | **7.28%** |
| Capture in top 5% | **23.25%** | 23.16% |

The nonlinear challenger was tested fairly using the same leakage-safe features and chronological splits. It slightly outperformed the Logistic Regression at the top 1% review band, but the Logistic Regression produced stronger overall PR-AUC, ROC-AUC and comparable or better capture at the other review capacities. The simpler, more interpretable model is therefore retained as the **champion model**.

## Why the F1 Threshold Is Not the Business Recommendation

The Logistic Regression's validation-selected maximum-F1 threshold was 0.90. On the December test set it achieved approximately 2.49% precision and 2.74% recall, catching 29 of 1,058 fraud transactions while flagging about 0.22% of transactions.

This threshold is useful as a statistical benchmark, but it is not treated as the operational recommendation. In highly imbalanced fraud screening, the more practical question is how much fraud can be captured for a fixed review capacity.

## Review-Capacity Operating Points

Thresholds were selected using the November validation set and then applied unchanged to December.

| Requested review capacity | December flag rate | Fraud captured | Fraud capture rate | Precision | Lift vs random |
|---:|---:|---:|---:|---:|---:|
| 0.5% | 0.460% | 45 | 4.25% | 1.89% | **9.25x** |
| 1% | 0.909% | 69 | 6.52% | 1.46% | **7.17x** |
| 2% | 1.934% | 128 | 12.10% | 1.28% | **6.25x** |
| 5% | 4.635% | 235 | 22.21% | 0.98% | **4.79x** |
| 10% | 9.589% | 376 | 35.54% | 0.76% | **3.71x** |

The strongest concentration appears at the smallest review bands. For example, reviewing roughly the highest-risk 0.5% of December transactions captures about 4.25% of synthetic fraud, representing about 9.25 times the concentration expected from random review.

## Explainability

The Logistic Regression coefficients recover risk relationships intentionally embedded in the synthetic generator. Strong positive model signals include:

- high customer risk segment
- Digital Goods merchant category
- high merchant risk rating
- cross-border transactions
- Travel and Electronics merchant categories
- web channel

Strong negative model signals include:

- low customer risk segment
- low merchant risk rating
- Healthcare and Grocery merchant categories
- domestic transactions

These are predictive associations within the simulated environment, not causal findings. Because the model uses regularised one-hot encoded features without a dropped reference category, individual exponentiated coefficients should not be interpreted as classical reference-category odds ratios.

## Model Selection Decision

**Champion:** Logistic Regression  
**Challenger:** Histogram Gradient Boosting

The final decision prioritises out-of-sample ranking performance, interpretability and operational usefulness rather than model complexity.

## Limitations

- Fraud labels are generated from known synthetic probabilities, so models can recover relationships intentionally encoded in the simulation.
- The results cannot be generalised to real payment fraud.
- No post-outcome fields such as decline reason, transaction status or fraud loss are used as predictive features.
- Customer, merchant and device identifiers are excluded to reduce memorisation risk.
- `age_band` is excluded from modelling because it is unnecessary for the stated fraud-risk objective.
- Review-capacity results illustrate queue prioritisation; they do not represent a production decisioning policy or recommended customer treatment.
