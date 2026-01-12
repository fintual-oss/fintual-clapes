import pandas as pd
from typing import Dict

def export_diversity_metrics(
    metrics_dict: Dict[str, pd.DataFrame],
    output_file: str,
    curve_name: str,
    n_portfolios: int
) -> None:
    """
    Export diversity metrics to Excel file with multiple sheets.
    
    MODIFIED VERSION:
    - Per-asset: weights_mean, weights_std only
    - Portfolio-level: hhi, euclidean_distance (both 1000 portfolios × 480 months)
    - Snapshots: weights_month_001, weights_month_240, weights_month_XXX
    
    Parameters:
    -----------
    metrics_dict : Dict[str, pd.DataFrame]
        Dictionary with all calculated metrics
    output_file : str
        Path to output Excel file
    curve_name : str
        Name of the curve being analyzed
    n_portfolios : int
        Number of portfolios analyzed
    """
    
    # Create Excel writer
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        
        # Get workbook and add formats
        workbook = writer.book
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })
        
        # NEW: Sheet order and descriptions
        sheet_order = [
            ('weights_mean', 'Mean portfolio weights across all trajectories (months × assets)'),
            ('weights_std', 'Standard deviation of weights (months × assets)'),
            ('hhi', 'Herfindahl-Hirschman Index for each portfolio at each month (portfolios × months)'),
            ('euclidean_distance', 'Euclidean distance from equal-weight portfolio (portfolios × months)'),
            ('weights_month_001', 'Portfolio weights snapshot at Month 1 (portfolios × assets)'),
            ('weights_month_240', 'Portfolio weights snapshot at Month 240 (portfolios × assets)'),
        ]
        
        # Find the last month snapshot dynamically
        last_month_key = None
        for key in metrics_dict.keys():
            if key.startswith('weights_month_') and key not in ['weights_month_001', 'weights_month_240']:
                last_month_key = key
                # Extract month number from key
                month_num = key.split('_')[-1]
                sheet_order.append((key, f'Portfolio weights snapshot at Month {month_num} (portfolios × assets)'))
                break
        
        # Write each sheet
        for sheet_name, description in sheet_order:
            if sheet_name in metrics_dict:
                df = metrics_dict[sheet_name]
                
                # Write to Excel
                df.to_excel(writer, sheet_name=sheet_name)
                
                # Get worksheet
                worksheet = writer.sheets[sheet_name]
                
                # Add description as comment in cell A1
                worksheet.write_comment('A1', description)
                
                # Auto-adjust column widths based on sheet type
                if sheet_name in ['weights_mean', 'weights_std']:
                    # Per-asset sheets: Month column + asset columns
                    for idx, col in enumerate(df.columns):
                        max_len = max(
                            df[col].astype(str).map(len).max(),
                            len(str(col))
                        ) + 2
                        worksheet.set_column(idx + 1, idx + 1, min(max_len, 12))
                    worksheet.set_column(0, 0, 8)  # Month column
                    
                elif sheet_name in ['hhi', 'euclidean_distance']:
                    # Portfolio × Month matrices: Portfolio column + many month columns
                    # Set all month columns to width 10
                    worksheet.set_column(1, len(df.columns), 10)
                    worksheet.set_column(0, 0, 16)  # Portfolio column
                    
                elif sheet_name.startswith('weights_month_'):
                    # Snapshot sheets: Portfolio column + asset columns
                    for idx, col in enumerate(df.columns):
                        max_len = max(
                            df[col].astype(str).map(len).max(),
                            len(str(col))
                        ) + 2
                        worksheet.set_column(idx + 1, idx + 1, min(max_len, 12))
                    worksheet.set_column(0, 0, 16)  # Portfolio column
        
        # Create summary sheet
        n_months = len(metrics_dict['weights_mean'])
        n_assets = len(metrics_dict['weights_mean'].columns)
        
        summary_data = {
            'Parameter': [
                'Curve Name',
                'Number of Portfolios',
                'Number of Months',
                'Number of Assets',
                'Equal-Weight Reference',
            ],
            'Value': [
                curve_name,
                n_portfolios,
                n_months,
                n_assets,
                f'1/{n_assets} = {1/n_assets:.6f}',
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='summary', index=False)
        
        # Format summary sheet
        worksheet = writer.sheets['summary']
        worksheet.set_column(0, 0, 25)
        worksheet.set_column(1, 1, 25)
    
    print(f"      ✓ Excel file created: {output_file}")
    print(f"         - {len(metrics_dict)} sheets")
    print(f"         - {n_portfolios} portfolios analyzed")
    print(f"         - Sheets: summary, weights_mean, weights_std, hhi, euclidean_distance, + 3 snapshots")
