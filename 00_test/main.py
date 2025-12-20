import os
import sys
import pandas as pd
import numpy as np
import time

# Get the directory of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add this directory to the beginning of sys.path to prioritize local imports
sys.path.insert(0, SCRIPT_DIR)

# Import local modules from this directory (with test_ prefix to avoid conflicts)
import test_config
import test_routes
import test_portfolio_generator
import test_diversity_metrics
import test_exporters

# Extract what we need from config
PROCESS_ALL_CURVES = test_config.PROCESS_ALL_CURVES
CURVES_TO_ANALYZE = test_config.CURVES_TO_ANALYZE
N_PORTFOLIOS_TO_ANALYZE = test_config.N_PORTFOLIOS_TO_ANALYZE
RETURNS_SEED = test_config.RETURNS_SEED
HIT_RUN_SEED = test_config.HIT_RUN_SEED
SCENARIO_SEED = test_config.SCENARIO_SEED
SIMULATION_METHOD = test_config.SIMULATION_METHOD
ALPHA_CVAR = test_config.ALPHA_CVAR
N_TRAJ = test_config.N_TRAJ
HORIZON_MONTHS = test_config.HORIZON_MONTHS
PERCENTILES = test_config.PERCENTILES

# Functions from routes
input_returns_path = test_routes.input_returns_path
input_glidepaths_path = test_routes.input_glidepaths_path
output_diversity_dir = test_routes.output_diversity_dir
output_diversity_file = test_routes.output_diversity_file

# Functions from other modules
generate_portfolios_with_weights = test_portfolio_generator.generate_portfolios_with_weights
calculate_all_diversity_metrics = test_diversity_metrics.calculate_all_diversity_metrics
export_diversity_metrics = test_exporters.export_diversity_metrics

def load_glidepaths_data(glides_file: str):
    """
    Load CVaR glidepaths from step 01 output.
    
    Returns:
    --------
    params_df : pd.DataFrame
        Parameters for each curve
    glides_df : pd.DataFrame
        Monthly CVaR limits
    """
    full_df = pd.read_excel(glides_file, header=0, index_col=0)
    
    # Parameter rows
    param_rows = ["t_start", "t_A", "A", "B", "t_B", "t_end"]
    params_df = full_df.loc[
        [r for r in param_rows if r in full_df.index], :
    ].copy()
    
    # Monthly CVaR limits
    idx_str = full_df.index.astype(str)
    monthly_mask = idx_str.str.startswith("Month_")
    glides_df = full_df.loc[monthly_mask, :].copy()
    
    if glides_df.empty:
        glides_df = full_df.loc[~idx_str.isin(param_rows), :].copy()
    
    T = glides_df.shape[0]
    glides_df.index = range(1, T + 1)
    glides_df.index.name = "Month"
    glides_df = glides_df.apply(pd.to_numeric, errors="coerce")
    
    return params_df, glides_df


