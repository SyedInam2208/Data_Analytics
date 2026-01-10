from pathlib import Path
import pandas as pd


RAW_FILES = {
    "customers": "customers.csv",
    "products": "products.csv",
    "purchases": "purchases.csv",
    "invoice_items": "invoice_items.csv",
}


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing RAW file: {path}")
    return pd.read_csv(path)


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    # RAW: CustomerID, customer_type
    df = df.rename(columns={"CustomerID": "customer_id"})
    df = df.dropna(subset=["customer_id"])
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    if "customer_type" in df.columns:
        df["customer_type"] = df["customer_type"].astype(str).str.strip()
    return df.drop_duplicates()


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    # RAW: product_id, item, category, price
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]  # keep names, but ensure clean
    df = df.dropna(subset=["product_id"])
    df["product_id"] = df["product_id"].astype(str).str.strip()

    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df = df.dropna(subset=["price"])
        df = df[df["price"] >= 0]

    return df.drop_duplicates()


def clean_purchases(df: pd.DataFrame) -> pd.DataFrame:
    """
    RAW purchases.csv columns:
      InvoiceID, date, CustomerID, product_id, quantity

    We normalize purchases into an invoice-level table:
      invoice_id, purchase_date, customer_id

    We ignore product_id/quantity here because invoice_items.csv is the line-item table.
    """
    df = df.rename(columns={
        "InvoiceID": "invoice_id",
        "CustomerID": "customer_id",
        "date": "purchase_date",
    })

    # Keep only invoice-level columns
    keep_cols = [c for c in ["invoice_id", "purchase_date", "customer_id"] if c in df.columns]
    df = df[keep_cols].copy()

    df = df.dropna(subset=["invoice_id", "customer_id"])
    df["invoice_id"] = df["invoice_id"].astype(str).str.strip()
    df["customer_id"] = df["customer_id"].astype(str).str.strip()

    if "purchase_date" in df.columns:
        df["purchase_date"] = pd.to_datetime(df["purchase_date"], errors="coerce")
        df = df.dropna(subset=["purchase_date"])

    # One row per invoice (invoice header)
    df = df.drop_duplicates(subset=["invoice_id"])

    return df


def clean_invoice_items(df: pd.DataFrame) -> pd.DataFrame:
    # RAW: InvoiceID, product_id, quantity, price, line_total
    df = df.rename(columns={
        "InvoiceID": "invoice_id",
        "price": "unit_price",
    })

    # Mandatory identifiers
    df = df.dropna(subset=["invoice_id", "product_id"])
    df["invoice_id"] = df["invoice_id"].astype(str).str.strip()
    df["product_id"] = df["product_id"].astype(str).str.strip()

    # Quantity numeric and > 0
    if "quantity" in df.columns:
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
        df = df.dropna(subset=["quantity"])
        df = df[df["quantity"] > 0]

    # Unit price numeric and >= 0
    if "unit_price" in df.columns:
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
        df = df.dropna(subset=["unit_price"])
        df = df[df["unit_price"] >= 0]

    # Line total numeric if present
    if "line_total" in df.columns:
        df["line_total"] = pd.to_numeric(df["line_total"], errors="coerce")

    return df.drop_duplicates()


def clean_and_write_processed(raw_dir: Path, processed_dir: Path) -> dict:
    ensure_dir(processed_dir)

    customers = clean_customers(read_csv(raw_dir / RAW_FILES["customers"]))
    products = clean_products(read_csv(raw_dir / RAW_FILES["products"]))
    purchases = clean_purchases(read_csv(raw_dir / RAW_FILES["purchases"]))
    invoice_items = clean_invoice_items(read_csv(raw_dir / RAW_FILES["invoice_items"]))

    paths = {
        "customers": processed_dir / "customers_clean.csv",
        "products": processed_dir / "products_clean.csv",
        "purchases": processed_dir / "purchases_clean.csv",
        "invoice_items": processed_dir / "invoice_items_clean.csv",
    }

    customers.to_csv(paths["customers"], index=False)
    products.to_csv(paths["products"], index=False)
    purchases.to_csv(paths["purchases"], index=False)
    invoice_items.to_csv(paths["invoice_items"], index=False)

    return paths
