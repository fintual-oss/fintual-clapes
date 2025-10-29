import os
import pandas as pd

from .config import T_B_YEAR, OUTPUT_XLSX
from .io_paths import output_dir, output_file
from .universe import build_universe_single_sheet

def main() -> None:
    """
    Build the full universe of CVaR glidepaths and export to Excel.
    Prints the number of curves generated and the output path.
    """
    # Build the DataFrame with all curves
    sheet_df = build_universe_single_sheet(t_B_year=T_B_YEAR)

    # Report in console
    num_curves = sheet_df.shape[1]
    print(f"Total number of CVaR glidepaths generated: {num_curves:,}")

    # Ensure output folder exists and export
    os.makedirs(output_dir(), exist_ok=True)
    out_xlsx = output_file(OUTPUT_XLSX)
    sheet_df.to_excel(out_xlsx)

    print(f"File saved at: {out_xlsx}")

if __name__ == "__main__":
    main()
