import os
import os.path as op
import pandas as pd

# Base folder = repository root (one level above this package)
BASE_DIR = op.dirname(op.dirname(op.abspath(__file__)))

def input_returns_path() -> str:
    """
    Path to the CSV with historical returns.
    Expects a file named 'returns.csv' at the repo root.
    """
    return op.join(BASE_DIR, "returns.csv")

def output_dir() -> str:
    """
    Folder where result files will be stored.
    """
    return op.join(BASE_DIR, "outputs")

def output_file() -> str:
    """
    Full path of the Excel file with results.
    """
    return op.join(output_dir(), "Loop_drunken_portfolio_results.xlsx")

def export_results(out_file: str, cvar_df: pd.DataFrame) -> None:
    """
    Write the DataFrame to an Excel file.
    Saves to sheet 'cvar_by_portfolio' without the index.
    """
    with pd.ExcelWriter(out_file, engine="xlsxwriter") as writer:
        cvar_df.to_excel(writer, sheet_name="cvar_by_portfolio", index=False)
