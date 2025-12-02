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
    
    Creates an Excel file with two sheets:
      - 'cvar': CVaR values (rows=months, columns=trajectories)
      - 'returns': Average returns (rows=months, columns=trajectories)
    
    Parameters:
    -----------
    output_file : str
        Path to the output Excel file
    cvar_matrix : np.ndarray
        CVaR matrix (shape: HORIZON_MONTHS × N_PORTFOLIOS)
    returns_matrix : np.ndarray
        Returns matrix (shape: HORIZON_MONTHS × N_PORTFOLIOS)
    n_portfolios : int
        Number of portfolios (trajectories)
    """
    # Trajectory column names: trajectory_001, trajectory_002, etc.
    trajectory_names = [f"trajectory_{i+1:03d}" for i in range(n_portfolios)]
    
    # Month row labels: 1, 2, 3, ..., 360
    n_months = cvar_matrix.shape[0]
    month_labels = list(range(1, n_months + 1))
    
    # Create DataFrames
    cvar_df = pd.DataFrame(
        cvar_matrix,
        index=month_labels,
        columns=trajectory_names
    )
    cvar_df.index.name = "Month"
    
    returns_df = pd.DataFrame(
        returns_matrix,
        index=month_labels,
        columns=trajectory_names
    )
    returns_df.index.name = "Month"
    
    # Export to Excel with two sheets
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        cvar_df.to_excel(writer, sheet_name="cvar")
        returns_df.to_excel(writer, sheet_name="returns")