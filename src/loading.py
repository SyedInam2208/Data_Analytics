"""Data loading from CSV files."""

import pandas as pd
from pathlib import Path
from typing import Tuple, Dict


class DataLoader:

    def __init__(self, datasource_path: Path = Path("data") / "raw"):
        self.datasource_path = datasource_path
        self._validate_datasource_exists()

    def _validate_datasource_exists(self):
        if not self.datasource_path.exists():
            raise FileNotFoundError(f"Datasource directory not found: {self.datasource_path}")

    def load_customers(self) -> pd.DataFrame:
        filepath = self.datasource_path / "customers.csv"
        df = pd.read_csv(filepath)

        expected_cols = ['CustomerID', 'customer_type']
        assert list(df.columns) == expected_cols, f"Expected columns {expected_cols}, got {list(df.columns)}"

        df['CustomerID'] = df['CustomerID'].astype(str)
        print(f"Loaded customers: {len(df):,} records")
        return df

    def load_products(self) -> pd.DataFrame:
        filepath = self.datasource_path / "products.csv"
        df = pd.read_csv(filepath)

        expected_cols = ['product_id', 'item', 'category', 'price']
        assert list(df.columns) == expected_cols, f"Expected columns {expected_cols}, got {list(df.columns)}"

        df['product_id'] = df['product_id'].astype(str)
        df['price'] = pd.to_numeric(df['price'], errors='coerce')

        print(f"Loaded products: {len(df):,} records")
        return df

    def load_invoice_items(self) -> pd.DataFrame:
        filepath = self.datasource_path / "invoice_items.csv"
        df = pd.read_csv(filepath)

        expected_cols = ['InvoiceID', 'product_id', 'quantity', 'price', 'line_total']
        assert list(df.columns) == expected_cols, f"Expected columns {expected_cols}, got {list(df.columns)}"

        df['InvoiceID'] = df['InvoiceID'].astype(str)
        df['product_id'] = df['product_id'].astype(str)
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['line_total'] = pd.to_numeric(df['line_total'], errors='coerce')

        print(f"Loaded invoice_items: {len(df):,} records")
        return df

    def load_purchases(self) -> pd.DataFrame:
        filepath = self.datasource_path / "purchases.csv"
        df = pd.read_csv(filepath)

        expected_cols = ['InvoiceID', 'date', 'CustomerID', 'product_id', 'quantity']
        assert list(df.columns) == expected_cols, f"Expected columns {expected_cols}, got {list(df.columns)}"

        df['InvoiceID'] = df['InvoiceID'].astype(str)
        df['CustomerID'] = df['CustomerID'].astype(str)
        df['product_id'] = df['product_id'].astype(str)
        df['date'] = pd.to_datetime(df['date'])
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')

        print(f"Loaded purchases: {len(df):,} records")
        return df

    def load_all(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        print("=" * 60)
        print("LOADING DATA FILES")
        print("=" * 60)

        customers = self.load_customers()
        products = self.load_products()
        invoice_items = self.load_invoice_items()
        purchases = self.load_purchases()

        print("=" * 60)
        print(f"TOTAL RECORDS LOADED: {len(invoice_items):,}")
        print("=" * 60)
        print()

        return customers, products, invoice_items, purchases

    def get_data_quality_report(self, df: pd.DataFrame, name: str) -> Dict:
        report = {
            'dataset': name,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'null_counts': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'memory_usage': df.memory_usage(deep=True).sum() / 1024**2
        }
        return report

    def print_quality_reports(self, customers, products, invoice_items, purchases):
        print("\n" + "=" * 60)
        print("DATA QUALITY REPORT")
        print("=" * 60)

        for df, name in [(customers, 'customers'),
                         (products, 'products'),
                         (invoice_items, 'invoice_items'),
                         (purchases, 'purchases')]:
            report = self.get_data_quality_report(df, name)
            print(f"\n{name.upper()}:")
            print(f"  Rows: {report['total_rows']:,}")
            print(f"  Columns: {report['total_columns']}")
            print(f"  Duplicates: {report['duplicate_rows']:,}")
            print(f"  Null values: {sum(report['null_counts'].values())}")
            print(f"  Memory: {report['memory_usage']:.2f} MB")


def load_data(datasource_path: Path = Path("data") / "raw",
              print_report: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    loader = DataLoader(datasource_path)
    customers, products, invoice_items, purchases = loader.load_all()

    if print_report:
        loader.print_quality_reports(customers, products, invoice_items, purchases)

    return customers, products, invoice_items, purchases


if __name__ == "__main__":
    customers, products, invoice_items, purchases = load_data()
