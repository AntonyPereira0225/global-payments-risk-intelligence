# Analytical Findings

> All findings in this document are derived from the project's validated **synthetic** payments dataset. They describe the simulated environment only and must not be interpreted as real payment-network or industry statistics.

## Merchant Intelligence

The merchant segmentation highlights a clear commercial-risk concentration.

- **High Value / Elevated Risk** contains 1,429 merchants (17.9% of the 8,000-merchant portfolio), but contributes about $228.0M of transaction value (45.9% of total value) and $548.9K of fraud loss (71.7% of total fraud loss).
- Its average approval rate is 91.49%, compared with 94.86% for the Core Portfolio.
- Combining **High Value / Elevated Risk** and **Elevated Risk** gives 3,122 merchants (39.0% of the portfolio) representing about 58.7% of transaction value and 93.7% of fraud loss.

**Interpretation:** the highest-risk merchants are commercially material, so prioritisation should balance revenue importance, approval performance and fraud loss rather than treating risk and commercial value separately.

## Customer Behaviour

Customer segmentation shows that value and activity are associated with more complex usage patterns in the simulated dataset.

- **High Value / High Activity** customers show 23.78% average cross-border activity and a 0.233% average fraud rate.
- **Core Customer** records 11.68% average cross-border activity and a 0.190% average fraud rate.
- High Value / High Activity customers therefore combine commercial importance with relatively higher cross-border and fraud exposure.

**Interpretation:** customer value alone is not sufficient for prioritisation; behavioural intensity and cross-border usage add useful context for risk monitoring.

## Fraud-Risk Concentration

The fraud-risk segmentation demonstrates a strong interaction between merchant risk, customer risk and cross-border activity.

- The highest fraud-rate segment is **High merchant risk / High customer risk / Cross-border**, at 3.437% across 1,222 transactions. This is about 16.9x the portfolio-wide fraud rate of 0.203%.
- The same segment has a fraud-loss rate of 1.5447%, the highest among the analysed risk combinations.
- **High merchant risk / Medium customer risk / Cross-border** records a 1.854% fraud rate and 1.0989% fraud-loss rate.
- Across all merchant/customer risk combinations, cross-border transactions show higher fraud rates than the corresponding domestic segment in this simulation, typically by roughly 1.6x to 2.3x.
- The segment with the highest fraud rate is not the segment with the largest absolute fraud loss. **High merchant risk / Low customer risk / Domestic** generates the largest absolute fraud loss ($134.3K) because of its much larger transaction volume.

**Interpretation:** effective prioritisation should combine fraud rate, absolute loss, transaction volume and cross-border context. A rate-only approach would over-emphasise small high-rate segments, while a loss-only approach could miss emerging concentrated risks.

## Transaction Velocity

Rolling 1-hour transaction velocity is a useful fraud signal in the simulated dataset.

- **High Velocity** transactions have a 0.717% fraud rate, about 3.6x the 0.198% rate for Normal Velocity transactions.
- **Elevated Velocity** transactions have a 0.619% fraud rate, about 3.1x the Normal Velocity rate.
- High and Elevated Velocity together represent only about 1.19% of all transactions, but account for about 3.73% of fraud transactions and 27.2% of total fraud loss.
- These two bands also represent about 14.2% of transaction value, showing that the alerts are concentrated in relatively high-value transaction activity rather than only high-count bursts.

**Interpretation:** velocity is informative but should not be treated as a standalone fraud rule. It works best as one feature within a broader risk framework alongside customer risk, merchant risk, cross-border status and transaction value.

## Portfolio Use

These findings will be used to shape the Power BI risk and merchant-intelligence pages. Final dashboard commentary should continue to label the results as synthetic simulation findings and avoid causal or industry-wide claims.
