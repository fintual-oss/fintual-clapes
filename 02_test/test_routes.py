import os.path as op
import sys

# Add current directory to path
SCRIPT_DIR = op.dirname(op.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import test_config

# Base directory = repository root (two levels above this package)
BASE_DIR = op.dirname(op.dirname(op.abspath(__file__)))

def input_returns_path() -> str:
    """
    Path to the CSV with historical returns.
    """
    return op.join(BASE_DIR, "returns.csv")

def input_glidepaths_path() -> str:
    """
    Path to the Excel file with CVaR glidepaths from step 01.
    """
    return op.join(BASE_DIR, "outputs", "glidepaths_universe.xlsx")

def output_diversity_dir() -> str:
    """
    Directory for portfolio diversity analysis results.
    """
    OUTPUT_SUBDIR = test_config.OUTPUT_SUBDIR
    return op.join(BASE_DIR, "outputs", OUTPUT_SUBDIR)

def output_diversity_file(curve_name: str) -> str:
    """
    Full path for a curve's diversity analysis Excel file.
    
    Parameters:
    -----------
    curve_name : str
        Name of the curve (e.g., 'curve_0001')
    
    Returns:
    --------
    str
        Full path to the Excel file
    """
    filename = f"{curve_name}_diversity.xlsx"
    return op.join(output_diversity_dir(), filename)
