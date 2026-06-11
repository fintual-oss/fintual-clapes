import os.path as op

# Base folder = repository root (two levels above this package)
BASE_DIR = op.dirname(op.dirname(op.abspath(__file__)))

def input_returns_path() -> str:
    """
    Path to the CSV with historical returns.
    Expects 'returns.csv' at the repo root.
    """
    return op.join(BASE_DIR, "returns.csv")

def input_glidepaths_path() -> str:
    """
    Path to the Excel file with CVaR glidepaths from step 01.
    Expects 'glidepaths_universe.xlsx' in the outputs folder.
    """
    return op.join(BASE_DIR, "outputs", "glidepaths_universe.xlsx")

def input_weights_dir() -> str:
    """
    Directory with HDF5 weight matrices from Module 02.
    """
    return op.join(BASE_DIR, "outputs", "hit_and_run_matrices")

def input_weights_file(curve_name: str) -> str:
    """
    Full path to a curve's HDF5 weight matrix from Module 02.

    Parameters:
    -----------
    curve_name : str
        Name of the curve (e.g., 'curve_0001')

    Returns:
    --------
    str
        Path: outputs/hit_and_run_matrices/<curve_name>.h5
        Dataset 'weights' → shape (HORIZON_MONTHS, N_PORTFOLIOS, N_ASSETS)
    """
    return op.join(input_weights_dir(), f"{curve_name}.h5")

def output_results_dir() -> str:
    """
    Directory where HDF5 scenario result files are stored.

    Returns:
    --------
    str
        Path: outputs/scenario_results/
    """
    return op.join(BASE_DIR, "outputs", "scenario_results")

def output_results_file(curve_name: str) -> str:
    """
    Full path for a curve's HDF5 scenario results file.

    Parameters:
    -----------
    curve_name : str
        Name of the curve (e.g., 'curve_0001')

    Returns:
    --------
    str
        Path: outputs/scenario_results/<curve_name>.h5

    HDF5 contents:
    --------------
    Dataset 'annualized_returns' → shape (N_SEEDS, N_PORTFOLIOS)
        - axis 0: scenario seeds (one row per seed)
        - axis 1: portfolio trajectories (e.g., 10,000)
    Attributes on dataset:
        - curve_name       : str
        - scenario_seeds   : str  (comma-separated list of seeds)
        - shuffle_seed     : int
        - returns_seed     : int
        - simulation_method: str
        - horizon_months   : int
        - n_portfolios     : int
    """
    return op.join(output_results_dir(), f"{curve_name}.h5")
