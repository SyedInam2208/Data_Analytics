from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_excel_with_sheets(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    ensure_dir(path.parent)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=name[:31])  # Excel sheet name limit


def save_pdf(fig, path: Path) -> None:
    """
    Save figure in a PDF-safe way:
    - uses tight_layout
    - reserves a bit of top margin for long titles
    """
    ensure_dir(path.parent)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def fmt_currency_axis(ax, label: str = "Value (€)"):
    ax.set_ylabel(label)
    ax.ticklabel_format(style='plain', axis='y')  # no scientific notation
