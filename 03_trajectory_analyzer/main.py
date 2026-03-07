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
    calculate_percentiles,
    calculate_pct_above_targets
)
from exporters import export_analysis_to_excel
from transformations import transform_trajectories, get_mode_description

# ========================================
# CONFIGURATION
# ========================================

# ----------------------------------------
# ANALYSIS MODE (SELECT ONE)
# ----------------------------------------
# Mode 1: Analyze original trajectories only (no transformation)
# Mode 2: Analyze sorted trajectories only (ranked by return per month)
# Mode 3: Analyze permuted trajectories only (random permutation per month)
# Mode 4: Analyze permuted + sorted trajectories
#         This mode generates 2x trajectories: permuted + sorted
# Mode 5: Analyze original + sorted trajectories
#         This mode generates 2x trajectories: original + sorted
# Mode 6: Analyze original + permuted trajectories
#         This mode generates 2x trajectories: original + permuted
# Mode 7: Analyze original + sorted + permuted trajectories
#         This mode generates 3x trajectories: original + sorted + permuted
ANALYSIS_MODE = 3  # OPTIONS: 1, 2, 3, 4, 5, 6, or 7

# Random seed for permutation (only used in modes 3, 4, 6, and 7)
# Set to None for different results each run, or set an integer for reproducibility
RANDOM_SEED = 42

# Target return thresholds (annualized)
# Can be a single value or multiple: [0.04, 0.055, 0.07]
TARGET_RETURN_THRESHOLDS = [
    0.0686, 0.0676, 0.0666, 0.0656, 0.0647, 0.0638, 0.0629, 0.0620,
    0.0612, 0.0603, 0.0595, 0.0587, 0.0579, 0.0571, 0.0563, 0.0556,
    0.0548, 0.0541, 0.0534, 0.0526, 0.0519, 0.0512, 0.0505, 0.0499,
    0.0492, 0.0485, 0.0479, 0.0472, 0.0466, 0.0460, 0.0453, 0.0447,
    0.0441, 0.0435, 0.0429, 0.0423, 0.0418, 0.0412, 0.0406, 0.0401,
    0.0395, 0.0390, 0.0384, 0.0379, 0.0373, 0.0368, 0.0363, 0.0358,
    0.0353, 0.0347, 0.0342, 0.0337, 0.0332, 0.0328, 0.0323, 0.0318,
    0.0313, 0.0308, 0.0303, 0.0299, 0.0294
]

# Percentiles to calculate
PERCENTILES = [10, 25, 50, 75, 90]

