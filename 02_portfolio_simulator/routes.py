import os.path as op

# Base folder = repository root (one level above this package)
BASE_DIR = op.dirname(op.dirname(op.abspath(__file__)))

def input_returns_path() -> str:
    """
    Path to the CSV with historical returns.
    Expects a file named 'returns.csv' at the repo root.
    """
    return op.join(BASE_DIR, "returns.csv")

def input_glidepaths_path() -> str:
    """
    Path to the Excel file with CVaR glidepaths from step 01.
    Expects 'glidepaths_universe.xlsx' in the outputs folder.
    """
    return op.join(BASE_DIR, "outputs", "glidepaths_universe.xlsx")

def output_hit_run_dir(run_label: str) -> str:
    """
    Directory for Hit-and-Run results, scoped by run_label.
    
    Parameters:
    -----------
    run_label : str
        Unique label for this run (e.g., 'juan_333')
    
    Returns:
    --------
    str
        Path to the output directory: outputs/hit_run_results/<run_label>/
    """
    return op.join(BASE_DIR, "outputs", "hit_run_results", run_label)

def output_hit_run_file(curve_name: str, run_label: str) -> str:
    """
    Full path for a curve's results file, scoped by run_label.
    
    Parameters:
    -----------
    curve_name : str
        Name of the curve (e.g., 'curve_0001')
    run_label : str
        Unique label for this run (e.g., 'juan_333')
    
    Returns:
    --------
    str
        Full path to the Excel file
    """
    filename = f"{curve_name}_results.xlsx"
    return op.join(output_hit_run_dir(run_label), filename)