import os
import sys
import time
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loaders import (
    load_glidepaths_parameters,
    load_glidepaths_cvar_limits,
    get_available_curves,
    load_annualized_returns,
)
from routes import (
    input_glidepaths_path,
    input_scenario_results_dir,
    input_scenario_results_file,
    output_analysis_full_pool_dir,
    output_analysis_full_pool_file,
)

# ============================================================
# CONFIGURATION
# ============================================================

# Target annualized return thresholds for % above calculations.
# Computed directly over the full (N_SEEDS x N_PORTFOLIOS) matrix.
TARGET_RETURN_THRESHOLDS = [
    0.0711, 0.0701, 0.0691, 0.0682, 0.0673, 0.0664, 0.0655, 0.0646,
    0.0638, 0.0629, 0.0621, 0.0613, 0.0605, 0.0597, 0.0589, 0.0582,
    0.0574, 0.0567, 0.0560, 0.0553, 0.0546, 0.0539, 0.0532, 0.0525,
    0.0519, 0.0512, 0.0506, 0.0499, 0.0493, 0.0487, 0.0481, 0.0474,
    0.0469, 0.0463, 0.0457, 0.0451, 0.0445, 0.0439, 0.0434, 0.0428,
    0.0423, 0.0417, 0.0412, 0.0407, 0.0401, 0.0396, 0.0391, 0.0386,
    0.0381, 0.0376, 0.0371, 0.0366, 0.0361, 0.0356, 0.0351, 0.0346,
    0.0342, 0.0337, 0.0332, 0.0328, 0.0323,
]

# Percentiles computed over the full matrix
PERCENTILES = [10, 25, 50, 75, 90]

# Sort output rows by cumulative_risk descending (highest risk curve first).
# Set to None to keep original curve order.
SORT_BY = "cumulative_risk"

# Curve selection
PROCESS_ALL_CURVES = True     # True = all .h5 files in scenario_results/
CURVES_TO_ANALYZE  = [        # Used only if PROCESS_ALL_CURVES = False
    "curve_0001",
    "curve_0002",
]

# Optional label appended to output filename
# Leave as "" for default: analysis_full_pool.xlsx
OUTPUT_LABEL = ""

# ============================================================
# VALIDATION
# ============================================================

assert len(TARGET_RETURN_THRESHOLDS) >= 1, "Provide at least one threshold."
assert all(0 < t < 1 for t in TARGET_RETURN_THRESHOLDS), \
    "All TARGET_RETURN_THRESHOLDS must be in (0, 1)."

# ============================================================
# CORE
# ============================================================

