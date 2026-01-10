from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    tables_figures: Path

    @staticmethod
    def from_src_file(src_file: str) -> "ProjectPaths":
        root = Path(src_file).resolve().parents[1]
        tf = root / "tables_figures"
        tf.mkdir(parents=True, exist_ok=True)
        return ProjectPaths(root=root, tables_figures=tf)


def get_engine():
    """
    Local PostgreSQL connection (Unix socket).
    Database: OutlierAnalytics
    """
    return create_engine("postgresql+psycopg2:///OutlierAnalytics", echo=False)


def load_integrated_dataframe() -> pd.DataFrame:
    """
    Builds an integrated transaction-level dataset from normalized tables:
      purchases (invoice header) + invoice_items (line items) + products + customers

    Returns a pandas DataFrame suitable for analytics + plots.
    """
    engine = get_engine()

    query = """
    SELECT
        p.invoice_id,
        p.purchase_date AS date,
        p.customer_id,
        c.customer_type,
        ii.product_id,
        pr.item,
        pr.category,
        pr.price AS product_price,
        ii.quantity,
        ii.unit_price AS price,
        COALESCE(ii.line_total, ii.quantity * ii.unit_price) AS line_total
    FROM purchases p
    JOIN customers c ON c.customer_id = p.customer_id
    JOIN invoice_items ii ON ii.invoice_id = p.invoice_id
    JOIN products pr ON pr.product_id = ii.product_id;
    """

    df = pd.read_sql(query, engine)

    # Type enforcement
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["line_total"] = pd.to_numeric(df["line_total"], errors="coerce")

    # Drop obviously broken rows
    df = df.dropna(subset=["invoice_id", "date", "customer_id", "product_id", "quantity", "price", "line_total"])

    # Derived time fields
    df["day_of_week"] = df["date"].dt.dayofweek  # 0=Mon
    df["day_name"] = df["date"].dt.day_name()

    return df
