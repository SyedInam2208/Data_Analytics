from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from analytics_utils import ProjectPaths, load_integrated_dataframe
from plotting_utils import save_excel_with_sheets, save_pdf


def flag_harmful(df: pd.DataFrame) -> pd.Series:
    return (
        (df["price"] <= 0) |
        (df["quantity"] <= 0) |
        (df["price"] < 0.1) |
        (df["quantity"] > 10000)
    )


def invoice_level(df: pd.DataFrame) -> pd.DataFrame:
    temp = df.copy()
    temp["day_name"] = temp["date"].dt.day_name()

    inv = (
        temp.groupby(["invoice_id", "date", "day_name", "customer_id", "customer_type"], as_index=False)
            .agg(
                revenue=("line_total", "sum"),
                items=("product_id", "nunique"),
                qty=("quantity", "sum"),
            )
    )
    return inv


def compute_kpis_from_invoice(inv: pd.DataFrame) -> dict:
    total_revenue = float(inv["revenue"].sum())
    invoices = int(inv["invoice_id"].nunique())
    customers = int(inv["customer_id"].nunique())
    aov = total_revenue / invoices if invoices else 0.0
    rpc = total_revenue / customers if customers else 0.0
    return {
        "Total_Revenue": total_revenue,
        "AOV": float(aov),
        "Revenue_per_Customer": float(rpc),
        "Invoices": invoices,
        "Customers": customers
    }


def distortion(with_val: float, without_val: float) -> tuple[float, float]:
    if without_val == 0:
        return 0.0, 0.0
    direction = (with_val - without_val) / without_val * 100.0
    magnitude = abs(direction)
    return float(magnitude), float(direction)


