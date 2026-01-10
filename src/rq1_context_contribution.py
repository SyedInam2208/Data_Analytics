from __future__ import annotations

import pandas as pd

from analytics_utils import ProjectPaths
from plotting_utils import save_excel_with_sheets

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def main():
    paths = ProjectPaths.from_src_file(__file__)
    data_path = paths.root / "data" / "processed" / "rq1_model_dataset.csv"

    df = pd.read_csv(data_path)
    df = df[df["outlier_class"].isin(["Harmful", "Benign", "Strategic"])].copy()

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

    X = df[feature_cols]
    y = df[target_col]

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

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf.fit(X_train, y_train)

    # Extract feature names
    ohe = clf.named_steps["preprocess"].named_transformers_["cat"]
    cat_feature_names = list(ohe.get_feature_names_out(cat_cols))
    full_feature_names = cat_feature_names + num_cols

    importances = clf.named_steps["model"].feature_importances_
    imp_df = pd.DataFrame({"feature": full_feature_names, "importance": importances})

    # Define contextual vs numeric buckets
    contextual_prefixes = ("customer_type_", "dominant_category_")
    contextual_mask = imp_df["feature"].str.startswith(contextual_prefixes)

    contextual_sum = float(imp_df.loc[contextual_mask, "importance"].sum())
    total_sum = float(imp_df["importance"].sum())
    contextual_ratio = (contextual_sum / total_sum * 100.0) if total_sum else 0.0

    summary = pd.DataFrame([{
        "Contextual_Importance_Sum": contextual_sum,
        "Total_Importance_Sum": total_sum,
        "Contextual_Contribution_%": contextual_ratio
    }])

    breakdown = (
        imp_df.assign(bucket=imp_df["feature"].apply(lambda f: "Contextual" if f.startswith(contextual_prefixes) else "Numeric/Temporal"))
        .groupby("bucket", as_index=False)["importance"].sum()
        .sort_values("importance", ascending=False)
    )

    save_excel_with_sheets(paths.tables_figures / "RQ1_Tb3.xlsx", {
        "Contextual_Contribution": summary,
        "Bucket_Breakdown": breakdown,
        "All_Features": imp_df.sort_values("importance", ascending=False),
    })

    print("[RQ1] Saved: tables_figures/RQ1_Tb3.xlsx")


if __name__ == "__main__":
    main()
