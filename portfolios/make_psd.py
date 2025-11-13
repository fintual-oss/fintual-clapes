import numpy as np

def f_make_psd(Sigma: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """
    Make a covariance matrix positive semi-definite (PSD).
    Steps:
    - Compute eigenvalues and eigenvectors of Sigma.
    - Replace negative (or very small) eigenvalues with eps.
    - Rebuild the matrix using the cleaned eigenvalues.
    """
    # Eigen-decomposition: Sigma = V * diag(d) * V.T
    d, V = np.linalg.eigh(Sigma)

    # Clip eigenvalues to be at least eps (avoid negatives)
    d_clipped = np.clip(d, eps, None)

    # Rebuild Sigma with the clipped eigenvalues
    # (V * d_clipped) @ V.T is faster than V @ np.diag(d_clipped) @ V.T
    return (V * d_clipped) @ V.T
