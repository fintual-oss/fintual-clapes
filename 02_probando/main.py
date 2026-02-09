import os
import numpy as np
import pandas as pd
from pathlib import Path
import time
from multiprocessing import Pool, cpu_count

# Import helper functions
from routes import (
    input_returns_path,
    input_glidepaths_path,
    output_hit_run_dir,
    output_hit_run_file,
)
from make_psd import f_make_psd
from simulate_asset_returns import simulate_asset_returns
from loaders import load_glidepaths_universe
from exporters import export_curve_results
from trajectory_generator import (
    generate_single_trajectory_backward,
    validate_trajectory
)

# ========================================
# CONFIGURATION - EDIT THESE PARAMETERS
# ========================================

# Simulation method
SIMULATION_METHOD = "copula"  # "mvn" or "copula"
# - "mvn": Multivariate Normal (faster, assumes Gaussian distribution)
# - "copula": Gaussian Copula (slower, preserves empirical marginals, better tail behavior)

# CVaR parameters
ALPHA_CVAR = 0.90  # CVaR confidence level (0.90 = worst 10% tail)

# Trajectory generation parameters
N_TRAJECTORIES = 5_000  # Number of independent trajectories to generate
N_TRAJ = 10_000  # Number of Monte Carlo scenarios for asset returns
HORIZON_MONTHS = 420  # 35 years

# Burn-in parameters for backward trajectory generation
INITIAL_BURN_IN = 25  # Burn-in for the final month (most restrictive)
ADAPTIVE_BURN_IN = 1  # FIXED burn-in when CVaR limit expands (NOT adaptive formula)
PROJECTION_BURN_IN = 5  # Burn-in when projection is needed

# Random seeds (for reproducibility)
RETURNS_SEED = 111  # Seed for simulated returns
TRAJECTORY_SEED = 222  # Seed for trajectory generation (Hit-and-Run)
SCENARIO_SEED = 333  # Seed for scenario selection per month (same for all curves)

# Curve selection
PROCESS_ALL_CURVES = False  # True = process all curves, False = only selected
CURVES_TO_PROCESS = [
    "curve_0001",
    "curve_0108"
]  # Curves to process if PROCESS_ALL_CURVES=False

# Validation
VALIDATE_TRAJECTORIES = True  # Validate all trajectories after generation
VERBOSE_FIRST_TRAJECTORY = True  # Print detailed info for first trajectory

# ========================================
# PARALLELIZATION CONFIGURATION
# ========================================

# Number of parallel processes to use for generating trajectories
# Options:
#   - None or "auto": Uses all available CPU cores minus 1 (recommended)
#   - Integer (e.g., 1, 4, 8): Uses exactly that many processes
#   - 1: Disables parallelization (sequential trajectory generation)

N_PROCESSES = 15  # <-- CHANGE THIS TO MATCH YOUR COMPUTER

# ========================================
# VALIDATION
# ========================================

assert SIMULATION_METHOD.lower() in [
    "mvn",
    "copula",
], "SIMULATION_METHOD must be 'mvn' or 'copula'."
assert 0 < ALPHA_CVAR < 1, "ALPHA_CVAR must be in (0,1)."
assert N_TRAJECTORIES >= 1, "N_TRAJECTORIES must be >= 1."
assert N_TRAJ >= 100, "Use at least 100 scenarios for stable results."

# Validate N_PROCESSES
if N_PROCESSES is not None and N_PROCESSES != "auto":
    assert isinstance(N_PROCESSES, int) and N_PROCESSES >= 1, \
        "N_PROCESSES must be 'auto', None, or a positive integer"


# ========================================
# HELPER FUNCTION FOR PARALLEL PROCESSING
# ========================================

