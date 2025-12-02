import os
import numpy as np
import pandas as pd
from pathlib import Path

# Import helper functions
from routes import (
    input_returns_path, 
    input_glidepaths_path,
    output_hit_run_dir, 
    output_hit_run_file
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
N_PORTFOLIOS_PER_MONTH = 10  # Number of portfolios to generate per month
N_TRAJ = 1_000  # Number of Monte Carlo scenarios
HORIZON_MONTHS = 480  # 40 years

# Random seeds (for reproducibility)
RETURNS_SEED = 42  # Seed for simulated returns
HIT_RUN_SEED = 123  # Seed for Hit-and-Run algorithm

# Curve selection
PROCESS_ALL_CURVES = False  # True = process all curves, False = only selected
CURVES_TO_PROCESS = [
    "curve_0001",
    "curve_0002"
]  # Curves to process if PROCESS_ALL_CURVES=False

# Validation
assert SIMULATION_METHOD.lower() in ["mvn", "copula"], "SIMULATION_METHOD must be 'mvn' or 'copula'."
assert 0 < ALPHA_CVAR < 1, "ALPHA_CVAR must be in (0,1)."
assert N_PORTFOLIOS_PER_MONTH >= 1, "N_PORTFOLIOS_PER_MONTH must be >= 1."
assert N_TRAJ >= 100, "Use at least 100 trajectories for stable results."

# ========================================
# MAIN FUNCTION
# ========================================

def main() -> None:
    """
    Generate portfolio trajectories using Hit-and-Run algorithm.
    
    For each CVaR glidepath curve:
      1. For each month t, generate N portfolios where CVaR < CVaR_limit(t)
      2. Build trajectory i by connecting portfolio i from each month
      3. Export CVaR and returns matrices to Excel
    """
    
    print("=" * 70)
    print("PORTFOLIO TRAJECTORY GENERATOR - HIT AND RUN")
    print("=" * 70)
    print(f"Simulation method: {SIMULATION_METHOD.upper()}")
    print(f"CVaR Level: {ALPHA_CVAR*100:.0f}%")
    print(f"Portfolios per month: {N_PORTFOLIOS_PER_MONTH}")
    print(f"Monte Carlo scenarios: {N_TRAJ:,}")
    print(f"Horizon: {HORIZON_MONTHS} months")
    print(f"Returns seed: {RETURNS_SEED}")
    print(f"Hit-and-Run seed: {HIT_RUN_SEED}")
    print("=" * 70)
    
    # ----------------------------------------
    # 1. Load historical returns
    # ----------------------------------------
    print("\n[1/6] Loading historical returns...")
    returns_df = pd.read_csv(
        input_returns_path(), 
        sep=",", 
        parse_dates=[0], 
        index_col=0
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
    print(f"\n[3/6] Simulating future asset returns using {SIMULATION_METHOD.upper()}...")
    rng_returns = np.random.default_rng(RETURNS_SEED)
    samples = simulate_asset_returns(
        mu=mu,
        Sigma_psd=Sigma_psd,
        R_historical=R,
        horizon_months=HORIZON_MONTHS,
        n_traj=N_TRAJ,
        rng=rng_returns,
        method=SIMULATION_METHOD
    )
    print(f"   Simulated returns shape: {samples.shape}")
    print(f"   (months × scenarios × assets)")
    
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
    # 5. Create output directory
    # ----------------------------------------
    print("\n[5/6] Setting up output directory...")
    output_dir = output_hit_run_dir()
    os.makedirs(output_dir, exist_ok=True)
    print(f"   Output directory: {output_dir}")
    
    # ----------------------------------------
    # 6. Process each curve
    # ----------------------------------------
    print("\n[6/6] Generating portfolios with Hit-and-Run...")
    print("-" * 70)
    
    # Initialize master random generator for Hit-and-Run seeds
    rng_master = np.random.default_rng(HIT_RUN_SEED)
    
    for curve_idx, curve_name in enumerate(curves_to_process, 1):
        print(f"\n[Curve {curve_idx}/{len(curves_to_process)}] {curve_name}")
        
        # Get CVaR limits for this curve (vector of length 360)
        cvar_limits = glides_df[curve_name].values
        
        # Storage for results
        cvar_matrix = np.zeros((HORIZON_MONTHS, N_PORTFOLIOS_PER_MONTH))
        returns_matrix = np.zeros((HORIZON_MONTHS, N_PORTFOLIOS_PER_MONTH))
        
        # Process each month
        for t in range(HORIZON_MONTHS):
            if (t + 1) % 50 == 0 or t == 0:
                print(f"   Month {t+1}/{HORIZON_MONTHS}...", end=" ", flush=True)
            
            # Get simulated returns for this month (shape: N_TRAJ × N_ASSETS)
            month_returns = samples[t, :, :]  # (10000, 9)
            
            # CVaR limit for this month
            target_cvar = cvar_limits[t]
            
            # Create Hit-and-Run sampler for this month
            # confidence_level for CVaR: if ALPHA=0.90, we look at worst 10%
            # so confidence_level = 1 - ALPHA = 0.10
            confidence_level = 1.0 - ALPHA_CVAR
            sampler = CVaRPortfolioSampler(
                returns=month_returns,
                confidence_level=confidence_level
            )
            
            # Generate seed for this month's Hit-and-Run
            month_seed = rng_master.integers(0, 2**31 - 1)
            np.random.seed(month_seed)  # Set seed for Hit-and-Run
            
            try:
                # Generate N portfolios satisfying CVaR < target_cvar
                portfolios = sampler.generate_portfolios(
                    target_cvar=target_cvar,
                    n_samples=N_PORTFOLIOS_PER_MONTH,
                    burn_in=50
                )
                
                # For each portfolio, compute CVaR and average return
                for p_idx in range(N_PORTFOLIOS_PER_MONTH):
                    weights = portfolios[p_idx, :]
                    
                    # Portfolio returns for this month (10000 scenarios)
                    port_returns = month_returns @ weights
                    
                    # CVaR (should be < target_cvar by construction)
                    cvar_val = sampler.calculate_cvar(weights)
                    
                    # Average return
                    avg_return = np.mean(port_returns)
                    
                    # Store results
                    cvar_matrix[t, p_idx] = cvar_val
                    returns_matrix[t, p_idx] = avg_return
                
                if (t + 1) % 50 == 0 or t == 0:
                    print("✓")
                    
            except Exception as e:
                print(f"\n   ERROR at month {t+1}: {e}")
                print(f"   Target CVaR: {target_cvar:.6f}")
                # Fill with NaN for this month
                cvar_matrix[t, :] = np.nan
                returns_matrix[t, :] = np.nan
        
        # Export results for this curve
        output_file = output_hit_run_file(curve_name)
        export_curve_results(
            output_file=output_file,
            cvar_matrix=cvar_matrix,
            returns_matrix=returns_matrix,
            n_portfolios=N_PORTFOLIOS_PER_MONTH
        )
        print(f"   ✓ Saved: {output_file}")
    
    print("\n" + "=" * 70)
    print("COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()