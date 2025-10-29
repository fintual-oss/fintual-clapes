import numpy as np

def f_cvar(x: np.ndarray, alpha: float) -> float:
    """
    Compute left-tail CVaR at level alpha.
    - Look at the worst (1 - alpha) part of the returns.
    - If the Value-at-Risk (VaR) is positive (no losses), set threshold to 0.
    - If there are no losses, return 0.0.
    - Otherwise, return the average of the losses (as a positive number).
    """
    # Convert input to NumPy array
    x = np.asarray(x, float)

    # Remove NaN values
    x = x[~np.isnan(x)]

    # If no data, return NaN
    if x.size == 0:
        return float("nan")

    # Compute VaR percentile for the left tail
    var_tail = np.percentile(x, (1.0 - alpha) * 100.0)

    # If VaR is positive, use 0 as threshold
    var_tail = min(var_tail, 0.0)

    # Select values in the loss tail (<= threshold)
    tail = x[x <= var_tail]

    # If there are no losses, CVaR is zero
    if tail.size == 0:
        return 0.0

    # Return the average loss, positive value
    return float(abs(tail.mean()))


def compute_cvar_series(port_returns: np.ndarray, alpha: float) -> np.ndarray:
    """
    Apply f_cvar to each row of port_returns.
    - port_returns has shape (T, S): T = months, S = scenarios.
    - For each month, calculate CVaR across scenarios.
    - Returns a vector (T,) with one CVaR for each month.
    """
    return np.apply_along_axis(f_cvar, 1, port_returns, alpha)


