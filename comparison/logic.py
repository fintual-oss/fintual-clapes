import numpy as np
import pandas as pd

def compare_glides_vs_portfolios(glides_df: pd.DataFrame, ports_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare each glidepath (columns in glides_df) against all portfolios
    (columns in ports_df) month by month.

    For each glidepath we compute:
      - portfolios_ok: number of portfolios that never exceed the limit
      - total_portfolios: total number of portfolios
      - pct_ok: portfolios_ok / total_portfolios

    Also compute:
      - pct_viol_1m ... pct_viol_10m: percentage of portfolios that violate
        the limit in exactly k months
      - pct_viol_gt10m: percentage of portfolios that violate the limit
        in more than 10 months

    All groups are mutually exclusive (no double counting).
    """

    # Both DataFrames must have the same number of months (rows)
    if glides_df.shape[0] != ports_df.shape[0]:
        raise ValueError(
            f"Row mismatch: glidepaths={glides_df.shape[0]} vs portfolios={ports_df.shape[0]}"
        )

    T = glides_df.shape[0]     # number of months
    P = ports_df.shape[1]      # number of portfolios
    curves = glides_df.columns # glidepath IDs

    # Convert portfolios data to a NumPy array for faster calculations
    ports_matrix = ports_df.to_numpy()  # shape (T, P)

    summary_rows: list[tuple] = []

    for g in curves:
        # The monthly CVaR limit for this glidepath
        gp = glides_df[g].to_numpy()  # shape (T,)

        # violations[t, p] = True if portfolio p exceeds the limit in month t
        violations = ports_matrix > gp[:, None]  # shape (T, P)

        # Number of months each portfolio violates the limit
        viol_counts = violations.sum(axis=0)  # shape (P,)

        # Portfolios with zero violations
        n_ok = int((viol_counts == 0).sum())
        pct_ok = n_ok / P if P > 0 else np.nan

        # Percentages for portfolios violating exactly k months (k = 1..10)
        pct_k_list = []
        for k in range(1, 11):
            n_k = int((viol_counts == k).sum())
            pct_k = n_k / P if P > 0 else np.nan
            pct_k_list.append(pct_k)

        # Category: portfolios that violate more than 10 months
        n_gt10 = int((viol_counts > 10).sum())
        pct_gt10 = n_gt10 / P if P > 0 else np.nan

        # One row for this glidepath
        row = (g, n_ok, P, pct_ok, *pct_k_list, pct_gt10)
        summary_rows.append(row)

    # Column names for the violation percentages
    viol_cols = [f"pct_viol_{k}m" for k in range(1, 11)] + ["pct_viol_gt10m"]

    # Final column order
    columns = ["curve_id", "portfolios_ok", "total_portfolios", "pct_ok"] + viol_cols

    return pd.DataFrame(summary_rows, columns=columns)
