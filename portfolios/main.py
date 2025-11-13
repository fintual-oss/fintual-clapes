import os
import numpy as np
import pandas as pd

# Import helper functions from local files
from routes import input_returns_path, output_dir, output_file, export_results
from make_psd import f_make_psd
from simulate_asset_returns import simulate_asset_returns
from weights import f_monthly_weights_sequence
from compute_portfolio_returns import compute_portfolio_returns
from compute_cvar import compute_cvar_series

# -------------------------------
# CONFIGURATION
# -------------------------------
ALPHA = 0.90            # CVaR level: 0.90 means we look at the worst 10%
DELTA = 0.05            # Step size for the random weights grid
N_TRAJ = 10_000         # Number of simulated scenarios
HORIZON_MONTHS = 360    # 30 years = 360 months
N_PORTFOLIOS = 1_000    # Number of portfolios to simulate
RETURNS_SEED = 42       # Random seed for returns (None = random each run)

# Basic checks
assert 0 < DELTA <= 1, "DELTA must be in (0,1]."
assert 0 < ALPHA < 1, "ALPHA must be in (0,1)."
assert N_TRAJ >= 100, "Use at least 100 trajectories for stable results."
assert N_PORTFOLIOS >= 1, "At least one portfolio is required."

# -------------------------------
# MAIN FUNCTION
# -------------------------------
def main(seed_weights: int | None = None) -> None:
    """
    Run the full simulation and save results.
    Steps:
    1) Read historical returns from CSV.
    2) Estimate mean and covariance; make covariance PSD.
    3) Simulate future asset returns with MVN.
    4) For each portfolio:
       - Generate random monthly weights.
       - Compute portfolio returns for each month and scenario.
       - Compute CVaR for each month.
    5) Save all CVaR results in an Excel file.
    """
    # 1) Load historical returns
    returns_df = pd.read_csv(input_returns_path(), sep=",", parse_dates=[0], index_col=0)
    assert returns_df.shape[1] >= 2, "At least two assets are required."
    R = returns_df.to_numpy(dtype=float)
    n_assets = R.shape[1]

    # 2) Estimate mean and covariance, then force PSD
    mu = np.nanmean(R, axis=0)
    Sigma = np.cov(R, rowvar=False, ddof=1)
    Sigma_psd = f_make_psd(Sigma, eps=1e-12)

    # 3) Simulate asset returns with random generator
    rng_returns = (np.random.default_rng(RETURNS_SEED)
                   if RETURNS_SEED is not None else np.random.default_rng())
    samples = simulate_asset_returns(
        mu=mu,
        Sigma_psd=Sigma_psd,
        horizon_months=HORIZON_MONTHS,
        n_traj=N_TRAJ,
        rng=rng_returns
    )

    # 4) Loop over portfolios
    month_labels = [f"m{t+1:03d}" for t in range(HORIZON_MONTHS)]
    cvar_cols: dict[str, np.ndarray] = {}

    # Seed for weights (optional)
    rng_weights_master = (np.random.default_rng(seed_weights)
                          if seed_weights is not None else None)

    for p in range(1, N_PORTFOLIOS + 1):
        # Random generator for each portfolio's weights
        rng_weights = (np.random.default_rng()
                       if rng_weights_master is None
                       else np.random.default_rng(rng_weights_master.integers(0, 2**63 - 1)))

        # Monthly weights (T x N)
        W = f_monthly_weights_sequence(
            n_assets=n_assets,
            horizon_months=HORIZON_MONTHS,
            delta=DELTA,
            rng=rng_weights
        )

        # Portfolio returns (T x S)
        port_returns = compute_portfolio_returns(samples=samples, W=W)

        # Monthly CVaR (vector of length T)
        cvar_monthly = compute_cvar_series(port_returns=port_returns, alpha=ALPHA)

        # Save results with portfolio name
        pname = f"portfolio_{p:03d}"
        cvar_cols[pname] = cvar_monthly

    # 5) Build DataFrame with portfolios as rows, months as columns
    cvar_df = pd.DataFrame.from_dict(cvar_cols, orient="index", columns=month_labels)
    cvar_df.index.name = "Portfolio"

    # Reset index to include portfolio names as a column
    cvar_df = cvar_df.reset_index()

    # 6) Save results to Excel
    export_results(out_file=output_file(), cvar_df=cvar_df)

    print(f"File successfully saved at: {output_file()}")

# Run when executed directly
if __name__ == "__main__":
    main()

