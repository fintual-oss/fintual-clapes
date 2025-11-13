import numpy as np
import pandas as pd

def compare_glides_vs_portfolios(glides_df: pd.DataFrame, ports_df: pd.DataFrame) -> pd.DataFrame:
    """
    Strict comparison for each curve:
      ports_df[t, p] <= glides_df[t, g]   for all months t
    Returns a summary DataFrame with:
      ['curve_id','portfolios_ok','total_portfolios','pct_ok']
    """
    if glides_df.shape[0] != ports_df.shape[0]:
        raise ValueError(
            f"Row mismatch: glidepaths={glides_df.shape[0]} vs portfolios={ports_df.shape[0]}"
        )

    T = glides_df.shape[0]      # months
    P = ports_df.shape[1]       # portfolios
    curves = glides_df.columns  # curve ids

    ports_matrix = ports_df.to_numpy()  # (T, P)
    summary_rows = []

    for g in curves:
        gp = glides_df[g].to_numpy()          # (T,)
        compliant_all = (ports_matrix <= gp[:, None]).all(axis=0)
        n_ok = int(compliant_all.sum())
        pct_ok = (n_ok / P) if P > 0 else np.nan
        summary_rows.append((g, n_ok, P, pct_ok))

    return pd.DataFrame(summary_rows, columns=["curve_id", "portfolios_ok", "total_portfolios", "pct_ok"])
