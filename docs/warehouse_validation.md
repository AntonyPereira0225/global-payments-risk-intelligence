# BigQuery Warehouse Validation

The validated synthetic dataset was loaded to BigQuery project `global-payments-intelligence`, dataset `payments_intelligence`.

## Reconciliation result

The warehouse fact table reconciled to the local Python validation output:

| Metric | BigQuery result |
|---|---:|
| Transactions | 5,000,000 |
| Approval rate | 93.95% |
| Fraud rate | 0.203% |
| Cross-border rate | 15.51% |
| Transaction value | $496,439,922.54 |
| Fraud loss | $766,088.56 |

The `transaction_value_usd` value may display in scientific notation in the BigQuery CLI as `4.9643992254E8`, which is equivalent to `$496,439,922.54`.

## Quality gate

This reconciliation confirms that the 5,000,000-row fact table loaded successfully without altering the validated business metrics. Advanced analytical views should be created only against this reconciled warehouse.
