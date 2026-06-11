import os
import sys
import time
import numpy as np
import pandas as pd
import h5py
from pathlib import Path

# Allow imports from shared utilities at repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from make_psd import f_make_psd
from simulate_asset_returns import simulate_asset_returns

from routes import (
    input_returns_path,
    input_weights_dir,
    input_weights_file,
    output_results_dir,
    output_results_file,
)

# ============================================================
# CONFIGURATION
# ============================================================

# Scenario seeds to evaluate.
# Each seed produces one independent draw of scenario_indices (480,),
# which selects one asset-return scenario per month.
# Add as many seeds as you want to explore.
SCENARIO_SEEDS = sorted(set([
    *range(1, 10001),      # Seeds 1-10000
]))

# Seed for the within-month portfolio shuffle.
# Kept fixed so the shuffle is identical across all scenario seeds,
# ensuring that differences in results come only from the scenario draw.
SHUFFLE_SEED = 42

# Must match the values used in Module 01 exactly.
RETURNS_SEED        = 111        # Seed for asset-return simulation
SIMULATION_METHOD   = "copula"   # "mvn" or "copula"
N_TRAJ              = 10_000     # Monte Carlo scenarios
HORIZON_MONTHS      = 480        # 40 years for men

# Curve selection
PROCESS_ALL_CURVES  = True # True = all .h5 files in hit_and_run_matrices/
CURVES_TO_PROCESS   = [f"curve_{i:04d}" for i in range(1, 128)] # Used only if PROCESS_ALL_CURVES = False

# ============================================================
# VALIDATION
# ============================================================

assert len(SCENARIO_SEEDS) >= 1, "Provide at least one scenario seed."
assert SIMULATION_METHOD.lower() in ("mvn", "copula"), \
    "SIMULATION_METHOD must be 'mvn' or 'copula'."
assert N_TRAJ >= 100, "N_TRAJ must be >= 100."

# ============================================================
# HELPERS
# ============================================================

def _get_available_curves(weights_dir: str) -> list:
    """Return sorted list of curve names that have an HDF5 weight file."""
    p = Path(weights_dir)
    if not p.exists():
        return []
    return sorted(f.stem for f in p.glob("curve_*.h5"))


def _load_weights(h5_path: str) -> tuple:
    """
    Load weight tensor and metadata from Module 01 HDF5 file.

    Returns:
    --------
    weights : np.ndarray, shape (HORIZON_MONTHS, N_PORTFOLIOS, N_ASSETS)
    meta    : dict with curve metadata
    """
    with h5py.File(h5_path, "r") as f:
        weights = f["weights"][:]          # full tensor into memory
        attrs   = dict(f["weights"].attrs)
    return weights.astype(np.float64), attrs


def _shuffle_within_months(weights: np.ndarray, shuffle_seed: int) -> np.ndarray:
    """
    Shuffle portfolio order independently within each month.

    This breaks the Markov-chain autocorrelation introduced by the
    Hit-and-Run sampler: consecutive portfolios within a month are
    correlated, but after shuffling the trajectory formed by position i
    across all months is independent of adjacent positions.

    Parameters:
    -----------
    weights      : (T, N, A)  original weight tensor
    shuffle_seed : int         seed for reproducibility

    Returns:
    --------
    shuffled : (T, N, A)  same values, independently permuted per month
    """
    np.random.seed(shuffle_seed)
    shuffled = weights.copy()
    T, N, _ = shuffled.shape
    for t in range(T):
        perm = np.random.permutation(N)
        shuffled[t] = shuffled[t, perm, :]
    return shuffled


def _compute_annualized_returns(
    weights_shuffled: np.ndarray,
    samples: np.ndarray,
    scenario_seed: int,
) -> np.ndarray:
    """
    For one scenario seed, compute the annualized cumulative return
    of each portfolio trajectory.

    Steps:
    ------
    1. Draw scenario_indices ~ Uniform{0, N_TRAJ-1}  shape (T,)
       Each entry selects one asset-return row per month.
    2. For month t, trajectory i:
         r[t, i] = weights_shuffled[t, i, :] @ samples[t, scenario_indices[t], :]
    3. Annualized return for trajectory i:
         (prod_t (1 + r[t, i]))^(12 / T) - 1

    Parameters:
    -----------
    weights_shuffled : (T, N, A)  shuffled portfolio weights
    samples          : (T, S, A)  simulated asset returns (S = N_TRAJ scenarios)
    scenario_seed    : int         seed for selecting one scenario per month

    Returns:
    --------
    annualized : np.ndarray, shape (N,)
        Annualized cumulative return for each of the N portfolio trajectories.
    """
    T, N, A = weights_shuffled.shape
    S       = samples.shape[1]

    # Draw one scenario index per month  →  shape (T,)
    rng              = np.random.default_rng(scenario_seed)
    scenario_indices = rng.integers(0, S, size=T)

    # Selected asset returns for each month  →  shape (T, A)
    selected_returns = samples[np.arange(T), scenario_indices, :]

    # Monthly portfolio returns  →  shape (T, N)
    monthly_returns  = np.einsum("tna,ta->tn", weights_shuffled, selected_returns)

    # Cumulative product across months  →  shape (N,)
    cumulative = np.prod(1.0 + monthly_returns, axis=0) - 1.0

    # Annualise: (1 + cumulative)^(12/T) - 1
    annualized = np.power(1.0 + cumulative, 12.0 / T) - 1.0

    return annualized


