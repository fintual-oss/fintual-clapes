import numpy as np
import pandas as pd
from typing import Tuple


def apply_random_permutation_per_month(
    returns_df: pd.DataFrame,
    random_seed: int = None
) -> pd.DataFrame:
    """
    Apply random permutation to returns within each month across trajectories.
    
    This maintains the distribution of returns for each month (respecting CVaR
    constraints) while breaking the continuity of original trajectories.
    
    Parameters:
    -----------
    returns_df : pd.DataFrame
        Monthly returns (rows=months, columns=trajectories)
        Shape: (MONTHS, N_TRAJECTORIES)
    random_seed : int, optional
        Random seed for reproducibility
    
    Returns:
    --------
    permuted_df : pd.DataFrame
        Returns with random permutation applied per month
        Shape: (MONTHS, N_TRAJECTORIES)
    
    Example:
    --------
    Original Month 1: [0.02, 0.03, 0.01, 0.04]
    Permuted Month 1: [0.04, 0.01, 0.03, 0.02]  (same values, different order)
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Create a copy to avoid modifying original
    permuted_df = returns_df.copy()
    
    # For each month (row), permute the returns across trajectories
    for month_idx in range(permuted_df.shape[0]):
        # Get returns for this month and make a writable copy
        month_returns = permuted_df.iloc[month_idx, :].values.copy()
        
        # Shuffle them
        np.random.shuffle(month_returns)
        
        # Assign back
        permuted_df.iloc[month_idx, :] = month_returns
    
    return permuted_df


def generate_sorted_trajectories(
    returns_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Generate sorted trajectories by ranking returns within each month.
    
    Creates N new trajectories where:
    - Trajectory 1: Takes the maximum return from each month
    - Trajectory 2: Takes the 2nd highest return from each month
    - ...
    - Trajectory N: Takes the minimum return from each month
    
    Parameters:
    -----------
    returns_df : pd.DataFrame
        Monthly returns (rows=months, columns=trajectories)
        Shape: (MONTHS, N_TRAJECTORIES)
    
    Returns:
    --------
    sorted_df : pd.DataFrame
        Sorted trajectories (rows=months, columns=sorted_trajectories)
        Shape: (MONTHS, N_TRAJECTORIES)
    
    Example:
    --------
    Original Month 1: [0.02, 0.03, 0.01, 0.04]
    Sorted trajectories for Month 1:
    - Traj 1: 0.04 (max)
    - Traj 2: 0.03 (2nd)
    - Traj 3: 0.02 (3rd)
    - Traj 4: 0.01 (min)
    """
    n_months, n_trajectories = returns_df.shape
    
    # Create array for sorted trajectories
    sorted_returns = np.zeros((n_months, n_trajectories))
    
    # For each month, sort returns in descending order
    for month_idx in range(n_months):
        month_returns = returns_df.iloc[month_idx, :].values
        # Sort descending (highest to lowest)
        sorted_returns[month_idx, :] = np.sort(month_returns)[::-1]
    
    # Create DataFrame with sorted trajectories
    sorted_columns = [f"sorted_traj_{i+1:05d}" for i in range(n_trajectories)]
    sorted_df = pd.DataFrame(
        sorted_returns,
        index=returns_df.index,
        columns=sorted_columns
    )
    
    return sorted_df


