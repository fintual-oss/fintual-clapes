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
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Load trajectory results (returns and CVaR) for a specific curve.
    
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
    cvar_df : pd.DataFrame
        Monthly CVaR (rows=months, columns=trajectories)
    metadata : Dict
        Dictionary with metadata (simulation_method, n_scenarios, etc.)
    """
    file_path = Path(hit_run_dir) / f"{curve_name}_results.xlsx"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Results file not found: {file_path}")
    
    # Load returns sheet
    returns_df = pd.read_excel(file_path, sheet_name="returns", index_col=0)
    
    # Load CVaR sheet
    cvar_df = pd.read_excel(file_path, sheet_name="cvar", index_col=0)
    
    # Verify dimensions match
    if returns_df.shape != cvar_df.shape:
        raise ValueError(
            f"Shape mismatch: returns {returns_df.shape} vs cvar {cvar_df.shape}"
        )
    
    # Extract metadata (basic information)
    metadata = {
        'n_months': returns_df.shape[0],
        'n_trajectories': returns_df.shape[1],
        'simulation_method': 'unknown',  # Could be extracted from filename or metadata sheet
        'n_scenarios': np.nan  # Could be extracted from metadata sheet if available
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
    
    return returns_df, cvar_df, metadata


def validate_trajectory_data(
    returns_df: pd.DataFrame,
    cvar_df: pd.DataFrame
) -> bool:
    """
    Validate that trajectory data is consistent and valid.
    
    Parameters:
    -----------
    returns_df : pd.DataFrame
        Monthly returns
    cvar_df : pd.DataFrame
        Monthly CVaR
    
    Returns:
    --------
    valid : bool
        True if data is valid
    """
    # Check for NaN values
    if returns_df.isna().any().any():
        print(" Warning: NaN values found in returns")
        return False
    
    if cvar_df.isna().any().any():
        print(" Warning: NaN values found in CVaR")
        return False
    
    # Check shapes match
    if returns_df.shape != cvar_df.shape:
        print(" Warning: Shape mismatch between returns and CVaR")
        return False
    
    # Check for reasonable values
    if (returns_df < -1).any().any() or (returns_df > 1).any().any():
        print(" Warning: Extreme return values detected")
        return False
    
    if (cvar_df < 0).any().any():
        print(" Warning: Negative CVaR values detected")
        return False
    
    return True