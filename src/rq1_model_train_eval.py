from __future__ import annotations

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier

from analytics_utils import ProjectPaths
from plotting_utils import save_excel_with_sheets


def main():
    paths = ProjectPaths.from_src_file(__file__)
    data_path = paths.root / "data" / "processed" / "rq1_model_dataset.csv"

    df = pd.read_csv(data_path)

    # Keep ONLY the three outlier classes for RQ1
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
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)

    # Metrics table
    report = classification_report(y_test, preds, output_dict=True, zero_division=0)
    tb1 = (
        pd.DataFrame(report)
        .transpose()
        .reset_index()
        .rename(columns={"index": "label"})
    )

    # Confusion matrix table (useful for report)
    labels = ["Harmful", "Benign", "Strategic"]
    cm = confusion_matrix(y_test, preds, labels=labels)
    tb1_cm = pd.DataFrame(cm, index=[f"true_{l}" for l in labels], columns=[f"pred_{l}" for l in labels]).reset_index()

    # Feature importance table (global)
    ohe = clf.named_steps["preprocess"].named_transformers_["cat"]
    cat_feature_names = list(ohe.get_feature_names_out(cat_cols))
    full_feature_names = cat_feature_names + num_cols

    importances = clf.named_steps["model"].feature_importances_
    tb2 = (
        pd.DataFrame({"feature": full_feature_names, "importance": importances})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    # Save tables
    save_excel_with_sheets(paths.tables_figures / "RQ1_Tb1.xlsx", {
        "Classification_Report": tb1,
        "Confusion_Matrix": tb1_cm,
    })
    save_excel_with_sheets(paths.tables_figures / "RQ1_Tb2.xlsx", {
        "Feature_Importance": tb2
    })

    print("[RQ1] Saved:")
    print(" - tables_figures/RQ1_Tb1.xlsx (metrics + confusion matrix)")
    print(" - tables_figures/RQ1_Tb2.xlsx (feature importance)")
    print("\nClass distribution used:")
    print(y.value_counts())


if __name__ == "__main__":
    main()
