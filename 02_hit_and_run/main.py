import os
import sys
import time
import numpy as np
import pandas as pd
import h5py
from pathlib import Path
from multiprocessing import Pool, cpu_count

# Allow imports from sibling modules (shared utilities)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from make_psd import f_make_psd
from simulate_asset_returns import simulate_asset_returns
from cvar_portfolio_sampler import CVaRPortfolioSampler
from loaders import load_glidepaths_universe

from routes import (
    input_returns_path,
    input_glidepaths_path,
    output_weights_dir,
    output_weights_file,
)

# ============================================================
# CONFIGURATION
# ============================================================

# Simulation method for asset returns
SIMULATION_METHOD = "copula"  # "mvn" or "copula"

# CVaR parameters
ALPHA_CVAR = 0.90  # CVaR confidence level (0.90 = worst 10% tail)

# Portfolio generation
N_PORTFOLIOS_PER_MONTH = 10_000  # Portfolios generated per month
N_TRAJ            = 10_000       # Monte Carlo scenarios for CVaR evaluation
HORIZON_MONTHS    = 480          # 40 years

# Random seeds (for full reproducibility)
RETURNS_SEED  = 111  # Seed for simulated returns (shared with Module 03)
HIT_RUN_SEED  = 222  # Seed for Hit-and-Run directions

# Curve selection
CURVE_START = "None"  # Primera curva a procesar (None = desde el inicio)
CURVE_END   = None 

# Parallelization (months within a curve run in parallel)
N_PROCESSES = 15  # Number of CPU processes. Set to 1 for sequential.

# ============================================================
# VALIDATION
# ============================================================

assert SIMULATION_METHOD.lower() in ("mvn", "copula"), \
    "SIMULATION_METHOD must be 'mvn' or 'copula'."
assert 0 < ALPHA_CVAR < 1, \
    "ALPHA_CVAR must be in (0, 1)."
assert N_PORTFOLIOS_PER_MONTH >= 1, \
    "N_PORTFOLIOS_PER_MONTH must be >= 1."
assert N_TRAJ >= 100, \
    "Use at least 100 trajectories for stable CVaR estimation."


# ============================================================
# PARALLEL WORKER - one month at a time
# ============================================================

def _process_month(args):
    """
    Generate Hit-and-Run weight samples for a single month.

    Parameters:
    -----------
    args : tuple
        (t, month_returns, target_cvar, confidence_level,
         month_seed, N_PORTFOLIOS_PER_MONTH)

    Returns:
    --------
    tuple : (t, weights, success, error_msg)
        weights : np.ndarray, shape (N_PORTFOLIOS_PER_MONTH, N_ASSETS)
                  Contains NaN rows where generation failed.
    """
    t, month_returns, target_cvar, confidence_level, month_seed, n_portfolios = args

    n_assets = month_returns.shape[1]
    weights_out = np.full((n_portfolios, n_assets), np.nan)

    try:
        sampler = CVaRPortfolioSampler(
            returns=month_returns,
            confidence_level=confidence_level,
        )
        np.random.seed(month_seed)

        portfolios = sampler.generate_portfolios_batch(
            target_cvar=target_cvar,
            n_samples=n_portfolios,
            burn_in=20,
        )

        n_generated = min(len(portfolios), n_portfolios)
        if n_generated > 0:
            weights_out[:n_generated] = portfolios[:n_generated]

        return (t, weights_out, True, None)

    except Exception as exc:
        return (t, weights_out, False, str(exc))


# ============================================================
# HDF5 HELPERS
# ============================================================

def _init_hdf5(h5_path: str, horizon: int, n_portfolios: int, n_assets: int,
               curve_name: str, asset_names: list, config: dict) -> None:
    """
    Create (or overwrite) an HDF5 file and pre-allocate the weights dataset.

    Dataset layout:
        'weights'  →  shape (HORIZON_MONTHS, N_PORTFOLIOS, N_ASSETS)
                       dtype float32  (saves ~50% space vs float64)
    """
    with h5py.File(h5_path, "w") as f:
        ds = f.create_dataset(
            "weights",
            shape=(horizon, n_portfolios, n_assets),
            dtype="float32",
            compression="gzip",
            compression_opts=4,       # balanced speed / size
            chunks=(1, n_portfolios, n_assets),  # chunk = one month slice
        )
        # Metadata as attributes
        ds.attrs["curve_name"]         = curve_name
        ds.attrs["horizon_months"]     = horizon
        ds.attrs["n_portfolios"]       = n_portfolios
        ds.attrs["n_assets"]           = n_assets
        ds.attrs["returns_seed"]       = config["returns_seed"]
        ds.attrs["hit_run_seed"]       = config["hit_run_seed"]
        ds.attrs["simulation_method"]  = config["simulation_method"]
        ds.attrs["alpha_cvar"]         = config["alpha_cvar"]
        ds.attrs["asset_names"]        = ",".join(asset_names)


