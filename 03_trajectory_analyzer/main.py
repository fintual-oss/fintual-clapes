import os
import pandas as pd
import numpy as np
from pathlib import Path

# Import local modules
from routes import (
    input_glidepaths_path,
    input_hit_run_dir,
    output_dir,
    output_analysis_file
)
from loaders import (
    load_glidepaths_parameters,
    load_glidepaths_cvar_limits,
    load_trajectory_results,
    get_available_curves
)
from metrics import (
    calculate_cumulative_return_annualized,
    calculate_trajectory_statistics,
    calculate_percentiles
)
from exporters import export_analysis_to_excel

# ========================================
# CONFIGURATION
# ========================================

# Target return threshold (annualized)
TARGET_RETURN_THRESHOLD = 0.0855

# Percentiles to calculate
PERCENTILES = [10, 25, 50, 75, 90]

# Process all available curves or specific ones
PROCESS_ALL_CURVES =True  # True = all available, False = only selected
CURVES_TO_ANALYZE = [
    "curve_0001",
    "curve_0002"
]

# ========================================
# MAIN FUNCTION
# ========================================

def main() -> None:
    """
    Analyze trajectory results from step 02 and generate Excel report.

    For each curve:
    1. Load trajectory data (returns and CVaR)
    2. Calculate cumulative annualized returns
    3. Calculate statistics and percentiles
    4. Calculate cumulative risk from CVaR limits (step 01)
    5. Combine with curve parameters
    6. Export Excel with 1 sheet:
       - results: Summary of all curves with statistics and cumulative risk
    """

    print("=" * 70)
    print("TRAJECTORY ANALYSIS - PORTFOLIO PERFORMANCE")
    print("=" * 70)
    print(f"Target return threshold: {TARGET_RETURN_THRESHOLD*100:.1f}%")
    print(f"Percentiles: {PERCENTILES}")
    print("=" * 70)

    # ----------------------------------------
    # 1. Load glidepath parameters
    # ----------------------------------------
    print("\n[1/7] Loading glidepath parameters...")
    params_df = load_glidepaths_parameters(input_glidepaths_path())
    print(f"   ✓ Loaded parameters for {params_df.shape[1]} curves")

    # ----------------------------------------
    # 2. Load CVaR limits from step 01
    # ----------------------------------------
    print("\n[2/7] Loading CVaR limit curves from step 01...")
    cvar_limits_df = load_glidepaths_cvar_limits(input_glidepaths_path())
    print(f"   ✓ Loaded CVaR limits: {cvar_limits_df.shape[0]} months × {cvar_limits_df.shape[1]} curves")

    # ----------------------------------------
    # 3. Get available curves from hit_run_results
    # ----------------------------------------
    print("\n[3/7] Finding available trajectory results...")
    available_curves = get_available_curves(input_hit_run_dir())
    print(f"   ✓ Found {len(available_curves)} curves with results")

    if len(available_curves) == 0:
        print("\n⚠ No trajectory results found!")
        print("   Make sure step 02 has been executed and results are in:")
        print(f"   {input_hit_run_dir()}")
        return

    # Select which curves to analyze
    if PROCESS_ALL_CURVES:
        curves_to_analyze = available_curves
        print(f"   Analyzing ALL {len(curves_to_analyze)} curves")
    else:
        curves_to_analyze = [c for c in CURVES_TO_ANALYZE if c in available_curves]
        if len(curves_to_analyze) == 0:
            print("\n⚠ None of the selected curves have results!")
            return
        print(f"   Analyzing {len(curves_to_analyze)} selected curves:")
        for c in curves_to_analyze:
            print(f"      - {c}")

    # ----------------------------------------
    # 4. Analyze each curve
    # ----------------------------------------
    print("\n[4/7] Analyzing trajectories...")
    print("-" * 70)

    results_list = []

    for curve_idx, curve_name in enumerate(curves_to_analyze, 1):
        print(f"\n[Curve {curve_idx}/{len(curves_to_analyze)}] {curve_name}")

        try:
            # Load trajectory data (returns and CVaR)
            returns_df, cvar_df, metadata = load_trajectory_results(
                input_hit_run_dir(),
                curve_name
            )

            n_months = returns_df.shape[0]
            n_trajectories = returns_df.shape[1]

            print(f"   Data: {n_months} months × {n_trajectories} trajectories")

            # Calculate cumulative annualized returns
            cumulative_returns = calculate_cumulative_return_annualized(
                returns_df.values
            )

            # Calculate summary statistics
            return_stats = calculate_trajectory_statistics(
                cumulative_returns,
                TARGET_RETURN_THRESHOLD
            )

            # Calculate percentiles
            return_percentiles = calculate_percentiles(
                cumulative_returns,
                PERCENTILES
            )

            # Get curve parameters
            if curve_name in params_df.columns:
                curve_params = params_df[curve_name].to_dict()
            else:
                print(f"   ⚠ Warning: Parameters not found for {curve_name}")
                curve_params = {
                    't_start': np.nan,
                    't_A': np.nan,
                    'A': np.nan,
                    'B': np.nan,
                    't_B': np.nan,
                    't_end': np.nan
                }

            # ============================================
            # Calculate cumulative risk from CVaR limits (step 01)
            # ============================================
            if curve_name in cvar_limits_df.columns:
                cvar_limits = cvar_limits_df[curve_name].values
                # Cumulative risk = sum of all monthly CVaR limits
                cumulative_risk = np.sum(cvar_limits)
            else:
                print(f"   ⚠ Warning: CVaR limits not found for {curve_name}")
                cumulative_risk = np.nan

            # Combine all information into a single record for summary
            result = {
                'curve_id': curve_name,
                **curve_params,
                'n_trajectories': n_trajectories,
                'horizon_months': n_months,
                'cumulative_risk': cumulative_risk,  # NEW: Risk from step 01 curve
                **return_stats,
                **return_percentiles
            }

            results_list.append(result)

            print(f"   ✓ Analysis complete")
            print(f"      Return (annualized mean): {return_stats['return_mean']*100:.2f}%")
            print(f"      Trajectories > {TARGET_RETURN_THRESHOLD*100:.0f}%: "
                  f"{return_stats['pct_above_target']*100:.1f}%")
            print(f"      Cumulative risk (area under curve): {cumulative_risk:.4f}")

        except Exception as e:
            print(f"⚠ Error analyzing {curve_name}: {e}")
            continue

    # ----------------------------------------
    # 5. Create DataFrame with all results
    # ----------------------------------------
    print("\n[5/7] Consolidating results...")

    if len(results_list) == 0:
        print("⚠ No results to export!")
        return

    results_df = pd.DataFrame(results_list)

    # Sort by percentage above target, then by mean return
    results_df = results_df.sort_values(
        by=['pct_above_target', 'return_mean'],
        ascending=[False, False]
    )

    print(f"   ✓ Consolidated {len(results_df)} curve analyses")

    # ----------------------------------------
    # 6. Export to Excel
    # ----------------------------------------
    print("\n[6/7] Exporting to Excel...")

    os.makedirs(output_dir(), exist_ok=True)
    output_file = output_analysis_file()

    export_analysis_to_excel(
        results_df=results_df,
        output_file=output_file
    )

    print(f"   ✓ Saved: {output_file}")

    # ----------------------------------------
    # 7. Summary information
    # ----------------------------------------
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Curves analyzed: {len(results_df)}")
    print(f"Target return: {TARGET_RETURN_THRESHOLD*100:.1f}%")

    if len(results_df) > 0:
        best_curve = results_df.iloc[0]
        print(f"\nBest curve (highest % above target):")
        print(f"  {best_curve['curve_id']}")
        print(f"  - A: {best_curve['A']:.4f}, B: {best_curve['B']:.4f}")
        print(f"  - t_A: {best_curve['t_A']:.0f} years")
        print(f"  - Return (mean): {best_curve['return_mean']*100:.2f}%")
        print(f"  - Trajectories > target: {best_curve['pct_above_target']*100:.1f}%")
        print(f"  - Cumulative risk: {best_curve['cumulative_risk']:.4f}")

    print("\n" + "=" * 70)
    print("COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"\nResults saved to: {output_file}")
    print(f"Sheet:")
    print(f"  - 'results': Summary of all curves with statistics and cumulative risk")


if __name__ == "__main__":
    main()
