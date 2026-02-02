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
from cvar_portfolio_sampler import CVaRPortfolioSampler
from loaders import load_glidepaths_universe
from exporters import export_curve_results

# ========================================
# CONFIGURATION - EDIT THESE PARAMETERS
# ========================================

# Simulation method
SIMULATION_METHOD = "copula"  # "mvn" or "copula"
# - "mvn": Multivariate Normal (faster, assumes Gaussian distribution)
# - "copula": Gaussian Copula (slower, preserves empirical marginals, better tail behavior)

# CVaR parameters
ALPHA_CVAR = 0.90  # CVaR confidence level (0.90 = worst 10% tail)

# Portfolio generation
N_PORTFOLIOS_PER_MONTH = 10_000  # Number of portfolios to generate per month
N_TRAJ = 10_000  # Number of Monte Carlo scenarios
HORIZON_MONTHS = 420  # 40 years

# Scenario selection mode
USE_RANDOM_SCENARIOS = False  # True = each portfolio uses different scenario (full randomness)
                              # False = all portfolios in a month use same scenario (current behavior)

# Random seeds (for reproducibility)
RETURNS_SEED = 111  # Seed for simulated returns
HIT_RUN_SEED = 222  # Seed for Hit-and-Run algorithm
SCENARIO_SEED = 333  # Seed for scenario selection per month (used when USE_RANDOM_SCENARIOS=False)
RANDOM_SCENARIO_SEED = 444  # Seed for random scenario assignment (used when USE_RANDOM_SCENARIOS=True)

# Curve selection
PROCESS_ALL_CURVES = True  # True = process all curves, False = only selected
CURVES_TO_PROCESS = [
    "curve_0001",
    "curve_0002"
]  # Curves to process if PROCESS_ALL_CURVES=False

# ========================================
# PARALLELIZATION CONFIGURATION
# ========================================

# Number of parallel processes to use for processing months within each curve
# Options:
#   - None or "auto": Uses all available CPU cores minus 1 (recommended)
#   - Integer (e.g., 1, 4, 8): Uses exactly that many processes
#   - 1: Disables parallelization (sequential month processing)
#
# Memory consideration:
#   - Each process loads month_returns (N_TRAJ × N_ASSETS)
#   - More processes = more memory needed
#   - Generally safe with "auto" for typical workloads

N_PROCESSES = 15  # <-- CHANGE THIS TO MATCH YOUR COMPUTER

# ========================================
# VALIDATION
# ========================================

assert SIMULATION_METHOD.lower() in [
    "mvn",
    "copula",
], "SIMULATION_METHOD must be 'mvn' or 'copula'."
assert 0 < ALPHA_CVAR < 1, "ALPHA_CVAR must be in (0,1)."
assert N_PORTFOLIOS_PER_MONTH >= 1, "N_PORTFOLIOS_PER_MONTH must be >= 1."
assert N_TRAJ >= 100, "Use at least 100 trajectories for stable results."

# Validate N_PROCESSES
if N_PROCESSES is not None and N_PROCESSES != "auto":
    assert isinstance(N_PROCESSES, int) and N_PROCESSES >= 1, \
        "N_PROCESSES must be 'auto', None, or a positive integer"


# ========================================
# HELPER FUNCTION FOR PARALLEL PROCESSING
# ========================================