# Process all available curves or specific ones
PROCESS_ALL_CURVES = True  # True = all available, False = only selected
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
    1. Load trajectory data (returns)
    2. Apply transformation based on ANALYSIS_MODE:
       - Mode 1: Use original trajectories
       - Mode 2: Generate sorted trajectories (ranked by return per month)
       - Mode 3: Generate permuted trajectories (random permutation per month)
       - Mode 4: Generate permuted + sorted trajectories
       - Mode 5: Generate original + sorted trajectories
       - Mode 6: Generate original + permuted trajectories
       - Mode 7: Generate original + sorted + permuted trajectories
    3. Calculate cumulative annualized returns
    4. Calculate statistics and percentiles
    5. Calculate cumulative risk from CVaR limits (step 01)
    6. Combine with curve parameters
    7. Export Excel with 1 sheet:
       - results: Summary of all curves with statistics and cumulative risk
    """

    print("=" * 70)
    print("TRAJECTORY ANALYSIS - PORTFOLIO PERFORMANCE")
    print("=" * 70)
    print(f"Analysis mode: {ANALYSIS_MODE}")
    print(f"  {get_mode_description(ANALYSIS_MODE)}")
    if ANALYSIS_MODE in [3, 4, 6, 7]:
        print(f"  Random seed: {RANDOM_SEED}")
    thresholds_str = ", ".join([f"{t*100:.2f}%" for t in TARGET_RETURN_THRESHOLDS])
    print(f"Target return thresholds: {thresholds_str}")
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
            # Load trajectory data (returns)
            returns_df, metadata = load_trajectory_results(
                input_hit_run_dir(),
                curve_name
            )

            n_months_original = returns_df.shape[0]
            n_trajectories_original = returns_df.shape[1]

            print(f"   Loaded: {n_months_original} months × {n_trajectories_original} trajectories")

            # ============================================
            # Apply transformation based on ANALYSIS_MODE
            # ============================================
            transformed_df, transformation_desc = transform_trajectories(
                returns_df=returns_df,
                mode=ANALYSIS_MODE,
                random_seed=RANDOM_SEED
            )

            n_months = transformed_df.shape[0]
            n_trajectories = transformed_df.shape[1]

            print(f"   Transformed: {transformation_desc}")

            # Calculate cumulative annualized returns
            cumulative_returns = calculate_cumulative_return_annualized(
                transformed_df.values
            )

            # Calculate summary statistics (mean, std, min, max)
            return_stats = calculate_trajectory_statistics(
                cumulative_returns,
                TARGET_RETURN_THRESHOLDS[0]  # kept for internal use, not exported
            )
            # Remove legacy single-threshold field
            return_stats.pop('pct_above_target', None)

            # Calculate percentiles
            return_percentiles = calculate_percentiles(
                cumulative_returns,
                PERCENTILES
            )

            # Calculate % above each target threshold
            pct_above_targets = calculate_pct_above_targets(
                cumulative_returns,
                TARGET_RETURN_THRESHOLDS
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
                'analysis_mode': ANALYSIS_MODE,
                'cumulative_risk': cumulative_risk,
                **return_stats,
                **return_percentiles,
                **pct_above_targets
            }

            results_list.append(result)

            print(f"   ✓ Analysis complete")
            print(f"      Return (annualized mean): {return_stats['return_mean']*100:.2f}%")
            for key, val in pct_above_targets.items():
                print(f"      Trajectories > {key.replace('pct_above_', '')}: {val*100:.2f}%")
            print(f"      Cumulative risk (area under curve): {cumulative_risk:.4f}")

        except Exception as e:
            print(f"⚠ Error analyzing {curve_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # ----------------------------------------
    # 5. Create DataFrame with all results
    # ----------------------------------------
    print("\n[5/7] Consolidating results...")

    if len(results_list) == 0:
        print("⚠ No results to export!")
        return

    results_df = pd.DataFrame(results_list)

    # Sort by first threshold column, then by mean return
    first_threshold_key = f"pct_above_{TARGET_RETURN_THRESHOLDS[0]*100:.2f}%"
    results_df = results_df.sort_values(
        by=[first_threshold_key, 'return_mean'],
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
    print(f"Analysis mode: {ANALYSIS_MODE} - {get_mode_description(ANALYSIS_MODE)}")
    print(f"Curves analyzed: {len(results_df)}")
    thresholds_str = ", ".join([f"{t*100:.2f}%" for t in TARGET_RETURN_THRESHOLDS])
    print(f"Target return thresholds: {thresholds_str}")

    if len(results_df) > 0:
        best_curve = results_df.iloc[0]
        print(f"\nBest curve (highest % above first target):")
        print(f"  {best_curve['curve_id']}")
        print(f"  - A: {best_curve['A']:.4f}, B: {best_curve['B']:.4f}")
        print(f"  - t_A: {best_curve['t_A']:.0f} years")
        print(f"  - Return (mean): {best_curve['return_mean']*100:.2f}%")
        for key in pct_above_targets.keys():
            print(f"  - Trajectories > {key.replace('pct_above_', '')}: {best_curve[key]*100:.2f}%")
        print(f"  - Cumulative risk: {best_curve['cumulative_risk']:.4f}")

    print("\n" + "=" * 70)
    print("COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"\nResults saved to: {output_file}")
    print(f"Sheet:")
    print(f"  - 'results': Summary of all curves with statistics and cumulative risk")


if __name__ == "__main__":
    main()