def _init_results_hdf5(
    h5_path: str,
    n_seeds: int,
    n_portfolios: int,
    curve_name: str,
    scenario_seeds: list,
    shuffle_seed: int,
    returns_seed: int,
    simulation_method: str,
    horizon_months: int,
) -> None:
    """
    Create (or overwrite) the results HDF5 and pre-allocate the dataset.

    Dataset 'annualized_returns':
        shape  (N_SEEDS, N_PORTFOLIOS)
        dtype  float32
        axis 0 → one row per scenario seed
        axis 1 → one column per portfolio trajectory
    """
    with h5py.File(h5_path, "w") as f:
        ds = f.create_dataset(
            "annualized_returns",
            shape=(n_seeds, n_portfolios),
            dtype="float32",
            compression="gzip",
            compression_opts=4,
            chunks=(1, n_portfolios),   # chunk = one seed row
        )
        ds.attrs["curve_name"]        = curve_name
        ds.attrs["scenario_seeds"]    = ",".join(str(s) for s in scenario_seeds)
        ds.attrs["shuffle_seed"]      = shuffle_seed
        ds.attrs["returns_seed"]      = returns_seed
        ds.attrs["simulation_method"] = simulation_method
        ds.attrs["horizon_months"]    = horizon_months
        ds.attrs["n_portfolios"]      = n_portfolios


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """
    Module 03 – Scenario Evaluator.

    For each curve (HDF5 weight matrix from Module 02):
      1. Load weights  (T × N × A)
      2. Shuffle portfolios within each month  (fixed SHUFFLE_SEED)
      3. Initialise output HDF5
      4. Open HDF5 ONCE and write all seeds inside the same context
         (avoids file-locking errors from repeated open/close per seed)
      5. For each scenario seed:
           a. Select one asset-return scenario per month
           b. Compute monthly portfolio returns  (T × N)
           c. Compute annualized cumulative return per trajectory  (N,)
           d. Write row directly into the open HDF5
    """

    # ── Header ───────────────────────────────────────────────────────────
    print("=" * 70)
    print("MODULE 03 - SCENARIO EVALUATOR")
    print("=" * 70)
    print(f"  Simulation method  : {SIMULATION_METHOD.upper()}")
    print(f"  Returns seed       : {RETURNS_SEED}  (must match Module 02)")
    print(f"  Shuffle seed       : {SHUFFLE_SEED}")
    print(f"  Scenario seeds     : {SCENARIO_SEEDS}")
    print(f"  N seeds            : {len(SCENARIO_SEEDS)}")
    print(f"  Horizon            : {HORIZON_MONTHS} months")
    print("=" * 70)

    # ── 1. Historical returns ─────────────────────────────────────────────
    print("\n[1/5] Loading historical returns...")
    returns_df = pd.read_csv(
        input_returns_path(), sep=",", parse_dates=[0], index_col=0
    )
    R           = returns_df.to_numpy(dtype=float)
    n_assets    = R.shape[1]
    asset_names = returns_df.columns.tolist()
    print(f"      {R.shape[0]} periods × {n_assets} assets")
    print(f"      Assets: {', '.join(asset_names)}")

    # ── 2. Simulate asset returns (deterministic, same as Module 02) ──────
    print(f"\n[2/5] Simulating asset returns ({SIMULATION_METHOD.upper()}, "
          f"RETURNS_SEED={RETURNS_SEED})...")
    mu        = np.nanmean(R, axis=0)
    Sigma_psd = f_make_psd(np.cov(R, rowvar=False, ddof=1), eps=1e-12)
    rng_ret   = np.random.default_rng(RETURNS_SEED)
    samples   = simulate_asset_returns(
        mu=mu,
        Sigma_psd=Sigma_psd,
        R_historical=R,
        horizon_months=HORIZON_MONTHS,
        n_traj=N_TRAJ,
        rng=rng_ret,
        method=SIMULATION_METHOD,
    )
    print(f"      samples shape: {samples.shape}  (months × scenarios × assets)")

    # ── 3. Discover curves ────────────────────────────────────────────────
    print("\n[3/5] Finding available weight matrices...")
    all_curves = _get_available_curves(input_weights_dir())
    print(f"      Found {len(all_curves)} curves in {input_weights_dir()}")

    if not all_curves:
        print("\n⚠  No HDF5 weight files found. Run Module 02 first.")
        return

    curves = all_curves if PROCESS_ALL_CURVES else [
        c for c in CURVES_TO_PROCESS if c in all_curves
    ]
    if not curves:
        print("⚠  None of CURVES_TO_PROCESS found. Check names.")
        return
    print(f"      Processing {len(curves)} curve(s)")

    # ── 4. Output directory ───────────────────────────────────────────────
    out_dir = output_results_dir()
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n[4/5] Output directory: {out_dir}")

    # ── 5. Process each curve ─────────────────────────────────────────────
    print("\n[5/5] Evaluating scenarios...")
    print("=" * 70)

    total_start = time.time()

    for curve_idx, curve_name in enumerate(curves, 1):
        curve_start = time.time()
        h5_in  = input_weights_file(curve_name)
        h5_out = output_results_file(curve_name)

        print(f"\n  [{curve_idx}/{len(curves)}] {curve_name}")

        if not Path(h5_in).exists():
            print(f"    ⚠  Weight file not found: {h5_in}  — skipping.")
            continue

        # 5a. Load weights from Module 02
        weights_raw, meta = _load_weights(h5_in)
        T, N, A = weights_raw.shape
        print(f"    Weights loaded   : ({T}, {N}, {A})")
        print(f"    Asset names      : {meta.get('asset_names', 'n/a')}")

        # 5b. Shuffle within each month (fixed seed → reproducible)
        print(f"    Shuffling portfolios within each month "
              f"(SHUFFLE_SEED={SHUFFLE_SEED})...")
        weights = _shuffle_within_months(weights_raw, SHUFFLE_SEED)
        print(f"    Shuffle complete.")

        # 5c. Initialise output HDF5
        _init_results_hdf5(
            h5_path=h5_out,
            n_seeds=len(SCENARIO_SEEDS),
            n_portfolios=N,
            curve_name=curve_name,
            scenario_seeds=SCENARIO_SEEDS,
            shuffle_seed=SHUFFLE_SEED,
            returns_seed=RETURNS_SEED,
            simulation_method=SIMULATION_METHOD,
            horizon_months=T,
        )

        # 5d. Open HDF5 ONCE and write all seeds inside the same context.
        #     This avoids the BlockingIOError (errno=35) that occurs when
        #     opening and closing the file repeatedly in a tight loop —
        #     the OS lock from the previous write has not been released
        #     before the next open attempt.
        with h5py.File(h5_out, "a") as h5_file:
            for seed_idx, seed in enumerate(SCENARIO_SEEDS):
                t0 = time.time()

                annualized = _compute_annualized_returns(
                    weights_shuffled=weights,
                    samples=samples,
                    scenario_seed=seed,
                )

                # Write directly into the already-open file
                h5_file["annualized_returns"][seed_idx, :] = \
                    annualized.astype("float32")

                elapsed_s = time.time() - t0
                print(
                    f"    Seed {seed:>6d}  "
                    f"({seed_idx+1}/{len(SCENARIO_SEEDS)})  "
                    f"mean={annualized.mean()*100:.2f}%  "
                    f"p50={np.median(annualized)*100:.2f}%  "
                    f"[{elapsed_s:.1f}s]"
                )

        curve_elapsed = time.time() - curve_start
        size_mb = Path(h5_out).stat().st_size / 1e6
        print(f"    ✓ Done in {curve_elapsed:.1f}s  |  {h5_out}  ({size_mb:.2f} MB)")

        if curve_idx < len(curves):
            avg = (time.time() - total_start) / curve_idx
            eta = avg * (len(curves) - curve_idx)
            print(f"    ⏱ Estimated remaining: {eta/60:.1f} min")

    # ── Summary ───────────────────────────────────────────────────────────
    total_elapsed = time.time() - total_start
    print("\n" + "=" * 70)
    print("MODULE 03 COMPLETE")
    print("=" * 70)
    print(f"  Curves processed   : {len(curves)}")
    print(f"  Scenario seeds     : {len(SCENARIO_SEEDS)}")
    print(f"  Total time         : {total_elapsed/60:.1f} min")
    print(f"  Output folder      : {out_dir}")
    print(f"  Tensor per curve   : ({len(SCENARIO_SEEDS)}, {N})")
    print(f"  Dtype saved        : float32")
    print("=" * 70)
    print("\n  ▶ How to read results:")
    print("    import h5py, numpy as np")
    print("    with h5py.File('scenario_results/curve_0001.h5', 'r') as f:")
    print("        arr = f['annualized_returns'][:]   # (N_seeds, 10_000)")
    print("        seeds = f['annualized_returns'].attrs['scenario_seeds']")
    print("=" * 70)


if __name__ == "__main__":
    main()