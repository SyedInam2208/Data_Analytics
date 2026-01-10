from __future__ import annotations

import sys
from pathlib import Path
import subprocess

from cleaning import clean_and_write_processed
from loading import load_processed_data


def run_script(script_path: Path, title: str) -> None:
    """
    Runs a python script as a subprocess using the current interpreter.
    Fails fast and prints stdout/stderr if anything breaks (professor-friendly).
    """
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)
    print(f"Running: {script_path.name}")

    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)

    if res.returncode != 0:
        print("\n--- STDOUT ---")
        print(res.stdout)
        print("\n--- STDERR ---")
        print(res.stderr)
        raise RuntimeError(f"FAILED: {script_path.name}")
    else:
        if res.stdout.strip():
            print(res.stdout.strip())
        if res.stderr.strip():
            print("\n[Warnings/Notes]")
            print(res.stderr.strip())


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    src_dir = project_root / "src"

    raw_dir = project_root / "data" / "RAW"
    processed_dir = project_root / "data" / "processed"
    schema_sql = project_root / "db" / "create_tables.sql"

    tables_figures_dir = project_root / "tables_figures"
    tables_figures_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("END-TO-END PIPELINE: ETL + ALL RQs")
    print("=" * 80)
    print(f"Project root:        {project_root}")
    print(f"RAW dir:             {raw_dir}")
    print(f"Processed dir:       {processed_dir}")
    print(f"Schema SQL:          {schema_sql}")
    print(f"Tables/Figures dir:  {tables_figures_dir}")

    # -------------------------
    # PART A: ETL (RAW -> processed -> PostgreSQL)
    # -------------------------
    print("\n" + "=" * 80)
    print("PART A: ETL (Cleaning + Loading)")
    print("=" * 80)

    processed_paths = clean_and_write_processed(raw_dir, processed_dir)
    load_processed_data(processed_paths, schema_sql)

    print("\nETL completed successfully.")
    print("Database is refreshed and ready for analytics.")

    # -------------------------
    # PART B: Run RQ scripts (in dependency order)
    # -------------------------
    print("\n" + "=" * 80)
    print("PART B: RUNNING ALL RESEARCH QUESTIONS")
    print("=" * 80)

    rq_scripts = [
        ("RQ2: KPI distortion + data quality analytics", src_dir / "rq2_kpi_distortion.py"),
        ("RQ3: Strategic value preservation analytics", src_dir / "rq3_strategic_value.py"),
        ("RQ1: Prepare modeling dataset", src_dir / "rq1_prepare_dataset.py"),
        ("RQ1: Train + evaluate model", src_dir / "rq1_model_train_eval.py"),
        ("RQ1: Contextual contribution", src_dir / "rq1_context_contribution.py"),
        ("RQ4: Explainability validation", src_dir / "rq4_explainability_validation.py"),
    ]

    for title, path in rq_scripts:
        if not path.exists():
            raise FileNotFoundError(f"Missing required script: {path}")
        run_script(path, title)

    print("\n" + "=" * 80)
    print("ALL DONE")
    print("=" * 80)
    print("Outputs saved in: tables_figures/")
    print("Processed data saved in: data/processed/")
    print("Database: refreshed in PostgreSQL (OutlierAnalytics).")


if __name__ == "__main__":
    main()
