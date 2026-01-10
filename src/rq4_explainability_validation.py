from __future__ import annotations

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

from analytics_utils import ProjectPaths
from plotting_utils import save_excel_with_sheets


def iqr_bounds(series: pd.Series, k: float = 1.5) -> tuple[float, float]:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    return float(q1 - k * iqr), float(q3 + k * iqr)


def build_model_and_features(df: pd.DataFrame):
    feature_cols = [
        "customer_type",
        "dominant_category",
        "month",
        "day_of_week",
        "is_weekend",
        "is_peak_season",
        "is_off_season",
        "invoice_revenue",
        "total_qty",
        "avg_price",
        "n_items",
    ]
    target_col = "outlier_class"

    X = df[feature_cols].copy()
    y = df[target_col].copy()

    cat_cols = ["customer_type", "dominant_category"]
    num_cols = [c for c in feature_cols if c not in cat_cols]

    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", "passthrough", num_cols),
        ]
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
        min_samples_leaf=2
    )

    clf = Pipeline(steps=[("preprocess", pre), ("model", model)])
    return clf, X, y, cat_cols, num_cols


def apply_business_rules(df: pd.DataFrame) -> pd.Series:
    """
    Implements the business rules from RQ4 KPI 4-2 (adapted to your dataset columns).
    Rules output a suggested class if rule applies, else None.

    Rules in your doc include:
      - wholesaler AND quantity high -> Strategic
      - price very low OR quantity extremely high -> Harmful
      - seasonal + peak season -> Strategic (we approximate via is_peak_season)
    """
    # thresholds
    _, qty_hi = iqr_bounds(df["total_qty"], k=1.5)
    _, rev_hi = iqr_bounds(df["invoice_revenue"], k=1.5)

    rule_pred = pd.Series([None] * len(df), index=df.index, dtype="object")

    # Harmful rules (high priority)
    harmful_mask = (df["avg_price"] <= 0) | (df["avg_price"] < 0.1) | (df["total_qty"] > 10000) | (df["total_qty"] <= 0)
    rule_pred.loc[harmful_mask] = "Harmful"

    # Strategic rules
    strategic_mask = (
        ((df["customer_type"].str.lower() == "wholesaler") & (df["total_qty"] > qty_hi)) |
        ((df["is_peak_season"] == True) & (df["invoice_revenue"] > rev_hi))
    )
    # only set where not already harmful
    rule_pred.loc[strategic_mask & rule_pred.isna()] = "Strategic"

    return rule_pred


