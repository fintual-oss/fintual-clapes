import numpy as np

def simulate_asset_returns(
    mu: np.ndarray,
    Sigma_psd: np.ndarray,
    horizon_months: int,
    n_traj: int,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Simulate asset returns with a multivariate normal (MVN).
    - mu: mean returns vector (N,)
    - Sigma_psd: covariance matrix (N x N), PSD
    - horizon_months: number of months (T)
    - n_traj: number of scenarios/paths (S)
    - rng: NumPy random generator
    Returns:
    - samples with shape (T, S, N)
    """
    # Draw MVN samples for each month and each scenario
    samples = rng.multivariate_normal(mean=mu, cov=Sigma_psd, size=(horizon_months, n_traj))
    return samples