def process_single_trajectory(args):
    """
    Generate a single trajectory (to be called in parallel).
    
    Parameters:
    -----------
    args : tuple
        (traj_idx, cvar_limits, returns_matrix, confidence_level, 
         trajectory_seed, burn_in_params, verbose)
    
    Returns:
    --------
    tuple : (traj_idx, trajectory, stats, violations, success, error_msg)
    """
    (traj_idx, cvar_limits, returns_matrix, confidence_level, 
     trajectory_seed, burn_in_params, validate, verbose) = args
    
    try:
        # Set seed for this trajectory
        np.random.seed(trajectory_seed)
        
        # Generate trajectory backward
        trajectory, stats = generate_single_trajectory_backward(
            cvar_limits=cvar_limits,
            returns_matrix=returns_matrix,
            confidence_level=confidence_level,
            initial_burn_in=burn_in_params['initial'],
            adaptive_base_burn_in=burn_in_params['adaptive_base'],
            adaptive_max_burn_in=burn_in_params['adaptive_max'],
            projection_burn_in=burn_in_params['projection'],
            verbose=verbose
        )
        
        # Validate if requested
        violations = []
        if validate:
            violations = validate_trajectory(
                trajectory=trajectory,
                cvar_limits=cvar_limits,
                returns_matrix=returns_matrix,
                confidence_level=confidence_level
            )
        
        return (traj_idx, trajectory, stats, violations, True, None)
        
    except Exception as e:
        return (traj_idx, None, None, None, False, str(e))


# ========================================
# MAIN FUNCTION
# ========================================

