import pandas as pd
import numpy as np
from routes import LOOP_SHEET_NAME

def load_portfolios(loop_file: str) -> pd.DataFrame:
    """
    Load CVaR by portfolio (wide -> T x P matrix).
    - Expects sheet 'cvar_by_portfolio' with:
      'Portfolio', and columns 'm001'..'m360'.
    - Returns a DataFrame (T x P) with index = 1..T (months),
      and columns = portfolio names.
    """
    df = pd.read_excel(loop_file, sheet_name=LOOP_SHEET_NAME)

    if "Portfolio" not in df.columns:
        raise ValueError("Expected 'Portfolio' column in 'cvar_by_portfolio' sheet.")

    # Detect month columns m001..m360 and sort them
    month_cols = [c for c in df.columns if isinstance(c, str) and c.startswith("m")]
    if not month_cols:
        raise ValueError("No month columns found (e.g., m001..).")
    month_cols = sorted(month_cols)

    # Keep only Portfolio + month columns
    df2 = df[["Portfolio"] + month_cols].copy()

    # Ensure numeric month columns
    df2[month_cols] = df2[month_cols].apply(pd.to_numeric, errors="coerce")

    # Transpose to get T x P (rows = months, cols = portfolios)
    ports_tp = df2.set_index("Portfolio")[month_cols].T

    # Reindex months as 1..T
    T = ports_tp.shape[0]
    ports_tp.index = np.arange(1, T + 1, dtype=int)

    return ports_tp  # (T x P)


def load_glidepaths(glides_file: str):
    """
    Load CVaR glidepaths (limits) and parameters.
    Expected structure (rows and columns):
      - Rows include: t_start, t_A, A, B, t_B, t_end, Month_1..Month_T
      - Columns: curve_0001..curve_G
    Returns:
      params_df: DataFrame with parameter rows
      glides_df: DataFrame (T x G) with monthly limits (index 1..T)
    """
    full = pd.read_excel(glides_file, header=0, index_col=0)

    # Parameter rows
    param_rows = ["t_start", "t_A", "A", "B", "t_B", "t_end"]
    idx_str = full.index.astype(str)

    # Minimal validation
    min_required = ["t_start", "t_A", "A", "B"]
    if not all(lbl in idx_str.values for lbl in min_required):
        raise ValueError("Missing parameter rows: need ['t_start','t_A','A','B'].")

    # Split parameters and monthly rows
    params_df = full.loc[[r for r in param_rows if r in full.index], :].copy()
    monthly_mask = idx_str.str.startswith("Month_")
    glides_df = full.loc[monthly_mask, :].copy()

    # Fallback: if Month_ rows are not labeled, take non-parameter rows
    if glides_df.empty:
        glides_df = full.loc[~idx_str.isin(param_rows), :].copy()

    # Reindex months to 1..T and ensure numeric
    T = glides_df.shape[0]
    glides_df.index = range(1, T + 1)
    glides_df = glides_df.apply(pd.to_numeric, errors="coerce")

    return params_df, glides_df
