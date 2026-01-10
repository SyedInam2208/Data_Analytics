from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt

from analytics_utils import ProjectPaths, load_integrated_dataframe
from plotting_utils import save_excel_with_sheets, save_pdf


def iqr_bounds(series: pd.Series, k: float = 1.5) -> tuple[float, float]:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    return float(q1 - k * iqr), float(q3 + k * iqr)


def flag_stat_outlier(df: pd.DataFrame) -> pd.Series:
    lo, hi = iqr_bounds(df["line_total"], 1.5)
    return (df["line_total"] < lo) | (df["line_total"] > hi)


def flag_harmful(df: pd.DataFrame) -> pd.Series:
    return (
        (df["price"] <= 0) |
        (df["quantity"] <= 0) |
        (df["price"] < 0.1) |
        (df["quantity"] > 10000)
    )


def flag_strategic(df: pd.DataFrame) -> pd.Series:
    harmful = flag_harmful(df)
    _, qhi = iqr_bounds(df["quantity"], 1.5)
    _, lthi = iqr_bounds(df["line_total"], 1.5)

    wholesaler_bulk = (df["customer_type"].str.lower() == "wholesaler") & (df["quantity"] > qhi)
    high_value = (df["line_total"] > lthi) & (~harmful)
    return wholesaler_bulk | high_value


def invoice_level(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["invoice_id", "date", "customer_id", "customer_type"], as_index=False)
          .agg(revenue=("line_total", "sum"))
    )


def aov(inv: pd.DataFrame) -> float:
    r = inv["revenue"].sum()
    n = inv["invoice_id"].nunique()
    return float(r / n) if n else 0.0


def trimmed_mean(series: pd.Series, trim: float = 0.05) -> float:
    s = series.dropna().sort_values()
    if len(s) == 0:
        return 0.0
    k = int(len(s) * trim)
    s2 = s.iloc[k:len(s)-k] if len(s) > 2*k else s
    return float(s2.mean())


