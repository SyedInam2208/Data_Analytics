#!/usr/bin/env python3
"""
Main script to run the complete data loading and cleaning pipeline.

Usage:
    python run_data_pipeline.py

Output:
    - cleaned_data.csv: Final cleaned and integrated dataset
    - cleaning_report.txt: Detailed cleaning statistics
"""

import sys
from pathlib import Path
from cleaning import DataCleaner
from loading import load_data
from cleaning import clean_and_integrate_data

# Add current directory to path to import data module
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Run the complete data pipeline."""
    print("\n" + "=" * 60)
    print("DATA LOADING AND CLEANING PIPELINE")
    print("=" * 60)
    print()

    # Configuration
    config = {
        'datasource_path': Path('data') / 'raw',
        'output_file': Path('data') / 'final' / 'cleaned_data.csv',
        'remove_harmful': True,
        'remove_thursday': True,
        'add_features': True
    }

    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()

    # Step 1: Load data
    print("STEP 1: Loading data...")
    try:
        customers, products, invoice_items, purchases = load_data(
            datasource_path=config['datasource_path'],
            print_report=True
        )
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the 'datasource' directory exists with the following CSV files:")
        print("  - customers.csv")
        print("  - products.csv")
        print("  - invoice_items.csv")
        print("  - purchases.csv")
        sys.exit(1)

    # Step 2: Clean and integrate
    print("\nSTEP 2: Cleaning and integrating data...")
    df_clean = clean_and_integrate_data(
        customers=customers,
        products=products,
        invoice_items=invoice_items,
        purchases=purchases,
        remove_harmful=config['remove_harmful'],
        remove_thursday=config['remove_thursday'],
        add_features=config['add_features']
    )

    # Step 3: Save results
    print(f"\nSTEP 3: Saving cleaned data to '{config['output_file']}'...")
    df_clean.to_csv(config['output_file'], index=False)
    print(f"✓ Saved {len(df_clean):,} records to {config['output_file']}")

    # Step 4: Generate data quality report
    print("\nSTEP 4: Generating data quality report...")

    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("DATA QUALITY REPORT")
    report_lines.append("=" * 60)
    report_lines.append("")

    # Basic info
    report_lines.append("DATASET SUMMARY")
    report_lines.append("-" * 60)
    report_lines.append(f"Total records: {len(df_clean):,}")
    report_lines.append(f"Total columns: {len(df_clean.columns)}")
    report_lines.append(f"Memory usage: {df_clean.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    report_lines.append("")

    # Date range
    report_lines.append("DATE RANGE")
    report_lines.append("-" * 60)
    report_lines.append(f"From: {df_clean['date'].min().date()}")
    report_lines.append(f"To: {df_clean['date'].max().date()}")
    report_lines.append(f"Days: {(df_clean['date'].max() - df_clean['date'].min()).days}")
    report_lines.append("")

    # Customer distribution
    report_lines.append("CUSTOMER DISTRIBUTION")
    report_lines.append("-" * 60)
    customer_dist = df_clean['customer_type'].value_counts()
    for ctype, count in customer_dist.items():
        pct = count / len(df_clean) * 100
        report_lines.append(f"{ctype:15s}: {count:8,} ({pct:5.2f}%)")
    report_lines.append("")

    # Temporal distribution
    report_lines.append("TEMPORAL DISTRIBUTION")
    report_lines.append("-" * 60)
    report_lines.append("By Day of Week:")
    dow_dist = df_clean['day_name'].value_counts().sort_index()
    for day, count in dow_dist.items():
        pct = count / len(df_clean) * 100
        report_lines.append(f"  {day:10s}: {count:8,} ({pct:5.2f}%)")
    report_lines.append("")

    report_lines.append("By Season:")
    peak_count = df_clean['is_peak_season'].sum()
    off_count = df_clean['is_off_season'].sum()
    normal_count = len(df_clean) - peak_count - off_count
    report_lines.append(f"  Peak (Sep-Nov): {peak_count:8,} ({peak_count/len(df_clean)*100:5.2f}%)")
    report_lines.append(f"  Off (Jan-Feb):  {off_count:8,} ({off_count/len(df_clean)*100:5.2f}%)")
    report_lines.append(f"  Normal:         {normal_count:8,} ({normal_count/len(df_clean)*100:5.2f}%)")
    report_lines.append("")

    # Statistics
    report_lines.append("KEY STATISTICS")
    report_lines.append("-" * 60)
    stats = df_clean[['quantity', 'price', 'line_total']].describe()
    report_lines.append(stats.to_string())
    report_lines.append("")

    # Data quality checks
    report_lines.append("DATA QUALITY CHECKS")
    report_lines.append("-" * 60)
    null_counts = df_clean.isnull().sum()
    null_total = null_counts.sum()
    report_lines.append(f"Total NULL values: {null_total}")
    if null_total > 0:
        report_lines.append("\nColumns with NULL values:")
        for col, count in null_counts[null_counts > 0].items():
            report_lines.append(f"  {col}: {count}")
    else:
        report_lines.append("  ✓ No NULL values found")
    report_lines.append("")

    duplicates = df_clean.duplicated().sum()
    report_lines.append(f"Duplicate records: {duplicates}")
    if duplicates > 0:
        report_lines.append("  ⚠ Warning: Duplicates found after cleaning")
    else:
        report_lines.append("  ✓ No duplicates")
    report_lines.append("")

    # Price calculation errors
    price_errors = df_clean[df_clean['line_total_error'] > 0.01]
    report_lines.append(f"Price calculation errors (>$0.01): {len(price_errors)}")
    if len(price_errors) > 0:
        report_lines.append(f"  ⚠ {len(price_errors)/len(df_clean)*100:.2f}% of records have calculation errors")
    else:
        report_lines.append("  ✓ All prices calculated correctly")

    report_lines.append("")
    report_lines.append("=" * 60)

    # Print to console
    report_text = "\n".join(report_lines)
    print("\n" + report_text)

    # Save to file
    with open(Path('data') / 'final' / 'cleaning_report.txt', 'w') as f:
        f.write(report_text)
    print(f"\n✓ Report saved to 'cleaning_report.txt'")

    # Step 5: Quick preview
    print("\n" + "=" * 60)
    print("PREVIEW OF CLEANED DATA (first 10 rows)")
    print("=" * 60)
    print(df_clean.head(10).to_string())

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  1. {config['output_file']} - Cleaned dataset ({len(df_clean):,} records)")
    print(f"  2. cleaning_report.txt - Data quality report")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
