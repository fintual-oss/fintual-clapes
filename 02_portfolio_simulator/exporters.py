import pandas as pd
import numpy as np

def export_curve_results(
    output_file: str,
    returns_matrix: np.ndarray,
    n_portfolios: int
) -> None:
    """
    Export returns matrix to Excel.
    
    IMPORTANT: Matrix is TRANSPOSED before saving to support large simulations.
    
    Creates an Excel file with one sheet:
      - 'returns': Monthly returns (rows=trajectories, columns=months)
    
    This format allows simulating millions of trajectories without hitting Excel's
    column limit (16,384 columns). With transposed format:
    - Rows: trajectories (can be 1,000,000+)
    - Columns: months (typically 480)
    
    Parameters:
    -----------
    output_file : str
        Path to the output Excel file
    returns_matrix : np.ndarray
        Returns matrix (shape: HORIZON_MONTHS × N_PORTFOLIOS)
        Will be transposed to (N_PORTFOLIOS × HORIZON_MONTHS) before saving
    n_portfolios : int
        Number of portfolios (trajectories)
    """
    # Trajectory row labels: trajectory_001, trajectory_002, etc.
    trajectory_names = [f"trajectory_{i+1:03d}" for i in range(n_portfolios)]
    
    # Month column labels: Month_1, Month_2, Month_3, ..., Month_480
    n_months = returns_matrix.shape[0]
    month_labels = [f"Month_{i}" for i in range(1, n_months + 1)]
    
    # TRANSPOSE matrix: (MONTHS × N_PORTFOLIOS) → (N_PORTFOLIOS × MONTHS)
    # This allows storing millions of trajectories in Excel
    returns_matrix_T = returns_matrix.T
    
    # Create DataFrame with TRANSPOSED orientation
    # Rows: trajectories, Columns: months
    returns_df = pd.DataFrame(
        returns_matrix_T,
        index=trajectory_names,
        columns=month_labels
    )
    returns_df.index.name = "Trajectory"
    
    # Export to Excel with single sheet
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        returns_df.to_excel(writer, sheet_name="returns")