def transform_trajectories(
    returns_df: pd.DataFrame,
    mode: int,
    random_seed: int = None
) -> Tuple[pd.DataFrame, str]:
    """
    Transform trajectories according to specified mode.
    
    Parameters:
    -----------
    returns_df : pd.DataFrame
        Original monthly returns (rows=months, columns=trajectories)
    mode : int
        Analysis mode:
        - 1: Original trajectories only
        - 2: Sorted trajectories only
        - 3: Permuted trajectories only
        - 4: Permuted + Sorted trajectories
        - 5: Original + Sorted trajectories
        - 6: Original + Permuted trajectories
        - 7: Original + Sorted + Permuted trajectories
    random_seed : int, optional
        Random seed for permutation (only used in modes 3, 4, 6, 7)
    
    Returns:
    --------
    transformed_df : pd.DataFrame
        Transformed returns matrix
    description : str
        Description of the transformation applied
    """
    if mode == 1:
        # Mode 1: Original trajectories (no transformation)
        description = "Original trajectories"
        return returns_df.copy(), description
    
    elif mode == 2:
        # Mode 2: Sorted trajectories only
        sorted_df = generate_sorted_trajectories(returns_df)
        description = f"Sorted trajectories (N={sorted_df.shape[1]})"
        return sorted_df, description
    
    elif mode == 3:
        # Mode 3: Permuted trajectories only
        permuted_df = apply_random_permutation_per_month(
            returns_df,
            random_seed=random_seed
        )
        
        # Rename permuted columns
        n_traj = permuted_df.shape[1]
        permuted_df.columns = [f"permuted_traj_{i+1:05d}" for i in range(n_traj)]
        
        description = f"Permuted trajectories (N={permuted_df.shape[1]})"
        return permuted_df, description
    
    elif mode == 4:
        # Mode 4: Permuted + Sorted
        # Step 1: Apply random permutation to original trajectories
        permuted_df = apply_random_permutation_per_month(
            returns_df,
            random_seed=random_seed
        )
        
        # Rename permuted columns
        n_traj = permuted_df.shape[1]
        permuted_df.columns = [f"permuted_traj_{i+1:05d}" for i in range(n_traj)]
        
        # Step 2: Generate sorted trajectories (from original, as they're the same)
        sorted_df = generate_sorted_trajectories(returns_df)
        
        # Step 3: Combine both
        combined_df = pd.concat([permuted_df, sorted_df], axis=1)
        
        description = (
            f"Permuted trajectories (N={permuted_df.shape[1]}) + "
            f"Sorted trajectories (N={sorted_df.shape[1]}) = "
            f"Total: {combined_df.shape[1]}"
        )
        
        return combined_df, description
    
    elif mode == 5:
        # Mode 5: Original + Sorted
        # Step 1: Keep original trajectories
        original_df = returns_df.copy()
        original_df.columns = [f"original_traj_{i+1:05d}" for i in range(original_df.shape[1])]
        
        # Step 2: Generate sorted trajectories
        sorted_df = generate_sorted_trajectories(returns_df)
        
        # Step 3: Combine both
        combined_df = pd.concat([original_df, sorted_df], axis=1)
        
        description = (
            f"Original trajectories (N={original_df.shape[1]}) + "
            f"Sorted trajectories (N={sorted_df.shape[1]}) = "
            f"Total: {combined_df.shape[1]}"
        )
        
        return combined_df, description
    
    elif mode == 6:
        # Mode 6: Original + Permuted
        # Step 1: Keep original trajectories
        original_df = returns_df.copy()
        original_df.columns = [f"original_traj_{i+1:05d}" for i in range(original_df.shape[1])]
        
        # Step 2: Generate permuted trajectories
        permuted_df = apply_random_permutation_per_month(
            returns_df,
            random_seed=random_seed
        )
        
        # Rename permuted columns
        n_traj = permuted_df.shape[1]
        permuted_df.columns = [f"permuted_traj_{i+1:05d}" for i in range(n_traj)]
        
        # Step 3: Combine both
        combined_df = pd.concat([original_df, permuted_df], axis=1)
        
        description = (
            f"Original trajectories (N={original_df.shape[1]}) + "
            f"Permuted trajectories (N={permuted_df.shape[1]}) = "
            f"Total: {combined_df.shape[1]}"
        )
        
        return combined_df, description
    
    elif mode == 7:
        # Mode 7: Original + Sorted + Permuted
        # Step 1: Keep original trajectories
        original_df = returns_df.copy()
        original_df.columns = [f"original_traj_{i+1:05d}" for i in range(original_df.shape[1])]
        
        # Step 2: Generate sorted trajectories
        sorted_df = generate_sorted_trajectories(returns_df)
        
        # Step 3: Generate permuted trajectories
        permuted_df = apply_random_permutation_per_month(
            returns_df,
            random_seed=random_seed
        )
        
        # Rename permuted columns
        n_traj = permuted_df.shape[1]
        permuted_df.columns = [f"permuted_traj_{i+1:05d}" for i in range(n_traj)]
        
        # Step 4: Combine all three
        combined_df = pd.concat([original_df, sorted_df, permuted_df], axis=1)
        
        description = (
            f"Original trajectories (N={original_df.shape[1]}) + "
            f"Sorted trajectories (N={sorted_df.shape[1]}) + "
            f"Permuted trajectories (N={permuted_df.shape[1]}) = "
            f"Total: {combined_df.shape[1]}"
        )
        
        return combined_df, description
    
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 1, 2, 3, 4, 5, 6, or 7.")


def get_mode_description(mode: int) -> str:
    """
    Get human-readable description of analysis mode.
    
    Parameters:
    -----------
    mode : int
        Analysis mode (1, 2, 3, 4, 5, 6, or 7)
    
    Returns:
    --------
    description : str
        Description of the mode
    """
    descriptions = {
        1: "Mode 1: Original trajectories only",
        2: "Mode 2: Sorted trajectories only (ranked by return per month)",
        3: "Mode 3: Permuted trajectories only (random permutation per month)",
        4: "Mode 4: Permuted + Sorted trajectories",
        5: "Mode 5: Original + Sorted trajectories",
        6: "Mode 6: Original + Permuted trajectories",
        7: "Mode 7: Original + Sorted + Permuted trajectories"
    }
    
    return descriptions.get(mode, "Unknown mode")
