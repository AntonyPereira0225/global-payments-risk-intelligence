# Source Code

Python source code for the synthetic payments data pipeline.

## Phase 2 modules

```text
src/
|-- config.py
|-- generate_dimensions.py
|-- generate_transactions.py
|-- validate_data.py
`-- run_pipeline.py
```

## What the generator models

The dataset is intentionally behavioural rather than purely random. The generator creates relationships between:

- customer segment and transaction frequency
- customer segment and cross-border behaviour
- customer segment and preferred payment channel
- merchant category and typical transaction amount
- merchant/country/customer risk and fraud probability
- cross-border and high-value transactions and approval probability
- fraud outcomes and fraud-loss exposure
- channel/payment method and processing time
- weekday, weekend and seasonal transaction volumes

All records are synthetic. No real customer, merchant or card data is used.

## Scale

Default configuration:

- 150,000 customers
- 8,000 merchants
- 75,000 devices
- 25 countries
- 5,000,000 payment transactions
- 12 months of transaction activity

Transactions are written in 250,000-row Parquet chunks using Zstandard compression so the pipeline can handle multi-million-row output without loading the complete fact table into memory.

## Run locally

From the repository root:

```bash
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Run the full pipeline in one command:

```bash
python src/run_pipeline.py
```

Or run each stage separately:

```bash
python src/generate_dimensions.py
python src/generate_transactions.py
python src/validate_data.py
```

The validator checks primary keys, referential integrity, required fields, transaction-status logic, fraud-loss logic, amount validity, processing-time ranges, transaction-ID continuity and total row count. It also produces summary metrics for approval rate, fraud rate, cross-border rate, transaction value and fraud loss.

## Reproducibility

A fixed random seed is defined in `config.py`. Re-running the generator with the same configuration reproduces the same synthetic behavioural model. Large generated datasets are intentionally excluded from GitHub; only code, documentation and later curated samples/outputs belong in the repository.

## Next phase

Phase 3 will load the generated data into BigQuery and build the dimensional warehouse, analytical SQL layer and reusable KPI views.
