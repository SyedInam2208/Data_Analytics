from pathlib import Path
from sqlalchemy import create_engine, text


def get_engine():
    return create_engine(
        "postgresql+psycopg2:///OutlierAnalytics",
        echo=False
    )


def run_schema(engine, sql_path: Path):
    with engine.begin() as conn:
        conn.execute(text(sql_path.read_text()))


def truncate_tables(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            TRUNCATE TABLE
                invoice_items,
                purchases,
                products,
                customers
            CASCADE;
        """))


def load_csv(engine, table_name: str, csv_path: Path):
    import pandas as pd
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, engine, if_exists="append", index=False)


def load_processed_data(processed_paths: dict, schema_sql: Path):
    engine = get_engine()

    run_schema(engine, schema_sql)
    truncate_tables(engine)

    load_csv(engine, "customers", processed_paths["customers"])
    load_csv(engine, "products", processed_paths["products"])
    load_csv(engine, "purchases", processed_paths["purchases"])
    load_csv(engine, "invoice_items", processed_paths["invoice_items"])
