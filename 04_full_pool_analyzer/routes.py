import os.path as op

# Base folder = repository root (two levels above this package)
BASE_DIR = op.dirname(op.dirname(op.abspath(__file__)))

def input_glidepaths_path() -> str:
    """
    Path to the Excel file with CVaR glidepaths from Module 01.
    Used to load curve parameters and CVaR limits.
    """
    return op.join(BASE_DIR, "outputs", "glidepaths_universe.xlsx")

def input_scenario_results_dir() -> str:
    """
    Directory with HDF5 scenario result files from Module 03.
    Path: outputs/scenario_results/
    """
    return op.join(BASE_DIR, "outputs", "scenario_results")

def input_scenario_results_file(curve_name: str) -> str:
    """
    Full path to a curve's HDF5 scenario results file from Module 03.

    Parameters:
    -----------
    curve_name : str
        Name of the curve (e.g., 'curve_0001')

    Returns:
    --------
    str
        Path: outputs/scenario_results/<curve_name>.h5
        Dataset 'annualized_returns' -> shape (N_SEEDS, N_PORTFOLIOS)
    """
    return op.join(input_scenario_results_dir(), f"{curve_name}.h5")

def output_analysis_full_pool_dir() -> str:
    """
    Directory for full pool analysis output files.
    Path: outputs/analysis_full_pool/
    """
    return op.join(BASE_DIR, "outputs", "analysis_full_pool")

def output_analysis_full_pool_file(label: str = "") -> str:
    """
    Path to the output Excel file.

    Parameters:
    -----------
    label : str
        Optional label appended to filename.
        Leave as "" for default filename.

    Returns:
    --------
    str
        Path: outputs/analysis_full_pool/analysis_full_pool_<label>.xlsx
              or    outputs/analysis_full_pool/analysis_full_pool.xlsx
    """
    filename = f"analysis_full_pool_{label}.xlsx" if label else "analysis_full_pool.xlsx"
    return op.join(output_analysis_full_pool_dir(), filename)
