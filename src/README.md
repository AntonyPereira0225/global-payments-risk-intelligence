# Source Code

Python source code for synthetic data generation, validation and feature engineering will live here.

Planned modules:

```text
src/
|-- config.py
|-- generate_dimensions.py
|-- generate_transactions.py
|-- validate_data.py
`-- feature_engineering.py
```

The generator will use a fixed random seed and explicit configuration so the dataset can be reproduced and scaled without committing multi-million-row outputs to GitHub.
