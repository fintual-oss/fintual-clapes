import numpy as np

def grid_vals(start: float, stop: float, step: float, ndigits: int = 3) -> np.ndarray:
    """
    Robust grid [start, ..., stop] including stop.
    Uses linspace to avoid floating point issues.
    """
    if step <= 0:
        raise ValueError("step must be > 0")
    if stop < start:
        raise ValueError("stop must be >= start")
    n = int(round((stop - start) / step))
    vals = np.linspace(start, stop, n + 1)
    return np.round(vals, ndigits)
