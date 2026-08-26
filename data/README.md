# Data

This project uses **synthetic payment data only**. No real customer, cardholder, merchant or payment-network records will be stored in this repository.

Large generated datasets will remain outside GitHub. The repository will contain only small samples where useful for schema demonstration and testing.

Planned local structure:

```text
data/
|-- raw/
|-- processed/
`-- sample/
```

The full dataset will be reproducible from the Python generator in `src/` using documented configuration and a fixed random seed.
