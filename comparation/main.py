import os
import pandas as pd

from routes import (
    BASE_DIR, LOOP_FILE, GLIDES_FILE,
    OUT_DIR, OUT_FILE, SUMMARY_SHEETNAME
)
from loaders import load_portfolios, load_glidepaths
from logic import compare_glides_vs_portfolios

def main() -> None:
    """
    Workflow:
    1) Load portfolios (T x P) and glidepaths (params, T x G).
    2) Compare each curve against all portfolios (strict by month).
    3) Merge curve params into the summary.
    4) Sort results and export to Excel.
    """
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1) Load data
    ports_df = load_portfolios(LOOP_FILE)          # (T x P)
    params_df, glides_df = load_glidepaths(GLIDES_FILE)  # params + (T x G)

    # 2) Compare curves vs portfolios
    summary = compare_glides_vs_portfolios(glides_df=glides_df, ports_df=ports_df)

    # 3) Attach parameters to each curve
    params_t = params_df.T.reset_index().rename(columns={"index": "curve_id"})
    for col in ["t_start", "t_A", "A", "B", "t_B", "t_end"]:
        if col in params_t.columns:
            params_t[col] = pd.to_numeric(params_t[col], errors="coerce")

    result = params_t.merge(summary, on="curve_id", how="right")

    # 4) Sort results (same idea as the original script)
    # Example: sort by B (desc), then by pct_ok (desc), then by A (desc)
    result = result.sort_values(
        by=["pct_ok", "A", "t_A"],
        ascending=[False, False, False]
    )

    # Export
    result.to_excel(OUT_FILE, sheet_name=SUMMARY_SHEETNAME, index=False)

    # Logs
    print(f"OK Summary saved to: {OUT_FILE}")
    print(f"- Months compared: {glides_df.shape[0]}")
    print(f"- Portfolios: {ports_df.shape[1]}")
    print(f"- Curves: {glides_df.shape[1]}")

if __name__ == "__main__":
    main()
