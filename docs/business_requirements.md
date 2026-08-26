# Business Requirements

## Business Context

This project models a fictional global payments organisation processing card and digital-payment transactions across multiple merchants, customers, markets, devices and channels.

The analytical platform must provide a consistent view of payment performance, merchant behaviour, customer activity, fraud exposure and operational exceptions.

## Primary Business Questions

### Executive Management

1. How are transaction volume and transaction value changing over time?
2. Are approval and decline rates improving or deteriorating?
3. Which regions, channels and payment methods are driving changes?
4. How much confirmed fraud loss is being generated and where is it concentrated?

### Merchant Operations

1. Which merchants have unusually high decline rates?
2. Which merchants are growing fastest by approved transaction value?
3. Which merchants show deteriorating approval performance?
4. Which merchant-category and country combinations require operational review?

### Risk & Fraud

1. Where are confirmed fraud rates and fraud losses highest?
2. Which customers or merchants show unusual transaction velocity?
3. Which transactions are unusually large relative to a customer's or merchant's history?
4. Where does geographic behaviour deviate from normal customer activity?
5. Which changes should be prioritised for investigation rather than treated as ordinary variation?

### Commercial

1. Which merchants contribute the most approved payment value?
2. Which merchants combine strong growth with healthy approval performance?
3. Which customer segments are most active and valuable?
4. How important is cross-border activity by customer and merchant segment?

### Data & BI

1. Are all dashboard metrics reproducible from documented SQL logic?
2. Are duplicate transactions, invalid keys, nulls and impossible values detected before reporting?
3. Are dimensions and facts joined consistently?
4. Can business users understand the definition and grain of each KPI?

## Functional Requirements

The platform should:

- generate reproducible synthetic payments data using a fixed random seed;
- preserve realistic relationships between customers, merchants, countries, channels, declines and fraud;
- load curated analytical tables into BigQuery;
- implement a star-schema model centred on a transaction fact table;
- maintain documented KPI definitions;
- provide reusable SQL analysis for payment, merchant, customer and risk reporting;
- perform data-quality checks before analytical outputs are produced;
- support an executive and operational Power BI dashboard;
- document assumptions, limitations and known synthetic-data artefacts.

## Non-Functional Requirements

- **Reproducibility:** generation scripts should produce consistent results for a fixed seed.
- **Scalability:** the design should support millions of transaction rows.
- **Auditability:** KPI calculations should be visible in SQL or documented DAX.
- **Data quality:** key fields, relationships and value ranges should be tested.
- **Clarity:** synthetic data must never be presented as real customer or payment-network data.
- **Performance:** analytical queries should avoid unnecessary scans and use partition/filter logic where appropriate.

## Success Criteria

The project is considered complete when it demonstrates an end-to-end path from synthetic raw data to validated warehouse tables, documented business metrics, advanced SQL analysis and an executive-quality BI output with clearly explained findings.
