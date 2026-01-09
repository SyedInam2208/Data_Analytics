# Data_Analytics
UE_Sem-1_DA_Project

## How to Run the Code
Follow these instructions to execute the pipeline manually:

1. **Install Dependencies:**
   Run the command: `pip install -r requirements.txt`

2. **Execute Stage Scripts (Sequential):**
   - **Pipeline:** `python src/run_data_pipeline.py`
   - **Ingestion:** `python src/loading.py`
   - **Cleaning:** `python src/cleaning.py`

## Integrated Table Structure (Master DataFrame)

This document outlines the schema of the integrated table generated after the data cleaning and feature engineering process.

### 1. Core Information
- **`InvoiceID`**: Unique identifier for each transaction
- **`date`**: Date of the transaction
- **`CustomerID`**: Unique identifier for each customer
- **`customer_type`**: Customer segment (**private** or **wholesaler**)

### 2. Product Details
- **`product_id`**: Unique identifier for each product
- **`item`**: Product name
- **`category`**: Product category

### 3. Transaction Metrics
- **`quantity`**: Number of units purchased
- **`price`**: Actual transaction price (after discounts)
- **`product_price`**: Original list price of the product
- **`line_total`**: Total transaction value (`quantity` × `price`)

### 4. Derived Features (Enabled when `add_features=True`)

#### Temporal Features
- **`year`, `month`, `quarter`**: Year, month, and quarter of the transaction
- **`day_of_week`**: Numeric day of the week (0 = Monday, 6 = Sunday)
- **`day_name`**: Name of the day of the week
- **`is_weekend`**: Boolean flag for weekend transactions
- **`is_peak_season`**: Boolean flag for high-volume season (**Sep–Nov**)
- **`is_off_season`**: Boolean flag for low-volume season (**Jan–Feb**)

#### Pricing Features
- **`price_vs_product_price`**: Ratio of the transaction price to the list price
- **`price_discount_pct`**: Applied discount percentage (%)

#### Validation Metrics
- **`calculated_line_total`**: Re-computed total value (`quantity` × `price`) for verification
- **`line_total_error`**: Difference between the recorded `line_total` and the `calculated_line_total`