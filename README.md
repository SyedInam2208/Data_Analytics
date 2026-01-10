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

Data_Analytics/
│
├── data/
│   ├── RAW/                # Original CSV files
│   └── processed/          # Cleaned & feature-engineered data
│
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
│
├── db/
│   └── create_tables.sql   # PostgreSQL schema
│
├── tables_figures/         # All generated tables & figures (RQ-wise)
│
├── requirements.txt
└── README.md


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
