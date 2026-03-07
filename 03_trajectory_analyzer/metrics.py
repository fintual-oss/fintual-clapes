import numpy as np
from typing import Dict, List


def calculate_cumulative_return_annualized(
    returns_matrix: np.ndarray
) -> np.ndarray:
    """
    Calculate cumulative annualized return for each trajectory.
    
    Formula:
    1. Cumulative return = Product(1 + monthly_returns) - 1
    2. Annualized return = (1 + cumulative_return)^(12/T) - 1
    
    Parameters:
    -----------
    returns_matrix : np.ndarray
        Monthly returns (T x N) where T=months, N=trajectories
    
    Returns:
    --------
    annualized_returns : np.ndarray
        Annualized cumulative return for each trajectory (N,)
    """
    T, N = returns_matrix.shape
    
    # Calculate cumulative return for each trajectory
    cumulative_returns = np.prod(1 + returns_matrix, axis=0) - 1
    
    # Annualize: (1 + cumulative)^(12/T) - 1
    annualized_returns = np.power(1 + cumulative_returns, 12.0 / T) - 1
    
    return annualized_returns


def calculate_trajectory_statistics(
    annualized_returns: np.ndarray,
    target_return: float
) -> Dict[str, float]:
    """
    Calculate summary statistics for trajectory returns.

    Parameters:
    -----------
    annualized_returns : np.ndarray
        Annualized returns for each trajectory (N,)
    target_return : float
        Target return threshold (e.g., 0.04 for 4%)
    
    Returns:
    --------
    stats : Dict[str, float]
        Dictionary with the following metrics:
        - return_mean: mean annualized return
        - return_std: standard deviation
        - return_min: minimum
        - return_max: maximum
        - pct_above_target: percentage of trajectories above target
    """
    stats = {
        'return_mean': float(np.mean(annualized_returns)),
        'return_std': float(np.std(annualized_returns, ddof=1)),
        'return_min': float(np.min(annualized_returns)),
        'return_max': float(np.max(annualized_returns)),
    }

    # Percentage above target
    n_above = np.sum(annualized_returns > target_return)
    n_total = len(annualized_returns)
    stats['pct_above_target'] = n_above / n_total if n_total > 0 else 0.0

    return stats


def calculate_pct_above_targets(
    annualized_returns: np.ndarray,
    thresholds: List[float]
) -> Dict[str, float]:
    """
    Calculate percentage of trajectories above each target return threshold.

    Parameters:
    -----------
    annualized_returns : np.ndarray
        Annualized returns for each trajectory (N,)
    thresholds : List[float]
        List of target return thresholds (e.g., [0.04, 0.055, 0.07])

    Returns:
    --------
    pct_dict : Dict[str, float]
        Dictionary with keys like 'pct_above_4.00%', 'pct_above_5.50%', etc.
    """
    n_total = len(annualized_returns)
    pct_dict = {}

    for threshold in thresholds:
        n_above = np.sum(annualized_returns > threshold)
        pct = n_above / n_total if n_total > 0 else 0.0
        key = f"pct_above_{threshold * 100:.2f}%"
        pct_dict[key] = float(pct)

    return pct_dict


def calculate_percentiles(
    annualized_returns: np.ndarray,
    percentiles: List[int]
) -> Dict[str, float]:
    """
    Calculate percentiles of annualized returns.

    Parameters:
    -----------
    annualized_returns : np.ndarray
        Annualized returns for each trajectory (N,)
    percentiles : List[int]
        List of percentiles to calculate (e.g., [10, 25, 50, 75, 90])
    
    Returns:
    --------
    percentile_dict : Dict[str, float]
        Dictionary with percentile values:
        - return_p10, return_p25, return_p50, return_p75, return_p90
    """
    percentile_dict = {}
    for p in percentiles:
        value = np.percentile(annualized_returns, p)
        key = f'return_p{p:02d}'
        percentile_dict[key] = float(value)
    return percentile_dict
