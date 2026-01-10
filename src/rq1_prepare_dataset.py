from __future__ import annotations

from pathlib import Path
import pandas as pd

from analytics_utils import ProjectPaths, load_integrated_dataframe


def iqr_bounds(series: pd.Series, k: float = 1.5) -> tuple[float, float]:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    return float(q1 - k * iqr), float(q3 + k * iqr)


def main():
    paths = ProjectPaths.from_src_file(__file__)
    df = load_integrated_dataframe()

    # ---- Invoice-level dataset ----
    # Invoice revenue
    inv = (
        df.groupby(["invoice_id", "date", "customer_id", "customer_type"], as_index=False)
          .agg(
              invoice_revenue=("line_total", "sum"),
              total_qty=("quantity", "sum"),
              avg_price=("price", "mean"),
              n_items=("product_id", "nunique"),
          )
    )

    # Dominant category per invoice (by revenue)
    cat_rev = (
        df.groupby(["invoice_id", "category"], as_index=False)
          .agg(cat_revenue=("line_total", "sum"))
          .sort_values(["invoice_id", "cat_revenue"], ascending=[True, False])
    )
    dom_cat = cat_rev.drop_duplicates("invoice_id")[["invoice_id", "category"]].rename(columns={"category": "dominant_category"})
    inv = inv.merge(dom_cat, on="invoice_id", how="left")

    # Temporal features
    inv["date"] = pd.to_datetime(inv["date"])
    inv["month"] = inv["date"].dt.month
    inv["day_of_week"] = inv["date"].dt.dayofweek
    inv["is_weekend"] = inv["day_of_week"].isin([5, 6])
    inv["is_peak_season"] = inv["month"].isin([9, 10, 11])
    inv["is_off_season"] = inv["month"].isin([1, 2])

    # Statistical outliers on invoice revenue (use percentile for better coverage)
    hi = inv["invoice_revenue"].quantile(0.99)
    lo = inv["invoice_revenue"].quantile(0.01)
    inv["is_statistical_outlier"] = (inv["invoice_revenue"] >= hi) | (inv["invoice_revenue"] <= lo)

    # Harmful: invoice-level data-quality rules
    inv["is_harmful"] = (
        (inv["total_qty"] <= 0) |
        (inv["avg_price"] <= 0) |
        (inv["avg_price"] < 0.1) |
        (inv["total_qty"] > 10000)
        )

    # Strategic: wholesaler bulk OR very high revenue (but not harmful)
    _, qty_hi = iqr_bounds(inv["total_qty"], k=1.5)
    _, rev_hi = iqr_bounds(inv["invoice_revenue"], k=1.5)

    inv["is_strategic"] = (
        ((inv["customer_type"].str.lower() == "wholesaler") & (inv["total_qty"] > qty_hi)) |
        ((inv["invoice_revenue"] > rev_hi) & (~inv["is_harmful"]))
        )

    # Benign: statistically extreme but business-neutral proxy
    inv["is_benign"] = (
    inv["is_statistical_outlier"] &
    (inv["customer_type"].str.lower() == "private") &
    (~inv["is_harmful"]) &
    (~inv["is_strategic"]) &
    (inv["total_qty"] <= qty_hi)
    )

    # Final label (3-way + Normal)
    def label_row(r):
        if r["is_harmful"]:
            return "Harmful"
        if r["is_strategic"]:
            return "Strategic"
        if r["is_benign"]:
            return "Benign"
        return "Normal"

    inv["outlier_class"] = inv.apply(label_row, axis=1)

    # Keep only statistical outliers for modeling task
    model_df = inv.loc[inv["is_statistical_outlier"]].copy()



    # Save dataset
    out_path = paths.root / "data" / "processed" / "rq1_model_dataset.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model_df.to_csv(out_path, index=False)

    print(f"[RQ1] Saved modeling dataset: {out_path}")
    print(model_df["outlier_class"].value_counts(dropna=False))


if __name__ == "__main__":
    main()
