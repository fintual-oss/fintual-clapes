import numpy as np
from scipy.stats import norm

def simulate_asset_returns_mvn(
    mu: np.ndarray,
    Sigma_psd: np.ndarray,
    horizon_months: int,
    n_traj: int,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Simulate asset returns using Multivariate Normal (MVN).
    
    Parameters:
    -----------
    mu : np.ndarray
        Mean returns vector (N,)
    Sigma_psd : np.ndarray
        Covariance matrix (N x N), PSD
    horizon_months : int
        Number of months (T)
    n_traj : int
        Number of scenarios/paths (S)
    rng : np.random.Generator
        NumPy random generator
    
    Returns:
    --------
    samples : np.ndarray
        Simulated returns with shape (T, S, N)
    """
    # Draw MVN samples for each month and each scenario
    samples = rng.multivariate_normal(mean=mu, cov=Sigma_psd, size=(horizon_months, n_traj))
    return samples


def simulate_asset_returns_copula(
    R_historical: np.ndarray,
    horizon_months: int,
    n_traj: int,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Simulate asset returns using Gaussian Copula.
    
    This method:
    1. Preserves empirical marginal distributions of each asset
    2. Models dependence structure via Gaussian copula
    3. Captures tail behavior and asymmetries better than MVN
    
    Parameters:
    -----------
    R_historical : np.ndarray
        Historical returns matrix (T_hist x N)
    horizon_months : int
        Number of months to simulate (T)
    n_traj : int
        Number of scenarios/paths (S)
    rng : np.random.Generator
        NumPy random generator
    
    Returns:
    --------
    samples : np.ndarray
        Simulated returns with shape (T, S, N)
    """
    T_hist, N_assets = R_historical.shape
    
    # Step 1: Convert historical returns to uniform [0,1] via empirical CDF
    U_historical = np.zeros_like(R_historical)
    for j in range(N_assets):
        U_historical[:, j] = _ranks_to_uniforms(R_historical[:, j])
    
    # Step 2: Transform uniforms to Gaussian space to estimate correlation
    Z_historical = norm.ppf(U_historical)
    
    # Step 3: Estimate Gaussian copula correlation matrix
    corr_copula = np.corrcoef(Z_historical, rowvar=False)
    # Make symmetric and ensure PSD
    corr_copula = (corr_copula + corr_copula.T) / 2.0
    
    # Step 4: For each month, simulate from Gaussian copula
    samples = np.zeros((horizon_months, n_traj, N_assets))
    
    for t in range(horizon_months):
        # Generate correlated Gaussian random variables
        Z_sim = rng.multivariate_normal(
            mean=np.zeros(N_assets),
            cov=corr_copula,
            size=n_traj
        )
        
        # Transform to uniform [0,1]
        U_sim = norm.cdf(Z_sim)
        
        # Transform uniforms to returns using empirical inverse CDF
        for j in range(N_assets):
            samples[t, :, j] = _empirical_inverse_cdf(
                R_historical[:, j],
                U_sim[:, j]
            )
    
    return samples


def _ranks_to_uniforms(x: np.ndarray) -> np.ndarray:
    """
    Convert data to uniform [0,1] via empirical CDF (rank-based).
    
    Parameters:
    -----------
    x : np.ndarray
        1D array of observations
    
    Returns:
    --------
    u : np.ndarray
        Uniform [0,1] values
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    
    # Ranks: 1, 2, ..., n
    ranks = x.argsort().argsort().astype(float) + 1.0
    
    # Convert to uniform using (rank - 0.5) / n
    u = (ranks - 0.5) / n
    
    return u


def _empirical_inverse_cdf(sample: np.ndarray, u: np.ndarray) -> np.ndarray:
    """
    Transform uniform [0,1] values to original scale using empirical inverse CDF.
    
    Parameters:
    -----------
    sample : np.ndarray
        Historical sample (e.g., returns of one asset)
    u : np.ndarray
        Uniform [0,1] values
    
    Returns:
    --------
    x : np.ndarray
        Values in original scale
    """
    # Sort historical sample
    x_sorted = np.sort(np.asarray(sample, dtype=float))
    n = x_sorted.size
    
    # Empirical CDF positions
    q_positions = (np.arange(1, n + 1) - 0.5) / n
    
    # Clip u to be within range
    u = np.clip(u, q_positions[0], q_positions[-1])
    
    # Linear interpolation
    return np.interp(u, q_positions, x_sorted)


def simulate_asset_returns(
    mu: np.ndarray,
    Sigma_psd: np.ndarray,
    R_historical: np.ndarray,
    horizon_months: int,
    n_traj: int,
    rng: np.random.Generator,
    method: str = "mvn"
) -> np.ndarray:
    """
    Simulate asset returns using specified method.
    
    Parameters:
    -----------
    mu : np.ndarray
        Mean returns vector (N,) - used for MVN method
    Sigma_psd : np.ndarray
        Covariance matrix (N x N), PSD - used for MVN method
    R_historical : np.ndarray
        Historical returns matrix (T_hist x N) - used for Copula method
    horizon_months : int
        Number of months (T)
    n_traj : int
        Number of scenarios/paths (S)
    rng : np.random.Generator
        NumPy random generator
    method : str, default="mvn"
        Simulation method: "mvn" or "copula"
    
    Returns:
    --------
    samples : np.ndarray
        Simulated returns with shape (T, S, N)
    """
    if method.lower() == "mvn":
        return simulate_asset_returns_mvn(
            mu=mu,
            Sigma_psd=Sigma_psd,
            horizon_months=horizon_months,
            n_traj=n_traj,
            rng=rng
        )
    elif method.lower() == "copula":
        return simulate_asset_returns_copula(
            R_historical=R_historical,
            horizon_months=horizon_months,
            n_traj=n_traj,
            rng=rng
        )
    else:
        raise ValueError(f"Unknown method: {method}. Use 'mvn' or 'copula'.")