def main():
    paths = ProjectPaths.from_src_file(__file__)
    df = load_integrated_dataframe()
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()

    is_out = flag_stat_outlier(df)
    is_harm = flag_harmful(df)
    is_strat = flag_strategic(df)

    # Approaches
    df_blanket = df.loc[~is_out].copy()
    df_context = df.loc[~is_harm].copy()  # remove only harmful

    inv_blanket = invoice_level(df_blanket)
    inv_context = invoice_level(df_context)

    aov_blanket = aov(inv_blanket)
    aov_context = aov(inv_context)

    # Ground truth proxy: 5% trimmed mean on invoice revenue after removing harmful
    inv_gt = invoice_level(df.loc[~is_harm].copy())
    gt = trimmed_mean(inv_gt["revenue"], 0.05)

    baseline_err = abs(aov_blanket - gt) / gt if gt else 0.0
    context_err = abs(aov_context - gt) / gt if gt else 0.0
    improvement_rate = ((baseline_err - context_err) / baseline_err * 100.0) if baseline_err else 0.0

    baseline_bias = ((aov_blanket - gt) / gt * 100.0) if gt else 0.0
    context_bias = ((aov_context - gt) / gt * 100.0) if gt else 0.0

    tb1 = pd.DataFrame([{
        "AOV_Blanket": aov_blanket,
        "AOV_ContextAware": aov_context,
        "AOV_GroundTruth_Trimmed": gt,
        "Baseline_Error_Magnitude": baseline_err,
        "Context_Error_Magnitude": context_err,
        "Improvement_Rate_%": improvement_rate,
        "Baseline_Bias_%": baseline_bias,
        "Context_Bias_%": context_bias,
    }])

    # Retention
    outlier_rev = df.loc[is_out, "line_total"].sum()
    retained_rev = df.loc[is_out & is_strat, "line_total"].sum()
    retention_pct = (retained_rev / outlier_rev * 100.0) if outlier_rev else 0.0

    tb2_overall = pd.DataFrame([{
        "Total_Outlier_Revenue": float(outlier_rev),
        "Retained_Strategic_Revenue": float(retained_rev),
        "Strategic_Revenue_Retention_Rate_%": float(retention_pct),
    }])

    tb2_seg = (
        df.loc[is_out & is_strat]
        .groupby("customer_type", as_index=False)["line_total"].sum()
        .rename(columns={"line_total": "retained_strategic_revenue"})
    )
    tb2_seg["share_%"] = tb2_seg["retained_strategic_revenue"] / tb2_seg["retained_strategic_revenue"].sum() * 100.0

    tb2_cat = (
        df.loc[is_out & is_strat]
        .groupby("category", as_index=False)["line_total"].sum()
        .rename(columns={"line_total": "retained_strategic_revenue"})
        .sort_values("retained_strategic_revenue", ascending=False)
        .head(15)
        .reset_index(drop=True)
    )

    tb3_top_strat = (
        df.loc[is_out & is_strat, ["invoice_id","date","customer_id","customer_type","product_id","category","quantity","price","product_price","line_total"]]
        .sort_values("line_total", ascending=False)
        .head(30)
        .reset_index(drop=True)
    )

    # Monthly comparison: blanket vs context revenue
    inv_b = invoice_level(df_blanket).assign(month=lambda x: x["date"].dt.to_period("M").dt.to_timestamp())
    inv_c = invoice_level(df_context).assign(month=lambda x: x["date"].dt.to_period("M").dt.to_timestamp())

    monthly_b = inv_b.groupby("month", as_index=False)["revenue"].sum().rename(columns={"revenue": "blanket_revenue"})
    monthly_c = inv_c.groupby("month", as_index=False)["revenue"].sum().rename(columns={"revenue": "context_revenue"})
    tb4_monthly = pd.merge(monthly_b, monthly_c, on="month", how="outer").fillna(0).sort_values("month")

    save_excel_with_sheets(paths.tables_figures / "RQ3_Tb1.xlsx", {"AOV_Comparison": tb1})
    save_excel_with_sheets(paths.tables_figures / "RQ3_Tb2.xlsx", {
        "Overall_Retention": tb2_overall,
        "Retention_by_Segment": tb2_seg,
        "Retention_by_Category_Top15": tb2_cat
    })
    save_excel_with_sheets(paths.tables_figures / "RQ3_Tb3.xlsx", {"Top_Strategic_Outliers": tb3_top_strat})
    save_excel_with_sheets(paths.tables_figures / "RQ3_Tb4.xlsx", {"Monthly_Revenue_Comparison": tb4_monthly})

    # --------------------
    # FIGURES 
    # --------------------

    # Fig1: Top categories (retained strategic revenue)
    fig1, ax1 = plt.subplots()
    ax1.barh(tb2_cat["category"], tb2_cat["retained_strategic_revenue"])
    ax1.set_title("RQ3: Top categories driving retained strategic revenue")
    ax1.set_xlabel("Retained strategic revenue (currency units)")
    ax1.set_ylabel("Category")
    save_pdf(fig1, paths.tables_figures / "RQ3_Fig1.pdf")

    # fig2: Monthly revenue trend (blanket vs context)
    fig2, ax2 = plt.subplots()
    ax2.plot(tb4_monthly["month"], tb4_monthly["blanket_revenue"], label="Blanket removal")
    ax2.plot(tb4_monthly["month"], tb4_monthly["context_revenue"], label="Context-aware (remove harmful)")
    ax2.set_title("RQ3: Monthly revenue trend (blanket vs context-aware)")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Revenue (currency units)")
    ax2.legend()
    save_pdf(fig2, paths.tables_figures / "RQ3_Fig2.pdf")

    # fig3: Scatter diagnostic (quantity vs price)
    fig3, ax3 = plt.subplots()
    sample = df.sample(min(len(df), 20000), random_state=42)
    s_out = flag_stat_outlier(sample)
    s_harm = flag_harmful(sample)
    s_strat = flag_strategic(sample)

    ax3.scatter(sample.loc[~s_out, "quantity"], sample.loc[~s_out, "price"], alpha=0.25, label="Normal")
    ax3.scatter(sample.loc[s_out & ~s_harm & ~s_strat, "quantity"], sample.loc[s_out & ~s_harm & ~s_strat, "price"], alpha=0.5, label="Outlier (benign)")
    ax3.scatter(sample.loc[s_out & s_strat, "quantity"], sample.loc[s_out & s_strat, "price"], alpha=0.6, label="Outlier (strategic)")
    ax3.scatter(sample.loc[s_harm, "quantity"], sample.loc[s_harm, "price"], alpha=0.6, label="Outlier (harmful)")

    ax3.set_title("RQ3: Quantity vs Price diagnostic scatter (outlier categories)")
    ax3.set_xlabel("Quantity (units)")
    ax3.set_ylabel("Unit price (currency units)")
    ax3.legend()
    save_pdf(fig3, paths.tables_figures / "RQ3_Fig3.pdf")

    print("Figures and Tables Generated Successfully for RQ3")


if __name__ == "__main__":
    main()
