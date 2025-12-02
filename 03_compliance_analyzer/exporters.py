import pandas as pd
from typing import List

def export_analysis_to_excel(
    results_df: pd.DataFrame,
    output_file: str,
    target_return: float,
    percentiles: List[int]
) -> None:
    """
    Export analysis results to Excel - simple, no formatting.
    
    Creates a single sheet with all results.
    
    Parameters:
    -----------
    results_df : pd.DataFrame
        DataFrame with all analysis results
    output_file : str
        Path to output Excel file
    target_return : float
        Target return threshold used (not used, kept for compatibility)
    percentiles : List[int]
        Percentiles calculated (not used, kept for compatibility)
    """
    
    # Export to Excel - single sheet, no formatting
    results_df.to_excel(output_file, sheet_name='results', index=False)
    
    print(f"   Excel file created:")
    print(f"      - {len(results_df)} curves analyzed")
    print(f"      - {len(results_df.columns)} columns")