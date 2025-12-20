import numpy as np
import pandas as pd
from typing import Dict, List


def calculate_weight_statistics(
    weights_matrix: np.ndarray,
    asset_names: List[str]
) -> Dict[str, pd.DataFrame]:
    """
    Calculate basic statistics for portfolio weights across trajectories.
    
    MODIFIED: Only calculates mean and std (removed min, max, range, percentiles)
    
    Parameters:
    -----------
    weights_matrix : np.ndarray
        Portfolio weights matrix (HORIZON_MONTHS × N_PORTFOLIOS × N_ASSETS)
    asset_names : List[str]
        Names of the assets
    
    Returns:
    --------
    stats : Dict[str, pd.DataFrame]
        Dictionary with DataFrames for each statistic:
        - 'mean': Mean weights per asset (months × assets)
        - 'std': Standard deviation per asset (months × assets)
    """
    n_months, n_portfolios, n_assets = weights_matrix.shape
    
    stats = {}
    
    # Mean weights
    mean_weights = np.mean(weights_matrix, axis=1)  # (months, assets)
    stats['mean'] = pd.DataFrame(
        mean_weights,
        columns=asset_names,
        index=range(1, n_months + 1)
    )
    stats['mean'].index.name = 'Month'
    
    # Standard deviation
    std_weights = np.std(weights_matrix, axis=1, ddof=1)
    stats['std'] = pd.DataFrame(
        std_weights,
        columns=asset_names,
        index=range(1, n_months + 1)
    )
    stats['std'].index.name = 'Month'
    
    return stats


def calculate_hhi_matrix(
    weights_matrix: np.ndarray
) -> pd.DataFrame:
    """
    Calculate HHI (Herfindahl-Hirschman Index) for each portfolio at each month.
    
    HHI = Σ(w_i²) for each portfolio
    
    Parameters:
    -----------
    weights_matrix : np.ndarray
        Portfolio weights matrix (HORIZON_MONTHS × N_PORTFOLIOS × N_ASSETS)
    
    Returns:
    --------
    hhi_df : pd.DataFrame
        DataFrame with HHI values
        Rows: portfolios (1 to N_PORTFOLIOS)
        Columns: months (1 to HORIZON_MONTHS)
        Shape: (N_PORTFOLIOS × HORIZON_MONTHS)
    """
    n_months, n_portfolios, n_assets = weights_matrix.shape
    
    # Calculate HHI for each portfolio at each month
    # HHI = sum of squared weights
    hhi_matrix = np.zeros((n_portfolios, n_months))
    
    for t in range(n_months):
        month_weights = weights_matrix[t, :, :]  # (n_portfolios, n_assets)
        hhi = np.sum(month_weights ** 2, axis=1)  # (n_portfolios,)
        hhi_matrix[:, t] = hhi
    
    # Create DataFrame
    # Rows = portfolios, Columns = months
    portfolio_names = [f"portfolio_{i+1:04d}" for i in range(n_portfolios)]
    month_names = [f"Month_{t+1}" for t in range(n_months)]
    
    hhi_df = pd.DataFrame(
        hhi_matrix,
        index=portfolio_names,
        columns=month_names
    )
    hhi_df.index.name = 'Portfolio'
    
    return hhi_df


def calculate_euclidean_distance_matrix(
    weights_matrix: np.ndarray
) -> pd.DataFrame:
    """
    Calculate Euclidean distance from equal-weight portfolio for each portfolio at each month.
    
    Equal-weight reference: [1/N, 1/N, ..., 1/N] where N = number of assets
    Distance = ||w - w_eq|| = sqrt(Σ(w_i - 1/N)²)
    
    Parameters:
    -----------
    weights_matrix : np.ndarray
        Portfolio weights matrix (HORIZON_MONTHS × N_PORTFOLIOS × N_ASSETS)
    
    Returns:
    --------
    distance_df : pd.DataFrame
        DataFrame with Euclidean distances
        Rows: portfolios (1 to N_PORTFOLIOS)
        Columns: months (1 to HORIZON_MONTHS)
        Shape: (N_PORTFOLIOS × HORIZON_MONTHS)
    """
    n_months, n_portfolios, n_assets = weights_matrix.shape
    
    # Equal-weight portfolio
    equal_weight = 1.0 / n_assets
    equal_weight_vector = np.full(n_assets, equal_weight)
    
    # Calculate Euclidean distance for each portfolio at each month
    distance_matrix = np.zeros((n_portfolios, n_months))
    
    for t in range(n_months):
        month_weights = weights_matrix[t, :, :]  # (n_portfolios, n_assets)
        
        # Calculate distance from equal-weight for each portfolio
        # Distance = sqrt(sum((w_i - 1/N)^2))
        diff = month_weights - equal_weight_vector  # (n_portfolios, n_assets)
        distance = np.sqrt(np.sum(diff ** 2, axis=1))  # (n_portfolios,)
        distance_matrix[:, t] = distance
    
    # Create DataFrame
    # Rows = portfolios, Columns = months
    portfolio_names = [f"portfolio_{i+1:04d}" for i in range(n_portfolios)]
    month_names = [f"Month_{t+1}" for t in range(n_months)]
    
    distance_df = pd.DataFrame(
        distance_matrix,
        index=portfolio_names,
        columns=month_names
    )
    distance_df.index.name = 'Portfolio'
    
    return distance_df


