import pandas as pd

def export_analysis_to_excel(
    results_df: pd.DataFrame,
    output_file: str
) -> None:
    """
    Export analysis results to Excel with single sheet.
    
    Creates 1 sheet:
    - 'results': Summary of all curves with statistics and cumulative risk
    
    Parameters:
    -----------
    results_df : pd.DataFrame
        DataFrame with all analysis results (summary)
    output_file : str
        Path to output Excel file
    """
    
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        # Sheet: Summary results
        results_df.to_excel(writer, sheet_name='results', index=False)
    
    print(f"   ✓ Excel file created:")
    print(f"      - Sheet 'results': {len(results_df)} curves analyzed")
