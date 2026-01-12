import pandas as pd
import numpy as np

def export_curve_results(
    output_file: str,
    cvar_matrix: np.ndarray,
    returns_matrix: np.ndarray,
    n_portfolios: int
) -> None:
    """
    Export CVaR and returns matrices to Excel.
    
    IMPORTANT: Matrices are TRANSPOSED before saving to support large simulations.
    
    Creates an Excel file with two sheets:
      - 'cvar': CVaR values (rows=trajectories, columns=months)
      - 'returns': Average returns (rows=trajectories, columns=months)
    
    This format allows simulating millions of trajectories without hitting Excel's
    column limit (16,384 columns). With transposed format:
    - Rows: trajectories (can be 1,000,000+)
    - Columns: months (typically 480)
    
    Parameters:
    -----------
    output_file : str
        Path to the output Excel file
    cvar_matrix : np.ndarray
        CVaR matrix (shape: HORIZON_MONTHS × N_PORTFOLIOS)
        Will be transposed to (N_PORTFOLIOS × HORIZON_MONTHS) before saving
    returns_matrix : np.ndarray
        Returns matrix (shape: HORIZON_MONTHS × N_PORTFOLIOS)
        Will be transposed to (N_PORTFOLIOS × HORIZON_MONTHS) before saving
    n_portfolios : int
        Number of portfolios (trajectories)
    """
    # Trajectory row labels: trajectory_001, trajectory_002, etc.
    trajectory_names = [f"trajectory_{i+1:03d}" for i in range(n_portfolios)]
    
    # Month column labels: Month_1, Month_2, Month_3, ..., Month_480
    n_months = cvar_matrix.shape[0]
    month_labels = [f"Month_{i}" for i in range(1, n_months + 1)]
    
    # TRANSPOSE matrices: (MONTHS × N_PORTFOLIOS) → (N_PORTFOLIOS × MONTHS)
    # This allows storing millions of trajectories in Excel
    cvar_matrix_T = cvar_matrix.T
    returns_matrix_T = returns_matrix.T
    
    # Create DataFrames with TRANSPOSED orientation
    # Rows: trajectories, Columns: months
    cvar_df = pd.DataFrame(
        cvar_matrix_T,
        index=trajectory_names,
        columns=month_labels
    )
    cvar_df.index.name = "Trajectory"
    
    returns_df = pd.DataFrame(
        returns_matrix_T,
        index=trajectory_names,
        columns=month_labels
    )
    returns_df.index.name = "Trajectory"
    
    # Export to Excel with two sheets
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        cvar_df.to_excel(writer, sheet_name="cvar")
        returns_df.to_excel(writer, sheet_name="returns")
