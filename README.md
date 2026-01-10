### *** Data_Analytics *** ###

UE_Sem-1_DA_Project
----
Project Overview

This project implements a context-aware outlier analytics framework on transactional retail data.
Instead of treating all statistical outliers as noise, the project distinguishes between:

- Harmful outliers – data quality issues that distort KPIs
- Benign outliers – statistically rare but business-neutral
- Strategic outliers – rare, high-value transactions that should be preserved

The framework combines:

- Statistical analysis
- Context-aware machine learning
- KPI distortion analysis
- Explainability and stability validation

```text
Data_Analytics/
├── data/
│   ├── RAW/                    # Original CSV files
│   └── processed/              # Cleaned & feature-engineered data
├── src/
│   ├── cleaning.py
│   ├── loading.py
│   ├── run_data_pipeline.py
│   ├── rq1_prepare_dataset.py
│   ├── rq1_model_train_eval.py
│   ├── rq1_context_contribution.py
│   ├── rq2_kpi_distortion.py
│   ├── rq3_strategic_value.py
│   └── rq4_explainability_validation.py
├── db/
│   └── create_tables.sql       # PostgreSQL schema
├── tables_figures/             # All generated tables & figures (RQ-wise)
├── requirements.txt
├── RQ_KPI.md
└── README.md

```
Integrated Table Structure (Master DataFrame)

This section describes the integrated dataset created after cleaning and feature engineering.

1. Core Information

- invoice_id – Unique identifier for each transaction
- date – Date of the transaction
- customer_id – Unique identifier for each customer
- customer_type – Customer segment (private / wholesaler)

2. Product Details

- product_id – Unique product identifier
- item – Product name
- category – Product category

3. Transaction Metrics

- quantity – Number of units purchased
- price – Transaction price (after discounts)
- product_price – Original list price
- line_total – quantity × price

4. Derived Features
*** Temporal Features:
   year, month, quarter
   day_of_week, day_name
   is_weekend
   is_peak_season (Sep–Nov)
   is_off_season (Jan–Feb)

*** Pricing & Validation Features:
   price_vs_product_price
   price_discount_pct
   calculated_line_total
   line_total_error

----

## Understanding the Research Questions

Research Question Implementation Mapping
| Research Question                           | Script                                                                             |
| ------------------------------------------- | ---------------------------------------------------------------------------------- |
| RQ1 – Context-aware outlier classification  | `rq1_prepare_dataset.py`, `rq1_model_train_eval.py`, `rq1_context_contribution.py` |
| RQ2 – KPI distortion analysis               | `rq2_kpi_distortion.py`                                                            |
| RQ3 – Strategic value preservation          | `rq3_strategic_value.py`                                                           |
| RQ4 – Explainability & stability validation | `rq4_explainability_validation.py`                                                 |


For a detailed explanation of the research questions, objectives, and key performance indicators (KPIs), please refer to the file:

- **`RQ_KPI.md`**

This document provides the formal definition of all research questions (RQ1–RQ4) and explains how each analytical component of the project is evaluated.


All generated tables and figures are saved in the tables_figures/ directory using the naming convention:
- RQ1_Tb1.xlsx, RQ1_Tb2.xlsx, ...
- RQ2_Tb1.xlsx, ...
- RQ4_Tb3.xlsx

----

*** How to Execute the Project (From Scratch)

This section explains how to run the entire project on a new system, including database setup.

Step 1: Install Python Dependencies

Create/activate a Python environment (recommended) and install dependencies:

```text
pip install -r requirements.txt
```

Step 2: Install and Start PostgreSQL

Ensure PostgreSQL is installed and running.

Check installation:

```text
psql --version
```

Start PostgreSQL service (example for macOS with Homebrew):

```text
brew services start postgresql
```

Step 3: Create the PostgreSQL Database (Required)

The project expects a PostgreSQL database named:

*** OutlierAnalytics


Create it using the terminal:

```text
psql postgres
```

Inside the PostgreSQL prompt, run:

```text
CREATE DATABASE "OutlierAnalytics";
```



✅ No tables need to be created manually — they are created automatically by the pipeline using create_tables.sql.

Step 4: Run the Entire Project (One Command)

From the project root directory, run:

```text
python src/run_data_pipeline.py
```

This single command will:

- Clean raw CSV data
- Generate processed datasets
- Create / recreate database tables
- Load cleaned data into PostgreSQL
- Execute RQ1 → RQ4 analytics scripts
- Generate all tables and figures

Outputs

After successful execution:
- Processed data → data/processed/
- Database tables → PostgreSQL (OutlierAnalytics)
- All analytical results → tables_figures/

Naming convention:
```text
RQ1_Tb1.xlsx, RQ1_Tb2.xlsx, ...
RQ2_Tb1.xlsx, ...
RQ4_Tb3.xlsx
```

Notes for Evaluation

- The project is fully reproducible
- No notebooks are required
- All steps are script-based
- The pipeline can be rerun multiple times safely
- Explainability is validated using:
    - Feature attribution
    - Business rule alignment
    - Stability analysis across retraining
