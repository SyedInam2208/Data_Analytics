"""Data cleaning and integration."""

import pandas as pd
import numpy as np
from typing import Tuple, Dict


class DataCleaner:

    def __init__(self, customers: pd.DataFrame, products: pd.DataFrame,
                 invoice_items: pd.DataFrame, purchases: pd.DataFrame):
        self.customers = customers.copy()
        self.products = products.copy()
        self.invoice_items = invoice_items.copy()
        self.purchases = purchases.copy()
        self.cleaning_stats = {}

    def remove_duplicates(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        print("\n" + "=" * 60)
        print("REMOVING DUPLICATES")
        print("=" * 60)

        invoice_before = len(self.invoice_items)
        self.invoice_items = self.invoice_items.drop_duplicates()
        invoice_removed = invoice_before - len(self.invoice_items)
        print(f"Invoice Items: Removed {invoice_removed:,} duplicates ({invoice_removed/invoice_before*100:.2f}%)")

        purchases_before = len(self.purchases)
        self.purchases = self.purchases.drop_duplicates()
        purchases_removed = purchases_before - len(self.purchases)
        print(f"Purchases: Removed {purchases_removed:,} duplicates ({purchases_removed/purchases_before*100:.2f}%)")

        self.cleaning_stats['duplicates_removed'] = {
            'invoice_items': invoice_removed,
            'purchases': purchases_removed
        }

        return self.invoice_items, self.purchases

    def create_integrated_table(self) -> pd.DataFrame:
        """Join all tables using invoice_items as base."""
        print("\n" + "=" * 60)
        print("CREATING INTEGRATED TABLE")
        print("=" * 60)

        df = self.invoice_items.copy()
        initial_count = len(df)
        print(f"Base table (invoice_items): {initial_count:,} records")

        df = df.merge(
            self.purchases[['InvoiceID', 'product_id', 'date', 'CustomerID']],
            on=['InvoiceID', 'product_id'],
            how='left'
        )
        print(f"After joining purchases: {len(df):,} records")

        unmatched_purchases = df['CustomerID'].isna().sum()
        if unmatched_purchases > 0:
            print(f"  Warning: {unmatched_purchases:,} records without purchase data")

        df = df.merge(
            self.customers[['CustomerID', 'customer_type']],
            on='CustomerID',
            how='left'
        )
        print(f"After joining customers: {len(df):,} records")

        unmatched_customers = df['customer_type'].isna().sum()
        if unmatched_customers > 0:
            print(f"  Warning: {unmatched_customers:,} records without customer data")

        products_renamed = self.products.copy()
        products_renamed = products_renamed.rename(columns={'price': 'product_price'})

        df = df.merge(
            products_renamed[['product_id', 'item', 'category', 'product_price']],
            on='product_id',
            how='left'
        )
        print(f"After joining products: {len(df):,} records")

        unmatched_products = df['category'].isna().sum()
        if unmatched_products > 0:
            print(f"  Warning: {unmatched_products:,} records without product data")

        column_order = [
            'InvoiceID', 'date', 'CustomerID', 'customer_type',
            'product_id', 'item', 'category',
            'quantity', 'price', 'product_price', 'line_total'
        ]
        df = df[column_order]

        self.cleaning_stats['integration'] = {
            'initial_records': initial_count,
            'final_records': len(df),
            'unmatched_purchases': unmatched_purchases,
            'unmatched_customers': unmatched_customers,
            'unmatched_products': unmatched_products
        }

        print(f"\nIntegrated table created: {len(df):,} records")
        return df

    def apply_harmful_rules(self, df: pd.DataFrame, remove_harmful: bool = True) -> pd.DataFrame:
        """Apply harmful outlier detection rules."""
        print("\n" + "=" * 60)
        print("APPLYING HARMFUL OUTLIER RULES")
        print("=" * 60)

        df = df.copy()
        df['is_harmful'] = False
        df['harmful_reason'] = ''
        initial_count = len(df)

        rule1_mask = (df['price'] == 0) | (df['price'] < 0.01)
        rule1_count = rule1_mask.sum()
        df.loc[rule1_mask, 'is_harmful'] = True
        df.loc[rule1_mask, 'harmful_reason'] = 'pricing_error'
        print(f"Rule 1 (Pricing error): {rule1_count:,} records")

        rule2_mask = (df['customer_type'] == 'private') & (df['quantity'] > 10000)
        rule2_count = rule2_mask.sum()
        df.loc[rule2_mask, 'is_harmful'] = True
        df.loc[rule2_mask, 'harmful_reason'] = 'private_extreme_quantity'
        print(f"Rule 2 (Private extreme quantity >10,000): {rule2_count:,} records")

        rule3_mask = (df['customer_type'] == 'wholesaler') & (df['quantity'] > 100000)
        rule3_count = rule3_mask.sum()
        df.loc[rule3_mask, 'is_harmful'] = True
        df.loc[rule3_mask, 'harmful_reason'] = 'wholesaler_extreme_quantity'
        print(f"Rule 3 (Wholesaler extreme quantity >100,000): {rule3_count:,} records")

        calculated_price = df['line_total'] / df['quantity']
        price_diff_pct = np.abs(calculated_price - df['price']) / df['price'] * 100
        rule4_mask = price_diff_pct > 5
        rule4_count = rule4_mask.sum()
        df.loc[rule4_mask, 'is_harmful'] = True
        df.loc[rule4_mask, 'harmful_reason'] = 'calculation_error'
        print(f"Rule 4 (Calculation error >5% tolerance): {rule4_count:,} records")

        rule5_mask = (df['price'] > 1000)
        rule5_count = rule5_mask.sum()
        if rule5_count > 0:
            df.loc[rule5_mask, 'is_harmful'] = True
            df.loc[rule5_mask, 'harmful_reason'] = 'suspicious_price'
            print(f"Rule 5 (Suspicious price >1000): {rule5_count:,} records")

        total_harmful = df['is_harmful'].sum()
        print(f"\nTotal harmful records: {total_harmful:,} ({total_harmful/initial_count*100:.2f}%)")

        if remove_harmful:
            df_clean = df[~df['is_harmful']].copy()
            removed = initial_count - len(df_clean)
            print(f"Removed {removed:,} harmful records")
            self.cleaning_stats['harmful_removed'] = removed
            return df_clean.drop(columns=['is_harmful', 'harmful_reason'])
        else:
            print("Harmful records flagged but not removed")
            return df

    def remove_thursday_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove Thursday data due to data quality issue."""
        print("\n" + "=" * 60)
        print("REMOVING THURSDAY DATA (DATA QUALITY ISSUE)")
        print("=" * 60)

        initial_count = len(df)
        df = df.copy()

        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_name'] = df['date'].dt.day_name()

        thursday_mask = df['day_of_week'] == 3
        thursday_count = thursday_mask.sum()

        print(f"Thursday records: {thursday_count:,} ({thursday_count/initial_count*100:.2f}%)")
        print(f"Expected if uniform: ~{initial_count/7:,.0f} ({100/7:.1f}%)")

        df_clean = df[~thursday_mask].copy()
        removed = initial_count - len(df_clean)

        print(f"Removed {removed:,} Thursday records")
        self.cleaning_stats['thursday_removed'] = removed

        return df_clean.drop(columns=['day_of_week', 'day_name'])

    def add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add temporal and price-related features."""
        print("\n" + "=" * 60)
        print("ADDING DERIVED FEATURES")
        print("=" * 60)

        df = df.copy()

        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_name'] = df['date'].dt.day_name()
        df['is_weekend'] = df['day_of_week'].isin([5, 6])
        df['is_peak_season'] = df['month'].isin([9, 10, 11])
        df['is_off_season'] = df['month'].isin([1, 2])
        df['quarter'] = df['date'].dt.quarter

        df['price_vs_product_price'] = df['price'] / df['product_price']
        df['price_discount_pct'] = (1 - df['price_vs_product_price']) * 100
        df['revenue'] = df['line_total']
        df['calculated_line_total'] = df['quantity'] * df['price']
        df['line_total_error'] = np.abs(df['line_total'] - df['calculated_line_total'])

        print("Added temporal features: year, month, day_of_week, is_weekend, is_peak_season")
        print("Added price features: price_vs_product_price, price_discount_pct")
        print("Added revenue and calculation verification features")

        return df

    def get_cleaning_summary(self) -> Dict:
        return self.cleaning_stats

    def print_cleaning_summary(self):
        print("\n" + "=" * 60)
        print("CLEANING SUMMARY")
        print("=" * 60)

        if 'duplicates_removed' in self.cleaning_stats:
            dup = self.cleaning_stats['duplicates_removed']
            print(f"\nDuplicates Removed:")
            print(f"  Invoice Items: {dup['invoice_items']:,}")
            print(f"  Purchases: {dup['purchases']:,}")

        if 'integration' in self.cleaning_stats:
            integ = self.cleaning_stats['integration']
            print(f"\nIntegration:")
            print(f"  Initial records: {integ['initial_records']:,}")
            print(f"  Final records: {integ['final_records']:,}")
            print(f"  Unmatched records: {integ['unmatched_purchases'] + integ['unmatched_customers'] + integ['unmatched_products']:,}")

        if 'harmful_removed' in self.cleaning_stats:
            print(f"\nHarmful Records Removed: {self.cleaning_stats['harmful_removed']:,}")

        if 'thursday_removed' in self.cleaning_stats:
            print(f"Thursday Records Removed: {self.cleaning_stats['thursday_removed']:,}")

        print("=" * 60)


def clean_and_integrate_data(customers: pd.DataFrame,
                              products: pd.DataFrame,
                              invoice_items: pd.DataFrame,
                              purchases: pd.DataFrame,
                              remove_harmful: bool = True,
                              remove_thursday: bool = True,
                              add_features: bool = True) -> pd.DataFrame:
    """Clean and integrate all data."""
    print("\n" + "=" * 60)
    print("DATA CLEANING AND INTEGRATION PIPELINE")
    print("=" * 60)

    cleaner = DataCleaner(customers, products, invoice_items, purchases)

    cleaner.remove_duplicates()
    df = cleaner.create_integrated_table()
    df = cleaner.apply_harmful_rules(df, remove_harmful=remove_harmful)

    if remove_thursday:
        df = cleaner.remove_thursday_data(df)

    if add_features:
        df = cleaner.add_derived_features(df)

    cleaner.print_cleaning_summary()

    print(f"\nFinal cleaned dataset: {len(df):,} records with {len(df.columns)} columns")
    print("=" * 60)

    return df


if __name__ == "__main__":
    from loading import load_data

    print("Loading data...")
    customers, products, invoice_items, purchases = load_data(print_report=False)

    print("\nCleaning and integrating data...")
    df_clean = clean_and_integrate_data(
        customers, products, invoice_items, purchases,
        remove_harmful=True,
        remove_thursday=True,
        add_features=True
    )

    print("\n" + "=" * 60)
    print("SAMPLE OF CLEANED DATA")
    print("=" * 60)
    print(df_clean.head(10))

    print("\n" + "=" * 60)
    print("DATA INFO")
    print("=" * 60)
    print(df_clean.info())
