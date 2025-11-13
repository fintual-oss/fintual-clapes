import numpy as np
import pandas as pd

from config import T_START_YEARS, T_END_YEARS, MONTHS
from param_grid import generate_param_grid
from cvar_piecewise import cvar_piecewise_months

def build_universe_single_sheet(t_start_y: int = T_START_YEARS, t_B_year: int | None = None) -> pd.DataFrame:
    """
    Build a DataFrame with all CVaR glidepaths.
    Rows:
      [t_start, t_A, A, B, t_B, t_end] + 360 monthly values (Month_1..Month_360)
    Notes:
      - t_start, t_A, t_B, t_end are expressed in years.
      - Monthly values are computed internally using months.
    """
    grid = generate_param_grid(t_B_year=t_B_year) if t_B_year is not None else generate_param_grid()

    # Relative monthly indices (1..MONTHS) and absolute ages in months
    month_idx = np.arange(1, MONTHS + 1, dtype=int)
    age_months_series = (t_start_y * 12) + month_idx

    all_cols = {}
    for i, (t_A_y, t_A_m, t_B_y, t_B_m, A, B) in enumerate(grid):
        col_name = f"curve_{i+1:04d}"
        cvar_vals = [cvar_piecewise_months(age_m, t_A_m, t_B_m, A, B) for age_m in age_months_series]
        all_cols[col_name] = [t_start_y, t_A_y, A, B, t_B_y, T_END_YEARS] + cvar_vals

    sheet_df = pd.DataFrame(all_cols)
    row_labels = ["t_start", "t_A", "A", "B", "t_B", "t_end"] + [f"Month_{i}" for i in month_idx]
    sheet_df.index = row_labels
    return sheet_df
