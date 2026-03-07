import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, List

def load_glidepaths_parameters(glides_file: str) -> pd.DataFrame:
    """
    Load glidepath parameters from step 01 output.
    
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
    # Load full Excel file
    full_df = pd.read_excel(glides_file, header=0, index_col=0)
    
    # Parameter rows
    param_rows = ["t_start", "t_A", "A", "B", "t_B", "t_end"]
    
    # Extract only parameter rows
    params_df = full_df.loc[
        [r for r in param_rows if r in full_df.index], :
    ].copy()
    
    # Ensure numeric
    params_df = params_df.apply(pd.to_numeric, errors="coerce")
    
    return params_df


def load_glidepaths_cvar_limits(glides_file: str) -> pd.DataFrame:
    """
    Load CVaR limit curves from step 01 output.
    
    Parameters:
    -----------
    glides_file : str
        Path to glidepaths_universe.xlsx
    
    Returns:
    --------
    cvar_limits_df : pd.DataFrame
        DataFrame with monthly CVaR limits (rows=months, columns=curves)
        Shape: (HORIZON_MONTHS x N_CURVES)
    """
    # Load full Excel file
    full_df = pd.read_excel(glides_file, header=0, index_col=0)
    
    # Parameter rows to exclude
    param_rows = ["t_start", "t_A", "A", "B", "t_B", "t_end"]
    
    # Extract monthly CVaR limits (rows starting with "Month_")
    idx_str = full_df.index.astype(str)
    monthly_mask = idx_str.str.startswith("Month_")
    cvar_limits_df = full_df.loc[monthly_mask, :].copy()
    
    # If no Month_ rows found, take all non-parameter rows
    if cvar_limits_df.empty:
        cvar_limits_df = full_df.loc[~idx_str.isin(param_rows), :].copy()
    
    # Reindex months as 1..T
    T = cvar_limits_df.shape[0]
    cvar_limits_df.index = range(1, T + 1)
    cvar_limits_df.index.name = "Month"
    
    # Ensure numeric values
    cvar_limits_df = cvar_limits_df.apply(pd.to_numeric, errors="coerce")
    
    return cvar_limits_df


def get_available_curves(hit_run_dir: str) -> List[str]:
    """
    Get list of curves that have results available in hit_run_results.
    
    Parameters:
    -----------
    hit_run_dir : str
        Path to hit_run_results directory
    
    Returns:
    --------
    curves : List[str]
        List of curve names (e.g., ['curve_0001', 'curve_0002'])
    """
    hit_run_path = Path(hit_run_dir)
    
    if not hit_run_path.exists():
        return []
    
    # Find all files matching pattern curve_XXXX_results.xlsx
    result_files = list(hit_run_path.glob("curve_*_results.xlsx"))
    
    # Extract curve names
    curves = []
    for file in result_files:
        # File name format: curve_0001_results.xlsx
        curve_name = file.stem.replace("_results", "")
        curves.append(curve_name)
    
    return sorted(curves)


def load_trajectory_results(
    hit_run_dir: str,
    curve_name: str
) -> Tuple[pd.DataFrame, Dict]:
    """
    Load trajectory results (returns) for a specific curve.
    
    IMPORTANT: Files are stored as (N_TRAJECTORIES × MONTHS) but are
    TRANSPOSED after loading to (MONTHS × N_TRAJECTORIES) for calculations.
    
    This maintains backward compatibility with all existing analysis code
    while supporting the new storage format that allows millions of trajectories.
    
    Parameters:
    -----------
    hit_run_dir : str
        Path to hit_run_results directory
    curve_name : str
        Name of the curve (e.g., 'curve_0001')
    
    Returns:
    --------
    returns_df : pd.DataFrame
        Monthly returns (rows=months, columns=trajectories)
        Shape: (MONTHS, N_TRAJECTORIES)
    metadata : Dict
        Dictionary with metadata (simulation_method, n_scenarios, etc.)
    """
    file_path = Path(hit_run_dir) / f"{curve_name}_results.xlsx"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Results file not found: {file_path}")
    
    # Load returns sheet (stored as: rows=trajectories, columns=months)
    returns_df = pd.read_excel(file_path, sheet_name="returns", index_col=0)
    
    # TRANSPOSE to maintain expected format for calculations
    # Storage format: (N_TRAJECTORIES × MONTHS)
    # Calculation format: (MONTHS × N_TRAJECTORIES)
    returns_df = returns_df.T
    
    # Extract metadata
    # After transpose: shape[0] = months, shape[1] = trajectories
    metadata = {
        'n_months': returns_df.shape[0],
        'n_trajectories': returns_df.shape[1],
        'simulation_method': 'unknown',
        'n_scenarios': np.nan
    }
    
    # Try to load metadata sheet if it exists (optional)
    try:
        xl_file = pd.ExcelFile(file_path)
        if 'metadata' in xl_file.sheet_names:
            metadata_df = pd.read_excel(file_path, sheet_name='metadata')
            # Extract relevant info from metadata
            # (This would need to be implemented based on actual metadata structure)
    except:
        pass  # Metadata sheet not required
    
    return returns_df, metadata


def validate_trajectory_data(
    returns_df: pd.DataFrame
) -> bool:
    """
    Validate that trajectory data is consistent and valid.
    
    Parameters:
    -----------
    returns_df : pd.DataFrame
        Monthly returns
    
    Returns:
    --------
    valid : bool
        True if data is valid
    """
    # Check for NaN values
    if returns_df.isna().any().any():
        print("   Warning: NaN values found in returns")
        return False
    
    # Check for reasonable values
    if (returns_df < -1).any().any() or (returns_df > 1).any().any():
        print("   Warning: Extreme return values detected")
        return False
    
    return True