def business_rule_alignment_table(df_test: pd.DataFrame, model_preds: pd.Series) -> pd.DataFrame:
    rule_preds = apply_business_rules(df_test)

    applicable = rule_preds.notna()
    total_applicable = int(applicable.sum())

    if total_applicable == 0:
        return pd.DataFrame([{
            "Total_Rule_Applicable": 0,
            "Aligned_Cases": 0,
            "Alignment_Rate_%": 0.0
        }])

    aligned = (model_preds[applicable] == rule_preds[applicable]).sum()
    alignment_rate = aligned / total_applicable * 100.0

    # Breakdown by rule class
    breakdown = (
        pd.DataFrame({
            "rule_class": rule_preds[applicable],
            "model_pred": model_preds[applicable]
        })
        .groupby(["rule_class", "model_pred"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )

    summary = pd.DataFrame([{
        "Total_Rule_Applicable": total_applicable,
        "Aligned_Cases": int(aligned),
        "Alignment_Rate_%": float(alignment_rate)
    }])

    return summary, breakdown


def topk_consistency(top_lists: list[list[str]], k: int = 3) -> float:
    """
    Simple consistency proxy:
    For each run, take top-k features; compute average Jaccard similarity between runs.
    """
    sets = [set(lst[:k]) for lst in top_lists]
    sims = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            inter = len(sets[i] & sets[j])
            union = len(sets[i] | sets[j])
            sims.append(inter / union if union else 0.0)
    return float(np.mean(sims)) if sims else 0.0


def main():
    paths = ProjectPaths.from_src_file(__file__)
    data_path = paths.root / "data" / "processed" / "rq1_model_dataset.csv"

    df = pd.read_csv(data_path)
    df = df[df["outlier_class"].isin(["Harmful", "Benign", "Strategic"])].copy()

    clf, X, y, cat_cols, num_cols = build_model_and_features(df)

    # Keep a stable test set so we can assess stability across retrains
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # -------------------------
    # RQ4 Tb1: Business rule alignment
    # -------------------------
    clf.fit(X_train, y_train)
    preds = pd.Series(clf.predict(X_test), index=X_test.index)

    # Reconstruct df_test at invoice-level feature space
    df_test = X_test.copy()
    df_test["outlier_class_true"] = y_test.values

    summary, breakdown = business_rule_alignment_table(df_test, preds)

    # -------------------------
    # RQ4 Tb2/Tb3: Stability via permutation importance + prediction stability
    # -------------------------
    top_features_each_run = []
    perm_tables = []
    pred_matrix = pd.DataFrame(index=X_test.index)

    # Build transformed feature names once (after fit, OHE knows categories)
    ohe = clf.named_steps["preprocess"].named_transformers_["cat"]
    cat_feature_names = list(ohe.get_feature_names_out(cat_cols))
    full_feature_names = cat_feature_names + num_cols

    for run in range(1, 6):
        # Retrain with different random_state to simulate stability checks
        model = RandomForestClassifier(
            n_estimators=300,
            random_state=40 + run,
            class_weight="balanced",
            n_jobs=-1,
            min_samples_leaf=2
        )

        local_clf = Pipeline(steps=[("preprocess", clf.named_steps["preprocess"]), ("model", model)])
        local_clf.fit(X_train, y_train)

        # Predictions
        run_preds = local_clf.predict(X_test)
        pred_matrix[f"run_{run}"] = run_preds

        # Permutation importance on test set (lightweight explainability proxy)
        X_test_trans = local_clf.named_steps["preprocess"].transform(X_test)
        pi = permutation_importance(
            local_clf.named_steps["model"],
            X_test_trans,
            y_test,
            n_repeats=5,
            random_state=100 + run,
            n_jobs=-1
        )
        imp = pd.DataFrame({
            "feature": full_feature_names,
            "importance_mean": pi.importances_mean,
            "importance_std": pi.importances_std,
            "run": run
        }).sort_values("importance_mean", ascending=False).reset_index(drop=True)

        perm_tables.append(imp)
        top_features_each_run.append(list(imp["feature"].head(10)))

    # Consistency score based on top-3 overlap across runs
    consistency = topk_consistency(top_features_each_run, k=3)
    tb2_summary = pd.DataFrame([{
        "Top3_Feature_Consistency_Jaccard": consistency,
        "Interpretation": "Higher = more stable explanations across retrains"
    }])

    # Detailed top features per run
    tb2_top = []
    for run, feats in enumerate(top_features_each_run, start=1):
        for rank, f in enumerate(feats[:10], start=1):
            tb2_top.append({"run": run, "rank": rank, "feature": f})
    tb2_top = pd.DataFrame(tb2_top)

    # Prediction stability: % of test instances whose predicted class is identical across all runs
    same_all = pred_matrix.nunique(axis=1) == 1
    stability_rate = float(same_all.mean() * 100.0)
    tb3 = pd.DataFrame([{
        "Test_instances": int(len(pred_matrix)),
        "Stable_predictions_count": int(same_all.sum()),
        "Prediction_Stability_%": stability_rate
    }])

    # Save outputs
    save_excel_with_sheets(paths.tables_figures / "RQ4_Tb1.xlsx", {
        "Rule_Alignment_Summary": summary,
        "Rule_Alignment_Breakdown": breakdown
    })

    save_excel_with_sheets(paths.tables_figures / "RQ4_Tb2.xlsx", {
        "Consistency_Summary": tb2_summary,
        "Top_Features_Per_Run": tb2_top
    })

    save_excel_with_sheets(paths.tables_figures / "RQ4_Tb3.xlsx", {
        "Prediction_Stability": tb3
    })

    print("[RQ4] Saved:")
    print(" - tables_figures/RQ4_Tb1.xlsx (business rule alignment)")
    print(" - tables_figures/RQ4_Tb2.xlsx (feature consistency across retrains)")
    print(" - tables_figures/RQ4_Tb3.xlsx (prediction stability across retrains)")


if __name__ == "__main__":
    main()