def main() -> None:
    """
    Analyze portfolio diversity for selected CVaR glidepath curves.
    
    For each curve:
    1. Re-generate portfolios using SAME seeds as step 02
    2. Extract portfolio weights (not saved in step 02)
    3. Calculate diversity metrics
    4. Export to Excel (one file per curve)
    """
    
    print("=" * 70)
    print("PORTFOLIO DIVERSITY ANALYZER")
    print("=" * 70)
    print(f"Portfolios per month: {N_PORTFOLIOS_TO_ANALYZE}")
    print(f"Simulation method: {SIMULATION_METHOD.upper()}")
    print(f"CVaR level: {ALPHA_CVAR*100:.0f}%")
    print(f"Monte Carlo scenarios: {N_TRAJ:,}")
    print(f"Horizon: {HORIZON_MONTHS} months")
    print()
    print("Seeds (must match step 02):")
    print(f"  - Returns seed: {RETURNS_SEED}")
    print(f"  - Hit-and-Run seed: {HIT_RUN_SEED}")
    print(f"  - Scenario seed: {SCENARIO_SEED}")
    print("=" * 70)
    
    # ----------------------------------------
    # 1. Load historical returns
    # ----------------------------------------
    print("\n[1/5] Loading historical returns...")
    returns_df = pd.read_csv(
        input_returns_path(),
        sep=",",
        parse_dates=[0],
        index_col=0
    )
    
    n_assets = returns_df.shape[1]
    asset_names = returns_df.columns.tolist()
    print(f"   ✓ Loaded {returns_df.shape[0]} periods × {n_assets} assets")
    print(f"   Assets: {', '.join(asset_names)}")
    
    # ----------------------------------------
    # 2. Load CVaR glidepath curves
    # ----------------------------------------
    print("\n[2/5] Loading CVaR glidepath curves...")
    params_df, glides_df = load_glidepaths_data(input_glidepaths_path())
    all_curves = glides_df.columns.tolist()
    print(f"   ✓ Loaded {len(all_curves)} curves")
    
    # Select curves to analyze
    if PROCESS_ALL_CURVES:
        curves_to_analyze = all_curves
        print(f"   → Analyzing ALL {len(curves_to_analyze)} curves")
    else:
        curves_to_analyze = [c for c in CURVES_TO_ANALYZE if c in all_curves]
        if len(curves_to_analyze) == 0:
            print("\n   ✗ ERROR: No valid curves selected!")
            return
        print(f"   → Analyzing {len(curves_to_analyze)} selected curves:")
        for c in curves_to_analyze:
            print(f"      - {c}")
    
    # ----------------------------------------
    # 3. Create output directory
    # ----------------------------------------
    print("\n[3/5] Setting up output directory...")
    output_dir = output_diversity_dir()
    os.makedirs(output_dir, exist_ok=True)
    print(f"   ✓ Output directory: {output_dir}")
    
    # ----------------------------------------
    # 4. Process each curve
    # ----------------------------------------
    print("\n[4/5] Analyzing portfolio diversity...")
    print("-" * 70)
    
    start_time = time.time()
    
    for curve_idx, curve_name in enumerate(curves_to_analyze, 1):
        print(f"\n[Curve {curve_idx}/{len(curves_to_analyze)}] {curve_name}")
        
        curve_start_time = time.time()
        
        try:
            # Get CVaR limits for this curve
            cvar_limits = glides_df[curve_name].values
            
            if len(cvar_limits) != HORIZON_MONTHS:
                print(f"   ✗ ERROR: Expected {HORIZON_MONTHS} months, got {len(cvar_limits)}")
                continue
            
            # Get curve parameters
            if curve_name in params_df.columns:
                A = params_df.loc['A', curve_name]
                B = params_df.loc['B', curve_name]
                t_A = params_df.loc['t_A', curve_name]
                print(f"   Parameters: A={A:.4f}, B={B:.4f}, t_A={t_A:.0f}")
            
            # Step 1: Generate portfolios with weights
            print(f"   [1/3] Generating {N_PORTFOLIOS_TO_ANALYZE} portfolios per month...")
            weights_matrix = generate_portfolios_with_weights(
                returns_df=returns_df,
                cvar_limits=cvar_limits,
                n_portfolios=N_PORTFOLIOS_TO_ANALYZE,
                n_traj=N_TRAJ,
                horizon_months=HORIZON_MONTHS,
                alpha_cvar=ALPHA_CVAR,
                returns_seed=RETURNS_SEED,
                hit_run_seed=HIT_RUN_SEED,
                simulation_method=SIMULATION_METHOD
            )
            
            # Check for NaN values
            nan_count = np.isnan(weights_matrix).sum()
            if nan_count > 0:
                print(f"      ⚠ Warning: {nan_count} NaN values in weights")
            
            print(f"      ✓ Weights matrix shape: {weights_matrix.shape}")
            
            # Step 2: Calculate diversity metrics
            print(f"   [2/3] Calculating diversity metrics...")
            metrics_dict = calculate_all_diversity_metrics(
                weights_matrix=weights_matrix,
                asset_names=asset_names,
                percentiles=PERCENTILES
            )
            print(f"      ✓ Calculated {len(metrics_dict)} metrics")
            
            # Step 3: Export to Excel
            print(f"   [3/3] Exporting to Excel...")
            output_file = output_diversity_file(curve_name)
            export_diversity_metrics(
                metrics_dict=metrics_dict,
                output_file=output_file,
                curve_name=curve_name,
                n_portfolios=N_PORTFOLIOS_TO_ANALYZE
            )
            
            curve_elapsed = time.time() - curve_start_time
            print(f"   ✓ Completed in {curve_elapsed:.1f} seconds")
            
        except Exception as e:
            print(f"   ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # ----------------------------------------
    # 5. Summary
    # ----------------------------------------
    total_elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"Curves analyzed: {len(curves_to_analyze)}")
    print(f"Portfolios per curve: {N_PORTFOLIOS_TO_ANALYZE}")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print(f"\nResults saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