def main() -> None:
    """
    Generate portfolio trajectories using backward Hit-and-Run algorithm.
    
    NEW APPROACH:
    - Generates complete trajectories from last month to first month
    - Each trajectory is independent and maintains temporal continuity
    - Uses adaptive burn-in based on CVaR limit changes
    - Handles infeasible points via projection
    
    For each CVaR glidepath curve:
      1. Generate N independent trajectories using backward algorithm
      2. Each trajectory consists of one portfolio per month
      3. Portfolios satisfy CVaR constraints and evolve coherently
      4. Export returns matrix to Excel
    """
    
    # Determine number of processes to use
    if N_PROCESSES is None or N_PROCESSES == "auto":
        n_processes = max(1, cpu_count() - 1)  # Leave 1 core free
    else:
        n_processes = N_PROCESSES
    
    print("=" * 70)
    print("PORTFOLIO TRAJECTORY GENERATOR - BACKWARD HIT-AND-RUN")
    print("=" * 70)
    print(f"Simulation method: {SIMULATION_METHOD.upper()}")
    print(f"CVaR Level: {ALPHA_CVAR*100:.0f}%")
    print(f"Trajectories to generate: {N_TRAJECTORIES:,}")
    print(f"Monte Carlo scenarios: {N_TRAJ:,}")
    print(f"Horizon: {HORIZON_MONTHS} months")
    print(f"Parallel processes: {n_processes}")
    print()
    print("BURN-IN CONFIGURATION:")
    print(f"  Initial (final month): {INITIAL_BURN_IN}")
    print(f"  When CVaR expands (FIXED): {ADAPTIVE_BURN_IN}")
    print(f"  Projection: {PROJECTION_BURN_IN}")
    print()
    print("TRAJECTORY GENERATION STRATEGY:")
    print("  ✓ Backward generation (from last month to first)")
    print("  ✓ Temporal continuity maintained")
    print("  ✓ Adaptive burn-in based on CVaR expansion")
    print("  ✓ Automatic projection for infeasible points")
    print("=" * 70)

    # ----------------------------------------
    # 1. Load historical returns
    # ----------------------------------------
    print("\n[1/6] Loading historical returns...")
    R_hist_df = pd.read_csv(input_returns_path(), index_col=0)
    R_historical = R_hist_df.values
    n_assets = R_historical.shape[1]
    print(f"   Loaded {R_historical.shape[0]} periods, {n_assets} assets")
    print(f"   Asset names: {list(R_hist_df.columns)}")

    # ----------------------------------------
    # 2. Estimate parameters for MVN
    # ----------------------------------------
    print("\n[2/6] Estimating asset return parameters...")
    mu_hat = np.mean(R_historical, axis=0)
    Sigma_hat = np.cov(R_historical, rowvar=False)
    Sigma_psd = f_make_psd(Sigma_hat, eps=1e-12)
    print(f"   Mean returns: {mu_hat}")
    print(f"   Covariance matrix: {Sigma_psd.shape}")

    # ----------------------------------------
    # 3. Simulate asset returns
    # ----------------------------------------
    print(f"\n[3/6] Simulating asset returns ({SIMULATION_METHOD.upper()})...")
    rng = np.random.default_rng(RETURNS_SEED)
    
    samples = simulate_asset_returns(
        mu=mu_hat,
        Sigma_psd=Sigma_psd,
        R_historical=R_historical,
        horizon_months=HORIZON_MONTHS,
        n_traj=N_TRAJ,
        rng=rng,
        method=SIMULATION_METHOD,
    )
    
    print(f"   Generated returns shape: {samples.shape}")
    print(f"     = (months={HORIZON_MONTHS}, scenarios={N_TRAJ}, assets={n_assets})")
    
    if SIMULATION_METHOD.lower() == "copula":
        print(f"   ✓ Using Gaussian Copula (preserves empirical marginals)")
    else:
        print(f"   ✓ Using Multivariate Normal")

    # ----------------------------------------
    # 4. Load CVaR glidepath curves
    # ----------------------------------------
    print("\n[4/6] Loading CVaR glidepath curves...")
    params_df, glides_df = load_glidepaths_universe(input_glidepaths_path())
    all_curves = glides_df.columns.tolist()
    print(f"   Total curves available: {len(all_curves)}")

    # Select which curves to process
    if PROCESS_ALL_CURVES:
        curves_to_process = all_curves
        print(f"   Processing ALL curves")
    else:
        curves_to_process = [c for c in CURVES_TO_PROCESS if c in all_curves]
        if len(curves_to_process) == 0:
            raise ValueError("No valid curves selected!")
        print(f"   Processing {len(curves_to_process)} selected curves:")
        for c in curves_to_process:
            print(f"      - {c}")

    # ----------------------------------------
    # 4b. Generate scenario selection (SAME for all curves)
    # ----------------------------------------
    print("\n[4b/6] Generating scenario selection...")
    print(f"   All curves will face the SAME sequence of market scenarios")
    scenario_rng = np.random.default_rng(SCENARIO_SEED)
    scenario_indices = scenario_rng.integers(0, N_TRAJ, size=HORIZON_MONTHS)
    print(f"   Generated {HORIZON_MONTHS} scenario indices (one per month)")
    print(f"   Range: 0 to {N_TRAJ - 1}")
    print(f"   First 10 scenarios: {scenario_indices[:10].tolist()}")
    print(f"   Last 10 scenarios: {scenario_indices[-10:].tolist()}")

    # ----------------------------------------
    # 5. Create output directory
    # ----------------------------------------
    print("\n[5/6] Setting up output directory...")
    output_dir = output_hit_run_dir()
    os.makedirs(output_dir, exist_ok=True)
    print(f"   Output directory: {output_dir}")

    # ----------------------------------------
    # 6. Process each curve
    # ----------------------------------------
    print("\n[6/6] Generating trajectories with backward Hit-and-Run...")
    print("-" * 70)
    
    # Prepare confidence level
    confidence_level = 1.0 - ALPHA_CVAR
    
    # Burn-in parameters
    burn_in_params = {
        'initial': INITIAL_BURN_IN,
        'adaptive_base': ADAPTIVE_BURN_IN,  # Fixed value, not adaptive formula
        'adaptive_max': ADAPTIVE_BURN_IN,   # Same as base (kept for compatibility)
        'projection': PROJECTION_BURN_IN
    }

    # Track timing for estimation
    start_time = time.time()
    
    # Process each curve
    for curve_idx, curve_name in enumerate(curves_to_process, 1):
        curve_start_time = time.time()
        print(f"\nProcessing {curve_name} ({curve_idx}/{len(curves_to_process)})...")

        # Get CVaR limits for this curve
        cvar_limits = glides_df[curve_name].values
        
        print(f"   CVaR limits: min={cvar_limits.min():.4f}, max={cvar_limits.max():.4f}")
        print(f"   First month limit: {cvar_limits[0]:.4f}")
        print(f"   Last month limit: {cvar_limits[-1]:.4f}")

        # Get absolute curve index for reproducible seed generation
        absolute_curve_idx = all_curves.index(curve_name)
        
        # Create RNG for this specific curve
        curve_rng = np.random.default_rng(TRAJECTORY_SEED + absolute_curve_idx)
        
        # Prepare arguments for each trajectory
        trajectory_args = []
        for traj_idx in range(N_TRAJECTORIES):
            # Generate unique seed for this trajectory
            trajectory_seed = curve_rng.integers(0, 2**31 - 1)
            
            # Verbose only for first trajectory if requested
            verbose = VERBOSE_FIRST_TRAJECTORY and traj_idx == 0
            
            trajectory_args.append((
                traj_idx,
                cvar_limits,
                samples,  # All trajectories use same simulated returns
                confidence_level,
                trajectory_seed,
                burn_in_params,
                VALIDATE_TRAJECTORIES,
                verbose
            ))
        
        # Process trajectories
        if n_processes == 1:
            # Sequential processing
            print(f"   Generating {N_TRAJECTORIES:,} trajectories sequentially...")
            results = []
            for i, args in enumerate(trajectory_args):
                if (i + 1) % 1000 == 0 or i == 0:
                    print(f"     Trajectory {i+1}/{N_TRAJECTORIES} ({(i+1)/N_TRAJECTORIES*100:.1f}%)")
                result = process_single_trajectory(args)
                results.append(result)
        else:
            # Parallel processing
            print(f"   Generating {N_TRAJECTORIES:,} trajectories in parallel ({n_processes} at a time)...")
            
            with Pool(processes=n_processes) as pool:
                results = []
                completed = 0
                for result in pool.imap_unordered(process_single_trajectory, trajectory_args, chunksize=10):
                    results.append(result)
                    completed += 1
                    
                    # Show progress
                    if completed % 500 == 0 or completed == N_TRAJECTORIES:
                        print(f"     Completed {completed:,}/{N_TRAJECTORIES:,} trajectories ({completed/N_TRAJECTORIES*100:.1f}%)")
        
        # Collect results
        trajectories = []
        failed_count = 0
        total_projections = 0
        total_burn_in = 0
        all_violations = []
        
        for traj_idx, trajectory, stats, violations, success, error_msg in results:
            if not success:
                failed_count += 1
                if failed_count <= 3:
                    print(f"   Warning: Trajectory {traj_idx} failed: {error_msg}")
                continue
            
            trajectories.append(trajectory)
            
            if stats:
                total_projections += stats['projected_count']
                total_burn_in += stats['total_burn_in']
            
            if violations:
                all_violations.extend([(traj_idx, v) for v in violations])
        
        if failed_count > 3:
            print(f"   Warning: {failed_count - 3} additional trajectories failed (not shown)")
        
        # Convert to numpy array
        trajectories = np.array(trajectories)  # Shape: (N_TRAJECTORIES, HORIZON_MONTHS, N_ASSETS)
        
        print(f"\n   Generation statistics:")
        print(f"     Successful trajectories: {len(trajectories):,}/{N_TRAJECTORIES:,}")
        print(f"     Total projections needed: {total_projections:,}")
        print(f"     Avg projections per trajectory: {total_projections/len(trajectories):.2f}")
        print(f"     Total burn-in iterations: {total_burn_in:,}")
        print(f"     Avg burn-in per trajectory: {total_burn_in/len(trajectories):.1f}")
        
        # Validation summary
        if VALIDATE_TRAJECTORIES:
            if all_violations:
                print(f"\n   ⚠️ VALIDATION WARNINGS:")
                print(f"     Total violations: {len(all_violations)}")
                
                # Group by type
                violation_types = {}
                for traj_idx, v in all_violations:
                    v_type = v['type']
                    if v_type not in violation_types:
                        violation_types[v_type] = []
                    violation_types[v_type].append((traj_idx, v))
                
                for v_type, violations_list in violation_types.items():
                    print(f"     {v_type}: {len(violations_list)} violations")
                    # Show first 3 examples
                    for i, (traj_idx, v) in enumerate(violations_list[:3]):
                        print(f"       Trajectory {traj_idx}, Month {v['month']}: {v['message']}")
                    if len(violations_list) > 3:
                        print(f"       ... and {len(violations_list) - 3} more")
            else:
                print(f"\n   ✓ VALIDATION PASSED: All trajectories satisfy constraints")
        
        # Calculate returns for each trajectory
        # For each trajectory, calculate monthly returns using the simulated asset returns
        print(f"\n   Calculating trajectory returns...")
        returns_matrix = np.zeros((HORIZON_MONTHS, len(trajectories)))
        
        # Use the SAME scenario sequence for all curves (already generated globally)
        # scenario_indices was generated once using SCENARIO_SEED before the curve loop
        
        for t in range(HORIZON_MONTHS):
            scenario_idx = scenario_indices[t]
            selected_scenario_returns = samples[t, scenario_idx, :]
            
            for traj_idx in range(len(trajectories)):
                portfolio_weights = trajectories[traj_idx, t, :]
                returns_matrix[t, traj_idx] = portfolio_weights @ selected_scenario_returns
        
        # Export results for this curve
        output_file = output_hit_run_file(curve_name)
        export_curve_results(
            output_file=output_file,
            returns_matrix=returns_matrix,
            n_portfolios=len(trajectories),
        )
        
        curve_elapsed = time.time() - curve_start_time
        print(f"\n   ✓ Completed {curve_name} in {curve_elapsed/60:.1f} minutes")
        print(f"   ✓ Exported to: {output_file}")
        
        # Estimate remaining time
        if curve_idx < len(curves_to_process):
            avg_time_per_curve = (time.time() - start_time) / curve_idx
            remaining_curves = len(curves_to_process) - curve_idx
            est_remaining = avg_time_per_curve * remaining_curves
            print(f"   Estimated time remaining: {est_remaining/60:.1f} minutes")

    # Final summary
    total_elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETED")
    print("=" * 70)
    print(f"Total curves processed: {len(curves_to_process)}")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print(f"Average time per curve: {total_elapsed/len(curves_to_process)/60:.1f} minutes")
    
    if n_processes > 1:
        print(f"\nParallelization info:")
        print(f"  Trajectories processed simultaneously: {n_processes}")
        print(f"  Total trajectory-level tasks: {len(curves_to_process) * N_TRAJECTORIES:,}")
        
    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("  - Trajectories generated using BACKWARD Hit-and-Run algorithm")
    print("  - Each trajectory maintains temporal continuity")
    print("  - Adaptive burn-in based on CVaR limit changes")
    print("  - Automatic projection for infeasible points")
    print("  - CVaR constraints satisfied for every month")
    print(f"  - ALL CURVES face the SAME sequence of {HORIZON_MONTHS} market scenarios")
    print(f"  - Scenario sequence generated with SCENARIO_SEED = {SCENARIO_SEED}")
    print(f"  - Parallel trajectory generation: {n_processes} trajectory(ies) simultaneously")
    print("=" * 70)


if __name__ == "__main__":
    main()
