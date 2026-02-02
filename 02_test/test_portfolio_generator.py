import numpy as np
import pandas as pd
import sys
import os

# Add parent directory to path to import from 02_portfolio_simulator
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '02_portfolio_simulator'))

from make_psd import f_make_psd
from simulate_asset_returns import simulate_asset_returns
from cvar_portfolio_sampler import CVaRPortfolioSampler

def generate_portfolios_with_weights(
    returns_df: pd.DataFrame,
    cvar_limits: np.ndarray,
    n_portfolios: int,
    n_traj: int,
    horizon_months: int,
    alpha_cvar: float,
    returns_seed: int,
    hit_run_seed: int,
    simulation_method: str = "copula"
) -> np.ndarray:
    """
    Generate portfolio weights using the same logic as step 02.
    
    This function replicates the portfolio generation from 02_portfolio_simulator
    but captures and returns the portfolio weights instead of just returns/CVaR.
    
    Parameters:
    -----------
    returns_df : pd.DataFrame
        Historical returns DataFrame
    cvar_limits : np.ndarray
        CVaR limits for each month (length = horizon_months)
    n_portfolios : int
        Number of portfolios to generate per month
    n_traj : int
        Number of Monte Carlo scenarios
    horizon_months : int
        Investment horizon in months
    alpha_cvar : float
        CVaR confidence level (e.g., 0.90)
    returns_seed : int
        Seed for return simulation
    hit_run_seed : int
        Seed for Hit-and-Run algorithm
    simulation_method : str
        "mvn" or "copula"
    
    Returns:
    --------
    weights_matrix : np.ndarray
        Portfolio weights (HORIZON_MONTHS × N_PORTFOLIOS × N_ASSETS)
    """
    
    # Extract returns data
    R = returns_df.to_numpy(dtype=float)
    n_assets = R.shape[1]
    
    # Estimate parameters
    mu = np.nanmean(R, axis=0)
    Sigma = np.cov(R, rowvar=False, ddof=1)
    Sigma_psd = f_make_psd(Sigma, eps=1e-12)
    
    # Simulate future asset returns
    rng_returns = np.random.default_rng(returns_seed)
    samples = simulate_asset_returns(
        mu=mu,
        Sigma_psd=Sigma_psd,
        R_historical=R,
        horizon_months=horizon_months,
        n_traj=n_traj,
        rng=rng_returns,
        method=simulation_method,
    )
    
    # Initialize weights matrix
    weights_matrix = np.zeros((horizon_months, n_portfolios, n_assets))
    
    # Initialize master random generator for Hit-and-Run seeds
    rng_master = np.random.default_rng(hit_run_seed)
    
    # Process each month
    for t in range(horizon_months):
        # Get simulated returns for this month
        month_returns = samples[t, :, :]  # (N_TRAJ × N_ASSETS)
        
        # CVaR limit for this month
        target_cvar = cvar_limits[t]
        
        # Create Hit-and-Run sampler
        confidence_level = 1.0 - alpha_cvar
        sampler = CVaRPortfolioSampler(
            returns=month_returns,
            confidence_level=confidence_level
        )
        
        # Generate seed for this month's Hit-and-Run
        month_seed = rng_master.integers(0, 2**31 - 1)
        np.random.seed(month_seed)
        
        try:
            # Generate portfolios
            portfolios = sampler.generate_portfolios_batch(
                target_cvar=target_cvar,
                n_samples=n_portfolios,
                burn_in=20,
            )
            
            # Store weights
            if len(portfolios) >= n_portfolios:
                weights_matrix[t, :, :] = portfolios[:n_portfolios, :]
            else:
                # If not enough portfolios generated, fill what we have
                n_generated = len(portfolios)
                weights_matrix[t, :n_generated, :] = portfolios
                # Fill remaining with NaN
                weights_matrix[t, n_generated:, :] = np.nan
                
        except Exception as e:
            print(f"      Warning: Error at month {t+1}: {e}")
            # Fill with NaN
            weights_matrix[t, :, :] = np.nan
    
    return weights_matrix
