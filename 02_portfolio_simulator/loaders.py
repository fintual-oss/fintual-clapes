import pandas as pd
import numpy as np

def load_glidepaths_universe(glides_file: str):
    """
    Load CVaR glidepaths from the step 01 output file.
    
    Expected structure:
      - Rows: t_start, t_A, A, B, t_B, t_end, Month_1, ..., Month_360
      - Columns: curve_0001, curve_0002, ..., curve_XXXX
    
    Parameters:
    -----------
    glides_file : str
        Path to the glidepaths_universe.xlsx file
    
    Returns:
    --------
    params_df : pd.DataFrame
        Parameters for each curve (rows: t_start, t_A, A, B, t_B, t_end)
    glides_df : pd.DataFrame
        Monthly CVaR limits (rows: months 1..360, columns: curve names)
    """
    # Load the full Excel file
    full_df = pd.read_excel(glides_file, header=0, index_col=0)
    
    # Parameter rows
    param_rows = ["t_start", "t_A", "A", "B", "t_B", "t_end"]
    
    # Extract parameters
    params_df = full_df.loc[
        [r for r in param_rows if r in full_df.index], :
    ].copy()
    
    # Extract monthly CVaR limits (rows starting with "Month_")
    idx_str = full_df.index.astype(str)
    monthly_mask = idx_str.str.startswith("Month_")
    glides_df = full_df.loc[monthly_mask, :].copy()
    
    # If no Month_ rows found, take all non-parameter rows
    if glides_df.empty:
        glides_df = full_df.loc[
            ~idx_str.isin(param_rows), :
        ].copy()
    
    # Reindex months as 1..T
    T = glides_df.shape[0]
    glides_df.index = range(1, T + 1)
    glides_df.index.name = "Month"
    
    # Ensure numeric values
    glides_df = glides_df.apply(pd.to_numeric, errors="coerce")
    
    return params_df, glides_df