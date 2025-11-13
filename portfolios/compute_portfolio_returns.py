import numpy as np

def compute_portfolio_returns(
    samples: np.ndarray,  # Shape (T, S, N): T = months, S = scenarios, N = assets
    W: np.ndarray         # Shape (T, N): one weight vector for each month
) -> np.ndarray:
    """
    Compute portfolio returns for each month and each scenario.
    - For each month t and scenario s:
      multiply the asset returns (samples[t, s, :])
      by the portfolio weights (W[t, :]).
    - This is a dot product operation.
    - The result has shape (T, S).
    """
    # Use einsum for fast batched dot products
    return np.einsum('tsn,tn->ts', samples, W)