def _compute_row(
    curve_name: str,
    curve_params: dict,
    cumulative_risk: float,
    arr: np.ndarray,
    horizon_months: int,
) -> dict:
    """
    Build one result row for a single curve.

    All statistics and pct_above values are computed directly on the
    full (N_SEEDS x N_PORTFOLIOS) matrix without any intermediate
    averaging step. Numpy operates over all elements of the 2D matrix,
    which is equivalent to flattening but avoids the memory copy.

    Parameters:
    -----------
    arr : np.ndarray, shape (N_SEEDS, N_PORTFOLIOS)
        Full annualized returns matrix from Module 03. dtype float32.

    Column order:
        1. curve_id, t_start, t_A, A, B, t_B, t_end
        2. n_portfolios, n_seeds, total_observations, horizon_months
        3. cumulative_risk
        4. return_mean, return_std, return_min, return_max
        5. return_p10 ... return_p90
        6. pct_above_X%  (one per threshold — LAST columns)
    """
    n_seeds, n_portfolios = arr.shape
    total_obs = n_seeds * n_portfolios

    # 1. Curve identifiers & parameters
    row = {
        "curve_id" : curve_name,
        "t_start"  : curve_params.get("t_start", np.nan),
        "t_A"      : curve_params.get("t_A",     np.nan),
        "A"        : curve_params.get("A",        np.nan),
        "B"        : curve_params.get("B",        np.nan),
        "t_B"      : curve_params.get("t_B",      np.nan),
        "t_end"    : curve_params.get("t_end",    np.nan),
    }

    # 2. Pool info
    row["n_portfolios"]      = n_portfolios
    row["n_seeds"]           = n_seeds
    row["total_observations"] = total_obs
    row["horizon_months"]    = horizon_months

    # 3. Cumulative CVaR risk
    row["cumulative_risk"] = cumulative_risk

    # 4. Return statistics — numpy operates over all elements of the 2D
    #    matrix directly (no flatten copy needed)
    row["return_mean"] = float(np.mean(arr))
    row["return_std"]  = float(np.std(arr, ddof=1))
    row["return_min"]  = float(np.min(arr))
    row["return_max"]  = float(np.max(arr))

    # 5. Percentiles over full matrix
    for p in PERCENTILES:
        row[f"return_p{p:02d}"] = float(np.percentile(arr, p))

    # 6. pct_above: fraction of ALL (seed, portfolio) pairs >= threshold
    #    (arr >= thr) produces a bool matrix (N_SEEDS, N_PORTFOLIOS)
    #    .mean() averages over all elements → scalar  (LAST columns)
    for thr in TARGET_RETURN_THRESHOLDS:
        key      = f"pct_above_{thr*100:.2f}%"
        row[key] = round(float((arr >= thr).mean()), 5)

    return row


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """
    Module 04 – Full Pool Scenario Analyzer.

    For each curve (HDF5 results from Module 03):
      1. Load full annualized returns matrix (N_SEEDS x N_PORTFOLIOS)
      2. Compute all statistics and pct_above directly on the full matrix
         (equivalent to a pool of N_SEEDS x N_PORTFOLIOS observations)
      3. Collect one row per curve and export to a single Excel file
    """

    # ── Header ───────────────────────────────────────────────────────────
    print("=" * 70)
    print("MODULE 04 - FULL POOL SCENARIO ANALYZER")
    print("=" * 70)
    thresholds_str = ", ".join(
        f"{t*100:.2f}%" for t in TARGET_RETURN_THRESHOLDS[:5]
    )
    print(f"  Target thresholds  : {thresholds_str} ... "
          f"({len(TARGET_RETURN_THRESHOLDS)} total)")
    print(f"  Percentiles        : {PERCENTILES}")
    print(f"  Sort by            : {SORT_BY}")
    print(f"  Output label       : '{OUTPUT_LABEL}'" if OUTPUT_LABEL
          else "  Output label       : (none)")
    print("=" * 70)

    # ── 1. Load glidepath parameters & CVaR limits ────────────────────────
    print("\n[1/4] Loading glidepath parameters and CVaR limits...")
    params_df      = load_glidepaths_parameters(input_glidepaths_path())
    cvar_limits_df = load_glidepaths_cvar_limits(input_glidepaths_path())
    print(f"      Parameters : {params_df.shape[1]} curves")
    print(f"      CVaR limits: {cvar_limits_df.shape[0]} months "
          f"x {cvar_limits_df.shape[1]} curves")

    # ── 2. Discover curves ────────────────────────────────────────────────
    print("\n[2/4] Finding available result files...")
    all_curves = get_available_curves(input_scenario_results_dir())
    print(f"      Found {len(all_curves)} curve(s) in "
          f"{input_scenario_results_dir()}")

    if not all_curves:
        print("\n  No HDF5 result files found. Run Module 03 first.")
        return

    curves = all_curves if PROCESS_ALL_CURVES else [
        c for c in CURVES_TO_ANALYZE if c in all_curves
    ]
    if not curves:
        print("  None of CURVES_TO_ANALYZE found. Check names.")
        return
    print(f"      Processing {len(curves)} curve(s)")

    # ── 3. Compute one row per curve ──────────────────────────────────────
    print("\n[3/4] Computing full-pool statistics per curve...")
    print("-" * 70)

    rows        = []
    total_start = time.time()

    for curve_idx, curve_name in enumerate(curves, 1):
        h5_path = input_scenario_results_file(curve_name)

        if not Path(h5_path).exists():
            print(f"  [{curve_idx}/{len(curves)}] {curve_name} "
                  f"— file not found, skipping.")
            continue

        # Load full matrix (N_SEEDS, N_PORTFOLIOS) as float32
        try:
            arr, horizon_months, attrs = load_annualized_returns(h5_path)
        except OSError as e:
            print(f"    ⚠  Skipping {curve_name} — corrupted or truncated file.")
            print(f"       Delete and regenerate with Module 03: {h5_path}")
            print(f"       Error: {e}")
            continue

        n_seeds, n_portfolios = arr.shape
        print(f"  [{curve_idx}/{len(curves)}] {curve_name}  "
              f"({n_seeds} seeds  |  {n_portfolios:,} portfolios  |  "
              f"{n_seeds * n_portfolios:,} total observations)")

        # Curve parameters
        if curve_name in params_df.columns:
            curve_params = params_df[curve_name].to_dict()
        else:
            print(f"    Warning: parameters not found for {curve_name}")
            curve_params = {
                k: np.nan for k in ["t_start", "t_A", "A", "B", "t_B", "t_end"]
            }

        # Cumulative risk: sum of all monthly CVaR limits for this curve
        if curve_name in cvar_limits_df.columns:
            cumulative_risk = float(np.sum(cvar_limits_df[curve_name].values))
        else:
            print(f"    Warning: CVaR limits not found for {curve_name}")
            cumulative_risk = np.nan

        # Build result row
        row = _compute_row(
            curve_name      = curve_name,
            curve_params    = curve_params,
            cumulative_risk = cumulative_risk,
            arr             = arr,
            horizon_months  = horizon_months,
        )
        rows.append(row)

    elapsed = time.time() - total_start
    print(f"\n  Processed {len(rows)} curves in {elapsed:.1f}s")

    if not rows:
        print("  No results collected. Exiting.")
        return

    # ── 4. Export to Excel ────────────────────────────────────────────────
    print("\n[4/4] Exporting Excel file...")
    os.makedirs(output_analysis_full_pool_dir(), exist_ok=True)

    df = pd.DataFrame(rows)

    if SORT_BY and SORT_BY in df.columns:
        df = df.sort_values(
            by=[SORT_BY, "curve_id"],
            ascending=[False, True],
        ).reset_index(drop=True)

    out_path = output_analysis_full_pool_file(OUTPUT_LABEL)
    df.to_excel(out_path, sheet_name="full_pool_analysis", index=False, engine="openpyxl")

    size_mb = Path(out_path).stat().st_size / 1e6

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("MODULE 04 COMPLETE")
    print("=" * 70)
    print(f"  Curves analyzed      : {len(rows)}")
    print(f"  Seeds / curve        : {n_seeds}")
    print(f"  Portfolios / curve   : {n_portfolios:,}")
    print(f"  Total obs / curve    : {n_seeds * n_portfolios:,}")
    print(f"  Thresholds           : {len(TARGET_RETURN_THRESHOLDS)}")
    print(f"  Total time           : {elapsed:.1f}s")
    print(f"  Output file          : {out_path}  ({size_mb:.2f} MB)")
    print(f"\n  Column structure:")
    print(f"    curve_id, t_start, t_A, A, B, t_B, t_end")
    print(f"    n_portfolios, n_seeds, total_observations, horizon_months")
    print(f"    cumulative_risk")
    print(f"    return_mean, return_std, return_min, return_max  (full pool)")
    print(f"    return_p10, p25, p50, p75, p90                   (full pool)")
    print(f"    pct_above_X%  x{len(TARGET_RETURN_THRESHOLDS)}  <- full pool, last columns")
    print("=" * 70)


if __name__ == "__main__":
    main()