def _write_month_slice(h5_path: str, t: int, weights: np.ndarray) -> None:
    """Write weights for month t into an already-initialised HDF5 file."""
    with h5py.File(h5_path, "a") as f:
        f["weights"][t, :, :] = weights.astype("float32")


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """
    Module 02 – Hit-and-Run Weight Sampler.

    Pipeline
    --------
    1. Load historical returns from CSV.
    2. Estimate mu & Sigma; make Sigma PSD.
    3. Simulate future asset returns → shape (480, 10_000, 9).
    4. Load CVaR glidepath curves.
    5. For each curve:
         a. Initialise an HDF5 file.
         b. For each month (in parallel), run Hit-and-Run to get weights.
         c. Write weights slice-by-slice into HDF5.
    """

    # Resolve process count
    n_proc = max(1, cpu_count() - 1) if N_PROCESSES in (None, "auto") else N_PROCESSES

    # ── Header ───────────────────────────────────────────────
    print("=" * 70)
    print("MODULE 01 - HIT-AND-RUN WEIGHT SAMPLER")
    print("=" * 70)
    print(f"  Simulation method   : {SIMULATION_METHOD.upper()}")
    print(f"  CVaR level          : {ALPHA_CVAR*100:.0f}%  (tail = {(1-ALPHA_CVAR)*100:.0f}%)")
    print(f"  Portfolios / month  : {N_PORTFOLIOS_PER_MONTH:,}")
    print(f"  MC scenarios (CVaR) : {N_TRAJ:,}")
    print(f"  Horizon             : {HORIZON_MONTHS} months")
    print(f"  Returns seed        : {RETURNS_SEED}")
    print(f"  Hit-and-Run seed    : {HIT_RUN_SEED}")
    print(f"  CPU processes       : {n_proc}")
    print("=" * 70)

    # ── 1. Historical returns ─────────────────────────────────
    print("\n[1/5] Loading historical returns...")
    returns_df = pd.read_csv(input_returns_path(), sep=",", parse_dates=[0], index_col=0)
    assert returns_df.shape[1] >= 2, "Need at least 2 assets."
    R = returns_df.to_numpy(dtype=float)
    n_assets   = R.shape[1]
    asset_names = returns_df.columns.tolist()
    print(f"      {R.shape[0]} periods × {n_assets} assets")
    print(f"      Assets: {', '.join(asset_names)}")

    # ── 2. Parameters ─────────────────────────────────────────
    print("\n[2/5] Estimating mu & Sigma...")
    mu        = np.nanmean(R, axis=0)
    Sigma     = np.cov(R, rowvar=False, ddof=1)
    Sigma_psd = f_make_psd(Sigma, eps=1e-12)
    print(f"      Covariance matrix shape: {Sigma_psd.shape}")

    # ── 3. Simulate asset returns ─────────────────────────────
    print(f"\n[3/5] Simulating asset returns ({SIMULATION_METHOD.upper()})...")
    print(f"      This matrix is deterministic for RETURNS_SEED={RETURNS_SEED}")
    print(f"      (Module 02 will regenerate it with the same seed)")
    rng_returns = np.random.default_rng(RETURNS_SEED)
    samples = simulate_asset_returns(
        mu=mu,
        Sigma_psd=Sigma_psd,
        R_historical=R,
        horizon_months=HORIZON_MONTHS,
        n_traj=N_TRAJ,
        rng=rng_returns,
        method=SIMULATION_METHOD,
    )
    # samples shape: (HORIZON_MONTHS, N_TRAJ, N_ASSETS)
    print(f"      samples shape: {samples.shape}  (months × scenarios × assets)")

    # ── 4. Load glidepath curves ──────────────────────────────
    print("\n[4/5] Loading CVaR glidepath curves...")
    params_df, glides_df = load_glidepaths_universe(input_glidepaths_path())
    all_curves = glides_df.columns.tolist()
    print(f"      Total curves available: {len(all_curves)}")

    idx_start = all_curves.index(CURVE_START) if CURVE_START else 0
    idx_end   = all_curves.index(CURVE_END) + 1 if CURVE_END else len(all_curves)
    curves    = all_curves[idx_start:idx_end]

    if not curves:
        raise ValueError("No valid curves found in the specified range.")
    print(f"      Processing {len(curves)} curves: {curves[0]} → {curves[-1]}")

    # ── 5. Output directory ───────────────────────────────────
    out_dir = output_weights_dir()
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n[5/5] Output directory: {out_dir}")

    # ── Config dict for HDF5 metadata ────────────────────────
    config = dict(
        returns_seed=RETURNS_SEED,
        hit_run_seed=HIT_RUN_SEED,
        simulation_method=SIMULATION_METHOD,
        alpha_cvar=ALPHA_CVAR,
    )
    confidence_level = 1.0 - ALPHA_CVAR

    # ── 6. Process curves ─────────────────────────────────────
    print("\n" + "=" * 70)
    print("GENERATING WEIGHTS")
    print("=" * 70)

    total_start = time.time()

    for curve_idx, curve_name in enumerate(curves, 1):
        curve_start = time.time()
        print(f"\n  [{curve_idx}/{len(curves)}] {curve_name}")

        # CVaR limits for this curve: shape (HORIZON_MONTHS,)
        cvar_limits = glides_df[curve_name].values

        # Reproducible seeds for this curve's months
        abs_idx    = all_curves.index(curve_name)          # stable regardless of subset
        curve_rng  = np.random.default_rng(HIT_RUN_SEED + abs_idx)

        # Initialise HDF5 (pre-allocate full tensor)
        h5_path = output_weights_file(curve_name)
        _init_hdf5(
            h5_path, HORIZON_MONTHS, N_PORTFOLIOS_PER_MONTH, n_assets,
            curve_name, asset_names, config,
        )

        # Build argument list for each month
        month_args = [
            (
                t,
                samples[t, :, :],           # (N_TRAJ, N_ASSETS) for this month
                cvar_limits[t],             # scalar CVaR limit
                confidence_level,
                int(curve_rng.integers(0, 2**31 - 1)),
                N_PORTFOLIOS_PER_MONTH,
            )
            for t in range(HORIZON_MONTHS)
        ]

        # Run months (parallel or sequential)
        if n_proc == 1:
            print(f"    Running sequentially ({HORIZON_MONTHS} months)...")
            results = []
            for i, args in enumerate(month_args):
                results.append(_process_month(args))
                if (i + 1) % 100 == 0:
                    pct = (i + 1) / HORIZON_MONTHS * 100
                    print(f"      {i+1}/{HORIZON_MONTHS}  ({pct:.0f}%)")
        else:
            print(f"    Running in parallel ({n_proc} processes, {HORIZON_MONTHS} months)...")
            with Pool(processes=n_proc) as pool:
                results = []
                done = 0
                for res in pool.imap_unordered(_process_month, month_args, chunksize=5):
                    results.append(res)
                    done += 1
                    if done % 50 == 0 or done == HORIZON_MONTHS:
                        pct = done / HORIZON_MONTHS * 100
                        print(f"      {done}/{HORIZON_MONTHS}  ({pct:.0f}%)")

        # Write results into HDF5 month by month
        failed = 0
        for t, weights, success, err in results:
            _write_month_slice(h5_path, t, weights)
            if not success:
                failed += 1
                if failed <= 5:
                    print(f"    ⚠ Month {t+1} failed: {err}")

        if failed > 5:
            print(f"    ⚠ ... and {failed - 5} more months failed.")

        elapsed = time.time() - curve_start
        size_mb = os.path.getsize(h5_path) / 1e6
        print(f"    ✓ Done in {elapsed/60:.1f} min  |  {h5_path}  ({size_mb:.1f} MB)")

        # ETA
        if curve_idx < len(curves):
            avg = (time.time() - total_start) / curve_idx
            eta = avg * (len(curves) - curve_idx)
            print(f"    ⏱ Estimated remaining: {eta/60:.1f} min")

    # ── Summary ───────────────────────────────────────────────
    total_elapsed = time.time() - total_start
    print("\n" + "=" * 70)
    print("MODULE 01 COMPLETE")
    print("=" * 70)
    print(f"  Curves processed : {len(curves)}")
    print(f"  Total time       : {total_elapsed/60:.1f} min")
    print(f"  Output folder    : {out_dir}")
    print(f"  Tensor per curve : ({HORIZON_MONTHS}, {N_PORTFOLIOS_PER_MONTH}, {n_assets})")
    print(f"  Dtype saved      : float32  (half the size of float64)")
    print(f"  Compression      : gzip level 4")
    print("=" * 70)
    print("\n  ▶ Ready for Module 03:")
    print(f"    - Reload weights with h5py: f['weights'][t, :, :]")
    print(f"    - Regenerate same 'samples' matrix using RETURNS_SEED={RETURNS_SEED}")
    print("=" * 70)


if __name__ == "__main__":
    main()