def process_single_month(args):
    """
    Process a single month (to be called in parallel).
    
    Parameters:
    -----------
    args : tuple
        (t, month_returns, target_cvar, scenario_idx, confidence_level, 
         month_seed, N_PORTFOLIOS_PER_MONTH, use_random_scenarios, random_scenario_seed)
    
    Returns:
    --------
    tuple : (t, portfolio_returns, success, error_msg)
        - t: month index
        - portfolio_returns: array of returns for this month
        - success: boolean indicating if processing succeeded
        - error_msg: error message if failed, None otherwise
    """
    (t, month_returns, target_cvar, scenario_idx, confidence_level, 
     month_seed, N_PORTFOLIOS_PER_MONTH, use_random_scenarios, random_scenario_seed) = args
    
    try:
        # Create Hit-and-Run sampler for this month
        sampler = CVaRPortfolioSampler(
            returns=month_returns, confidence_level=confidence_level
        )
        
        # Set seed for Hit-and-Run
        np.random.seed(month_seed)
        
        # Generate N portfolios satisfying CVaR < target_cvar
        portfolios = sampler.generate_portfolios_batch(
            target_cvar=target_cvar,
            n_samples=N_PORTFOLIOS_PER_MONTH,
            burn_in=20,
        )
        
        # Calculate returns based on scenario selection mode
        portfolio_returns = np.full(N_PORTFOLIOS_PER_MONTH, np.nan)
        
        if len(portfolios) < N_PORTFOLIOS_PER_MONTH:
            n_generated = len(portfolios)
            if n_generated == 0:
                return (t, portfolio_returns, True, None)
        else:
            n_generated = N_PORTFOLIOS_PER_MONTH
        
        if use_random_scenarios:
            # MODE: Random scenarios - each portfolio uses different scenario
            # Create RNG specific to this month for reproducibility
            month_rng = np.random.default_rng(random_scenario_seed)
            n_scenarios = month_returns.shape[0]
            
            # Generate random scenario index for each portfolio
            random_scenario_indices = month_rng.integers(0, n_scenarios, size=n_generated)
            
            # Calculate return for each portfolio using its own scenario
            for i in range(n_generated):
                scenario_idx_i = random_scenario_indices[i]
                selected_scenario_returns = month_returns[scenario_idx_i, :]
                portfolio_returns[i] = portfolios[i] @ selected_scenario_returns
        else:
            # MODE: Single scenario - all portfolios use same scenario
            selected_scenario_returns = month_returns[scenario_idx, :]
            portfolio_returns[:n_generated] = portfolios[:n_generated] @ selected_scenario_returns
        
        return (t, portfolio_returns, True, None)
        
    except Exception as e:
        return (t, np.full(N_PORTFOLIOS_PER_MONTH, np.nan), False, str(e))


# ========================================
# MAIN FUNCTION
# ========================================

