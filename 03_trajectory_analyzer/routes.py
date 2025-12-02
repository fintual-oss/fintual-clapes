import os.path as op

# Base directory = repository root (one level above this package)
BASE_DIR = op.dirname(op.dirname(op.abspath(__file__)))

def input_glidepaths_path() -> str:
    """
    Path to the glidepaths universe Excel from step 01.
    """
    return op.join(BASE_DIR, "outputs", "glidepaths_universe.xlsx")

def input_hit_run_dir() -> str:
    """
    Directory with hit-and-run results from step 02.
    """
    return op.join(BASE_DIR, "outputs", "hit_run_results")

def input_hit_run_file(curve_name: str) -> str:
    """
    Path to a specific curve's results file from step 02.
    
    Parameters:
    -----------
    curve_name : str
        Name of the curve (e.g., 'curve_0001')
    
    Returns:
    --------
    str
        Full path to the Excel file
    """
    filename = f"{curve_name}_results.xlsx"
    return op.join(input_hit_run_dir(), filename)

def output_dir() -> str:
    """
    Directory for analysis outputs.
    """
    return op.join(BASE_DIR, "outputs")

def output_analysis_file() -> str:
    """
    Path to the comprehensive analysis Excel file.
    """
    return op.join(output_dir(), "trajectory_analysis_summary.xlsx")