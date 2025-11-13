import numpy as np

def f_generate_drunken_weights(n_assets: int, delta: float, rng: np.random.Generator) -> np.ndarray:
    """
    Generate one random weight vector using a simple "drunken manager" idea.
    - Create a grid {0, delta, 2*delta, ..., 1}.
    - Choose (n_assets - 1) random cut points on that grid.
    - Sort them and take differences to get weights.
    - Weights are non-negative and sum to 1.
    """
    # Grid of possible cut points (rounded for stability)
    grid = np.round(np.arange(0.0, 1.0 + 1e-12, delta), 2)

    # Number of cut points needed to split [0, 1] into n_assets parts
    k = n_assets - 1

    # Randomly choose cut points with replacement
    cut_points = rng.choice(grid, size=k, replace=True)

    # Sort to ensure correct order on [0, 1]
    cut_points.sort()

    # Add the endpoints 0 and 1
    augmented = np.concatenate(([0.0], cut_points, [1.0]))

    # Differences between consecutive points -> weights that sum to 1
    weights = np.diff(augmented)
    return weights

def f_monthly_weights_sequence(
    n_assets: int,
    horizon_months: int,
    delta: float,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Build a matrix of monthly weights W with shape (T, N).
    - For each month t, generate one random weight vector.
    - Stack all vectors to get T rows (one per month).
    """
    # Allocate the output matrix
    W = np.empty((horizon_months, n_assets), dtype=float)

    # Generate weights for each month
    for t in range(horizon_months):
        W[t, :] = f_generate_drunken_weights(n_assets, delta, rng)

    return W