def main():
    paths = ProjectPaths.from_src_file(__file__)
    df = load_integrated_dataframe()

    harmful = flag_harmful(df)
    df_with = df.copy()
    df_without = df.loc[~harmful].copy()

    inv_with = invoice_level(df_with)
    inv_without = invoice_level(df_without)

    k_with = compute_kpis_from_invoice(inv_with)
    k_without = compute_kpis_from_invoice(inv_without)

    # --------------------
    # TABLES (primary for values)
    # --------------------
    rows = []
    for kpi in ["Total_Revenue", "AOV", "Revenue_per_Customer"]:
        mag, direction = distortion(k_with[kpi], k_without[kpi])
        rows.append({
            "KPI": kpi,
            "With_Harmful": k_with[kpi],
            "Without_Harmful": k_without[kpi],
            "Distortion_Magnitude_%": mag,
            "Distortion_Direction_%": direction,
            "Direction_Label": "Overestimation" if direction > 0 else ("Underestimation" if direction < 0 else "No change"),
        })
    tb1_summary = pd.DataFrame(rows)
    tb1_meta = pd.DataFrame([{
        "Rows_total": len(df),
        "Harmful_rows": int(harmful.sum()),
        "Harmful_rate_%": float(harmful.mean() * 100),
        "Invoices_total": k_with["Invoices"],
        "Customers_total": k_with["Customers"],
    }])

    # Distortion by customer_type
    seg_rows = []
    for seg in sorted(df["customer_type"].dropna().unique()):
        invw = invoice_level(df_with[df_with["customer_type"] == seg])
        invwo = invoice_level(df_without[df_without["customer_type"] == seg])
        kw = compute_kpis_from_invoice(invw)
        kwo = compute_kpis_from_invoice(invwo)
        for kpi in ["Total_Revenue", "AOV", "Revenue_per_Customer"]:
            mag, direction = distortion(kw[kpi], kwo[kpi])
            seg_rows.append({
                "customer_type": seg,
                "KPI": kpi,
                "With_Harmful": kw[kpi],
                "Without_Harmful": kwo[kpi],
                "Distortion_Magnitude_%": mag,
                "Distortion_Direction_%": direction,
            })
    tb2_by_segment = pd.DataFrame(seg_rows)

    # Top harmful transactions
    tb3_top_harmful = (
        df_with.loc[harmful, ["invoice_id", "date", "customer_id", "customer_type", "product_id", "category", "quantity", "price", "line_total"]]
        .sort_values("line_total", ascending=False)
        .head(20)
        .reset_index(drop=True)
    )

    # Day-of-week anomaly profile (invoice count + revenue)
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    tb4_dow = (
        inv_with.groupby("day_name", as_index=False)
        .agg(invoices=("invoice_id", "nunique"),
             revenue=("revenue", "sum"))
    )
    tb4_dow["day_name"] = pd.Categorical(tb4_dow["day_name"], categories=day_order, ordered=True)
    tb4_dow = tb4_dow.sort_values("day_name").reset_index(drop=True)

    save_excel_with_sheets(paths.tables_figures / "RQ2_Tb1.xlsx", {
        "Distortion_Summary": tb1_summary,
        "Meta": tb1_meta
    })
    save_excel_with_sheets(paths.tables_figures / "RQ2_Tb2.xlsx", {"Distortion_by_Segment": tb2_by_segment})
    save_excel_with_sheets(paths.tables_figures / "RQ2_Tb3.xlsx", {"Top_Harmful_Transactions": tb3_top_harmful})
    save_excel_with_sheets(paths.tables_figures / "RQ2_Tb4.xlsx", {"DayOfWeek_Profile": tb4_dow})

    # --------------------
    # FIGURES (only non-duplicate insights)
    # --------------------

    # Fig1: Daily revenue time-series with vs without harmful
    inv_with2 = inv_with.copy()
    inv_without2 = inv_without.copy()
    inv_with2["date_day"] = inv_with2["date"].dt.floor("D")
    inv_without2["date_day"] = inv_without2["date"].dt.floor("D")

    inv_with_daily = (
        inv_with2.groupby("date_day", as_index=False)["revenue"]
        .sum()
        .rename(columns={"date_day": "date", "revenue": "with_harmful"})
    )
    inv_wo_daily = (
        inv_without2.groupby("date_day", as_index=False)["revenue"]
        .sum()
        .rename(columns={"date_day": "date", "revenue": "without_harmful"})
    )
    ts = pd.merge(inv_with_daily, inv_wo_daily, on="date", how="inner")

    fig1, ax1 = plt.subplots()
    ax1.plot(ts["date"], ts["with_harmful"], label="With harmful")
    ax1.plot(ts["date"], ts["without_harmful"], label="Without harmful")
    ax1.set_title("RQ2: Daily revenue trend (with vs without harmful outliers)")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Revenue (currency units)")
    ax1.legend()
    save_pdf(fig1, paths.tables_figures / "RQ2_Fig1.pdf")

    # Fig2: Day-of-week (invoices + revenue twin axis)
    fig2, ax2 = plt.subplots()
    ax2.bar(tb4_dow["day_name"].astype(str), tb4_dow["invoices"])
    ax2.set_xlabel("Day of Week")
    ax2.set_ylabel("Invoice count")
    ax2.set_title("RQ2: Day-of-week distribution (Invoices and Revenue)")

    ax2b = ax2.twinx()
    ax2b.plot(tb4_dow["day_name"].astype(str), tb4_dow["revenue"], marker="o")
    ax2b.set_ylabel("Revenue (currency units)")
    fig2.autofmt_xdate(rotation=20)
    save_pdf(fig2, paths.tables_figures / "RQ2_Fig2.pdf")

    # Fig3: Distribution of line_total (log count) harmful vs non-harmful
    fig3, ax3 = plt.subplots()
    ax3.hist(df_without["line_total"], bins=50, alpha=0.7, label="Non-harmful")
    ax3.hist(df_with.loc[harmful, "line_total"], bins=50, alpha=0.7, label="Harmful")
    ax3.set_yscale("log")
    ax3.set_xlabel("Line total (currency units)")
    ax3.set_ylabel("Count (log scale)")
    ax3.set_title("RQ2: Transaction value distribution (harmful vs non-harmful)")
    ax3.legend()
    save_pdf(fig3, paths.tables_figures / "RQ2_Fig3.pdf")

    print("Tables and Figures Generated Successfully for RQ2")


if __name__ == "__main__":
    main()
