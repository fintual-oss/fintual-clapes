import numpy as np
import pandas as pd
import h5py
from pathlib import Path
from typing import List, Tuple, Dict


def load_glidepaths_parameters(glides_file: str) -> pd.DataFrame:
    """
    Load glidepath parameters from Module 01 output.

    Parameters:
    -----------
    glides_file : str
        Path to glidepaths_universe.xlsx

    Returns:
    --------
    params_df : pd.DataFrame
        DataFrame with parameter rows (t_start, t_A, A, B, t_B, t_end)
        and curve columns (curve_0001, curve_0002, etc.)
    """
    full_df    = pd.read_excel(glides_file, header=0, index_col=0)
    param_rows = ["t_start", "t_A", "A", "B", "t_B", "t_end"]
    params_df  = full_df.loc[
        [r for r in param_rows if r in full_df.index], :
    ].copy()
    params_df  = params_df.apply(pd.to_numeric, errors="coerce")
    return params_df


def load_glidepaths_cvar_limits(glides_file: str) -> pd.DataFrame:
    """
    Load monthly CVaR limit curves from Module 01 output.

    Parameters:
    -----------
    glides_file : str
        Path to glidepaths_universe.xlsx

    Returns:
    --------
    cvar_limits_df : pd.DataFrame
        Monthly CVaR limits — shape (HORIZON_MONTHS, N_CURVES)
    """
    full_df    = pd.read_excel(glides_file, header=0, index_col=0)
    param_rows = ["t_start", "t_A", "A", "B", "t_B", "t_end"]
    idx_str    = full_df.index.astype(str)

    monthly_mask   = idx_str.str.startswith("Month_")
    cvar_limits_df = full_df.loc[monthly_mask, :].copy()

    if cvar_limits_df.empty:
        cvar_limits_df = full_df.loc[~idx_str.isin(param_rows), :].copy()

    T = cvar_limits_df.shape[0]
    cvar_limits_df.index      = range(1, T + 1)
    cvar_limits_df.index.name = "Month"
    cvar_limits_df = cvar_limits_df.apply(pd.to_numeric, errors="coerce")
    return cvar_limits_df


def get_available_curves(results_dir: str) -> List[str]:
    """
    Return sorted list of curve names that have an HDF5 results file.

    Parameters:
    -----------
    results_dir : str
        Path to outputs/scenario_results/

    Returns:
    --------
    List[str]
        e.g., ['curve_0001', 'curve_0002', ...]
    """
    p = Path(results_dir)
    if not p.exists():
        return []
    return sorted(f.stem for f in p.glob("curve_*.h5"))


def load_annualized_returns(
    h5_path: str,
) -> Tuple[np.ndarray, int, Dict]:
    """
    Load the full annualized returns matrix from a Module 03 HDF5 file.

    The matrix is loaded as float32 and kept as-is (no flatten, no copy).
    All statistics in Module 04 operate directly on this 2D matrix,
    which is equivalent to operating on the flattened vector but avoids
    the memory overhead of creating a copy.

    Parameters:
    -----------
    h5_path : str
        Path to curve HDF5 file from Module 03.

    Returns:
    --------
    arr : np.ndarray, shape (N_SEEDS, N_PORTFOLIOS)
        Full annualized returns matrix. dtype float32 to minimize
        memory usage — numpy statistics functions handle this correctly.
    horizon_months : int
        Number of months in the horizon (from HDF5 metadata).
    attrs : dict
        Full metadata attributes from the HDF5 dataset.
    """
    try:
        with h5py.File(h5_path, "r") as f:
            # Keep as float32 to halve memory usage vs float64.
            # For a (1000 x 10000) matrix:
            #   float32 -> ~40 MB
            #   float64 -> ~80 MB
            arr   = f["annualized_returns"][:]
            attrs = dict(f["annualized_returns"].attrs)
    except OSError as e:
        raise OSError(
            f"Could not open HDF5 file (possibly corrupted or truncated): "
            f"{h5_path}\n  Original error: {e}"
        )

    horizon_months = int(attrs.get("horizon_months", 480))
    # Return as float32 — no cast to float64 needed since we operate
    # over the full matrix and numpy promotes precision automatically
    return arr, horizon_months, attrs