def get_weights_snapshot(
    weights_matrix: np.ndarray,
    asset_names: List[str],
    month_index: int
) -> pd.DataFrame:
    """
    Get portfolio weights snapshot for a specific month.
    
    Parameters:
    -----------
    weights_matrix : np.ndarray
        Portfolio weights matrix (HORIZON_MONTHS × N_PORTFOLIOS × N_ASSETS)
    asset_names : List[str]
        Names of the assets
    month_index : int
        Month index (0-indexed, e.g., 0 for month 1, 239 for month 240)
    
    Returns:
    --------
    snapshot_df : pd.DataFrame
        DataFrame with portfolio weights for the specified month
        Rows: portfolios (1 to N_PORTFOLIOS)
        Columns: assets
        Shape: (N_PORTFOLIOS × N_ASSETS)
    """
    n_months, n_portfolios, n_assets = weights_matrix.shape
    
    # Validate month_index
    if month_index < 0 or month_index >= n_months:
        raise ValueError(f"month_index must be between 0 and {n_months-1}")
    
    # Extract weights for the specified month
    month_weights = weights_matrix[month_index, :, :]  # (n_portfolios, n_assets)
    
    # Create DataFrame
    portfolio_names = [f"portfolio_{i+1:04d}" for i in range(n_portfolios)]
    
    snapshot_df = pd.DataFrame(
        month_weights,
        index=portfolio_names,
        columns=asset_names
    )
    snapshot_df.index.name = 'Portfolio'
    
    return snapshot_df


def calculate_all_diversity_metrics(
    weights_matrix: np.ndarray,
    asset_names: List[str],
    percentiles: List[int] = [10, 25, 50, 75, 90]
) -> Dict[str, pd.DataFrame]:
    """
    Calculate all diversity metrics for portfolio weights.
    
    MODIFIED VERSION:
    - Per-asset statistics: only mean and std (removed min, max, range, percentiles)
    - Portfolio-level metrics:
      * HHI matrix (1000 portfolios × 480 months)
      * Euclidean distance matrix (1000 portfolios × 480 months)
      * Weight snapshots for months 1, 240, and 480 (1000 portfolios × 9 assets each)
    
    Parameters:
    -----------
    weights_matrix : np.ndarray
        Portfolio weights matrix (HORIZON_MONTHS × N_PORTFOLIOS × N_ASSETS)
    asset_names : List[str]
        Names of the assets
    percentiles : List[int]
        Percentiles to calculate (NOT USED, kept for compatibility)
    
    Returns:
    --------
    all_metrics : Dict[str, pd.DataFrame]
        Dictionary with all calculated metrics
    """
    n_months = weights_matrix.shape[0]
    
    # 1. Calculate per-asset statistics (mean and std only)
    weight_stats = calculate_weight_statistics(weights_matrix, asset_names)
    
    # 2. Calculate HHI matrix (portfolios × months)
    hhi_matrix = calculate_hhi_matrix(weights_matrix)
    
    # 3. Calculate Euclidean distance matrix (portfolios × months)
    distance_matrix = calculate_euclidean_distance_matrix(weights_matrix)
    
    # 4. Get weight snapshots for specific months
    # Month 1 (index 0)
    snapshot_month_1 = get_weights_snapshot(weights_matrix, asset_names, 0)
    
    # Month 240 (index 239) - middle of horizon
    month_240_idx = min(239, n_months - 1)
    snapshot_month_240 = get_weights_snapshot(weights_matrix, asset_names, month_240_idx)
    
    # Last month (index n_months - 1)
    snapshot_month_last = get_weights_snapshot(weights_matrix, asset_names, n_months - 1)
    
    # Combine all metrics
    all_metrics = {
        'weights_mean': weight_stats['mean'],
        'weights_std': weight_stats['std'],
        'hhi': hhi_matrix,
        'euclidean_distance': distance_matrix,
        'weights_month_001': snapshot_month_1,
        'weights_month_240': snapshot_month_240,
        f'weights_month_{n_months:03d}': snapshot_month_last,
    }
    
    return all_metrics
