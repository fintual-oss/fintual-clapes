import os.path as op

# Base folder = repository root (two levels above this package)
BASE_DIR = op.dirname(op.dirname(op.abspath(__file__)))

def input_returns_path() -> str:
    """
    Path to the CSV with historical returns.
    Expects a file named 'returns.csv' at the repo root.
    """
    return op.join(BASE_DIR, "returns.csv")

def input_glidepaths_path() -> str:
    """
    Path to the Excel file with CVaR glidepaths.
    Expects 'glidepaths_universe.xlsx' in the outputs folder.
    """
    return op.join(BASE_DIR, "outputs", "glidepaths_universe.xlsx")

def output_weights_dir() -> str:
    """
    Directory where HDF5 weight matrices are stored.
    
    Returns:
    --------
    str
        Path: outputs/hit_and_run_matrices/
    """
    return op.join(BASE_DIR, "outputs", "hit_and_run_matrices")

def output_weights_file(curve_name: str) -> str:
    """
    Full path for a curve's HDF5 weight matrix file.
    
    Parameters:
    -----------
    curve_name : str
        Name of the curve (e.g., 'curve_0001')
    
    Returns:
    --------
    str
        Full path to the HDF5 file:
        outputs/hit_and_run_matrices/curve_0001.h5
    
    HDF5 contents:
    --------------
    Dataset 'weights' → shape (HORIZON_MONTHS, N_PORTFOLIOS, N_ASSETS)
        - axis 0: months (e.g., 480)
        - axis 1: portfolios generated per month (e.g., 10,000)
        - axis 2: assets (e.g., 9)
    Attributes:
        - curve_name: str
        - horizon_months: int
        - n_portfolios: int
        - n_assets: int
        - returns_seed: int
        - hit_run_seed: int
        - simulation_method: str
        - alpha_cvar: float
        - asset_names: str (comma-separated)
    """
    filename = f"{curve_name}.h5"
    return op.join(output_weights_dir(), filename)