def main() -> None:
    """
    Generate portfolio trajectories using Hit-and-Run algorithm.
    
    PARALLELIZATION:
    - Processes each curve sequentially (one at a time)
    - Within each curve, processes multiple months simultaneously
    - This is efficient because months are independent within a curve
    
    For each CVaR glidepath curve:
      1. For each month t (IN PARALLEL), generate N portfolios where CVaR < CVaR_limit(t)
      2. Build trajectory i by connecting portfolio i from each month
      3. Export returns matrix to Excel
    """
    
    # Determine number of processes to use
    if N_PROCESSES is None or N_PROCESSES == "auto":
        n_processes = max(1, cpu_count() - 1)  # Leave 1 core free
    else:
        n_processes = N_PROCESSES
    
    print("=" * 70)
    print("PORTFOLIO TRAJECTORY GENERATOR - HIT AND RUN (PARALLEL MONTHS)")
    print("=" * 70)
    print(f"Simulation method: {SIMULATION_METHOD.upper()}")
    print(f"CVaR Level: {ALPHA_CVAR*100:.0f}%")
    print(f"Portfolios per month: {N_PORTFOLIOS_PER_MONTH}")
    print(f"Monte Carlo scenarios: {N_TRAJ:,}")
    print(f"Horizon: {HORIZON_MONTHS} months")
    print(f"Returns seed: {RETURNS_SEED}")
    print(f"Hit-and-Run seed: {HIT_RUN_SEED}")
    if USE_RANDOM_SCENARIOS:
        print(f"Scenario mode: RANDOM (each portfolio uses different scenario)")
        print(f"Random scenario seed: {RANDOM_SCENARIO_SEED}")
    else:
        print(f"Scenario mode: FIXED (all portfolios in month use same scenario)")
        print(f"Scenario selection seed: {SCENARIO_SEED}")
    print("-" * 70)
    print(f"PARALLELIZATION:")
    print(f"  Available CPU cores: {cpu_count()}")
    print(f"  Processes to use: {n_processes}")
    if n_processes == 1:
        print(f"  Mode: SEQUENTIAL (no parallelization)")
    else:
        print(f"  Mode: PARALLEL ({n_processes} months simultaneously per curve)")
        print(f"  Strategy: Process curves sequentially, months in parallel")
    print("=" * 70)

    # ----------------------------------------
    # 1. Load historical returns
    # ----------------------------------------
    print("\n[1/6] Loading historical returns...")
    returns_df = pd.read_csv(
        input_returns_path(), sep=";", parse_dates=[0], index_col=0
    )

    assert returns_df.shape[1] >= 2, "At least two assets are required."
    R = returns_df.to_numpy(dtype=float)
    n_assets = R.shape[1]
    asset_names = returns_df.columns.tolist()
    print(f"   Loaded {R.shape[0]} periods × {n_assets} assets")
    print(f"   Assets: {', '.join(asset_names)}")

    # ----------------------------------------
    # 2. Estimate mean and covariance, make PSD
    # ----------------------------------------
    print("\n[2/6] Estimating parameters...")
    mu = np.nanmean(R, axis=0)
    Sigma = np.cov(R, rowvar=False, ddof=1)
    Sigma_psd = f_make_psd(Sigma, eps=1e-12)
    print(f"   Mean returns (monthly): {mu}")
    print(f"   Covariance matrix: {Sigma_psd.shape}")

    # ----------------------------------------
    # 3. Simulate future asset returns
    # ----------------------------------------
    print(
        f"\n[3/6] Simulating future asset returns using {SIMULATION_METHOD.upper()}..."
    )
    rng_returns = np.random.default_rng(RETURNS_SEED)
    samples = simulate_asset_returns(
        mu=mu,
        Sigma_psd=Sigma_psd,
        R_historical=R,
        horizon_months=HORIZON_MONTHS,
        n_traj=N_TRAJ,
        rng=rng_returns,
        method=SIMULATION_METHOD,
    )
    print(f"   Simulated returns shape: {samples.shape}")
    print(f"   (months × scenarios × assets)")

    if SIMULATION_METHOD.lower() == "copula":
        print(f"   ✓ Using Gaussian Copula (preserves empirical marginals)")
    else:
        print(f"   ✓ Using Multivariate Normal")

    # ----------------------------------------
    # 3b. Generate scenario selection (only for fixed scenario mode)
    # ----------------------------------------
    if USE_RANDOM_SCENARIOS:
        print(f"\n[3b/6] Scenario mode: RANDOM")
        print(f"   Each portfolio will use a different randomly selected scenario")
        print(f"   Scenarios will differ between curves (using curve-specific seeds)")
        scenario_indices = None  # Not needed in random mode
    else:
        print(f"\n[3b/6] Scenario mode: FIXED - Generating scenario selection...")
        rng_scenario = np.random.default_rng(SCENARIO_SEED)
        scenario_indices = rng_scenario.integers(0, N_TRAJ, size=HORIZON_MONTHS)
        
        print(f"   Generated {HORIZON_MONTHS} random scenario indices")
        print(f"   Range: 0 to {N_TRAJ - 1}")
        print(f"   First 10 indices: {scenario_indices[:10].tolist()}")
        print(f"   Note: All portfolios in month t use the same scenario index")

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
    # 5. Create output directory
    # ----------------------------------------
    print("\n[5/6] Setting up output directory...")
    output_dir = output_hit_run_dir()
    os.makedirs(output_dir, exist_ok=True)
    print(f"   Output directory: {output_dir}")

    # ----------------------------------------
    # 6. Process each curve (months in parallel)
    # ----------------------------------------
    print("\n[6/6] Generating portfolios with Hit-and-Run...")
    print("-" * 70)
    
    # Prepare confidence level
    confidence_level = 1.0 - ALPHA_CVAR

    # Track timing for estimation
    start_time = time.time()
    
    # Process each curve
    for curve_idx, curve_name in enumerate(curves_to_process, 1):
        curve_start_time = time.time()
        print(f"\nProcessing {curve_name} ({curve_idx}/{len(curves_to_process)})...")

        # Get CVaR limits for this curve
        cvar_limits = glides_df[curve_name].values

        # Storage for results
        returns_matrix = np.zeros((HORIZON_MONTHS, N_PORTFOLIOS_PER_MONTH))
        
        # Get absolute curve index for reproducible seed generation
        # This ensures same seeds regardless of which curves are processed
        absolute_curve_idx = all_curves.index(curve_name)
        
        # Create RNG for this specific curve (reproducible based on absolute position)
        curve_rng = np.random.default_rng(HIT_RUN_SEED + absolute_curve_idx)
        
        # Prepare arguments for each month
        month_args = []
        for t in range(HORIZON_MONTHS):
            month_returns = samples[t, :, :]
            target_cvar = cvar_limits[t]
            
            # Get scenario index (only used if USE_RANDOM_SCENARIOS=False)
            scenario_idx = scenario_indices[t] if scenario_indices is not None else 0
            
            # Generate seed for Hit-and-Run
            month_seed = curve_rng.integers(0, 2**31 - 1)
            
            # Generate seed for random scenario selection (only used if USE_RANDOM_SCENARIOS=True)
            # This ensures different curves get different random scenarios
            random_scenario_seed = RANDOM_SCENARIO_SEED + absolute_curve_idx * HORIZON_MONTHS + t
            
            month_args.append((
                t,
                month_returns,
                target_cvar,
                scenario_idx,
                confidence_level,
                month_seed,
                N_PORTFOLIOS_PER_MONTH,
                USE_RANDOM_SCENARIOS,
                random_scenario_seed
            ))
        
        # Process months
        if n_processes == 1:
            # Sequential processing
            print(f"   Processing {HORIZON_MONTHS} months sequentially...")
            results = []
            for i, args in enumerate(month_args):
                if (i + 1) % 100 == 0:
                    print(f"     Month {i+1}/{HORIZON_MONTHS} ({(i+1)/HORIZON_MONTHS*100:.1f}%)")
                result = process_single_month(args)
                results.append(result)
        else:
            # Parallel processing
            print(f"   Processing {HORIZON_MONTHS} months in parallel ({n_processes} at a time)...")
            
            with Pool(processes=n_processes) as pool:
                # Use imap_unordered for better performance
                results = []
                completed = 0
                for result in pool.imap_unordered(process_single_month, month_args, chunksize=5):
                    results.append(result)
                    completed += 1
                    
                    # Show progress every 50 months
                    if completed % 50 == 0 or completed == HORIZON_MONTHS:
                        print(f"     Completed {completed}/{HORIZON_MONTHS} months ({completed/HORIZON_MONTHS*100:.1f}%)")
        
        # Collect results into returns_matrix
        failed_months = 0
        for t, portfolio_returns, success, error_msg in results:
            returns_matrix[t, :] = portfolio_returns
            if not success:
                failed_months += 1
                if failed_months <= 5:  # Only show first 5 errors
                    print(f"   Warning: Month {t+1} failed: {error_msg}")
        
        if failed_months > 5:
            print(f"   Warning: {failed_months - 5} additional months failed (not shown)")
        
        # Export results for this curve
        output_file = output_hit_run_file(curve_name)
        export_curve_results(
            output_file=output_file,
            returns_matrix=returns_matrix,
            n_portfolios=N_PORTFOLIOS_PER_MONTH,
        )
        
        curve_elapsed = time.time() - curve_start_time
        print(f"   ✓ Completed {curve_name} in {curve_elapsed/60:.1f} minutes")
        
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
        print(f"  Months processed simultaneously: {n_processes}")
        print(f"  Total month-level tasks: {len(curves_to_process) * HORIZON_MONTHS:,}")
        
    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("  - Portfolios generated using Hit-and-Run algorithm")
    if USE_RANDOM_SCENARIOS:
        print(f"  - RANDOM SCENARIO MODE: Each portfolio uses different scenario")
        print(f"  - Each curve has its own random scenario sequence")
        print(f"  - Total scenario diversity: {N_PORTFOLIOS_PER_MONTH * HORIZON_MONTHS:,} per curve")
    else:
        print(f"  - FIXED SCENARIO MODE: All portfolios in month t use same scenario")
        print(f"  - All curves share the same month-to-month scenario sequence")
    print(f"  - CVaR constraints satisfied during generation (not re-calculated)")
    print(f"  - Parallel month processing: {n_processes} month(s) simultaneously")
    print("=" * 70)


if __name__ == "__main__":
    main()
