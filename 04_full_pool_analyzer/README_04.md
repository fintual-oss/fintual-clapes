# 04_full_pool_analyzer — Full Pool Scenario Analyzer

## Overview

This is the final module of the pipeline. It reads the annualized return results produced by step 03 and aggregates them into a single Excel file with one row per glidepath curve. For each curve, it computes return statistics and the fraction of outcomes that exceed a set of target return thresholds.

The key design decision of this module is that all statistics are computed over the **full pool** of `(N_SEEDS × N_PORTFOLIOS)` observations simultaneously, without any intermediate averaging step. This treats every `(seed, portfolio)` pair as an independent observation, giving the maximum statistical resolution available.

The output Excel file is the final deliverable of the full pipeline and is used to compare and rank glidepath strategies.

## What is Cumulative Risk?

Each glidepath curve has a CVaR limit for every month of the horizon. `cumulative_risk` is the sum of all those monthly CVaR limits across the full horizon. It is a single scalar that summarizes how much total risk a glidepath strategy allows over its lifetime: a higher value means more risk was permitted, a lower value means the strategy was more conservative throughout.

This metric is used as the default sort key in the output, placing the most aggressive strategies at the top.

## What is `pct_above`?

For each target return threshold, `pct_above` is the fraction of all `(seed, portfolio)` pairs in the full pool whose annualized return is greater than or equal to that threshold. It answers the question: "across all scenarios and all portfolio trajectories, what proportion achieved at least X% annualized return?"

A list of thresholds is defined in `TARGET_RETURN_THRESHOLDS`. Each threshold produces one column in the output Excel file.

## Connection to Module 00

The values in `TARGET_RETURN_THRESHOLDS` are not arbitrary — they should be set using the **required returns calculated by module 00** (`00_target_return`). That module finds the exact annual return each demographic profile needs to retire with a Y% replacement rate. Using those values as thresholds here allows interpreting the output as:

> "X% of all (seed, portfolio) outcomes achieve the return needed for [demographic profile] to retire adequately."

**Workflow:**
1. Run module 00 and note the `Required Return (%)` for each profile from the Summary sheet.
2. Use those values (converted to decimals) as entries in `TARGET_RETURN_THRESHOLDS` in this module.
3. Interpret each `pct_above_X.XX%` column as the probability of meeting the pension adequacy target for the corresponding profile.

## File Structure

```
04_full_pool_analyzer/
├── main.py       # Main execution script (EDIT CONFIGURATION HERE)
├── loaders.py    # Reads glidepath parameters and HDF5 results from step 03
├── routes.py     # Path management
└── __init__.py   # Package documentation
```

## Required Inputs

Before running, ensure the following files exist:

```
repo_root/
└── outputs/
    ├── glidepaths_universe.xlsx
    └── scenario_results/
        ├── curve_0001.h5
        ├── curve_0002.h5
        └── ...
```

**`glidepaths_universe.xlsx`**: Output from step 01. Used to read curve parameters (`t_start`, `t_A`, `A`, `B`, `t_B`, `t_end`) and the monthly CVaR limits needed to compute `cumulative_risk`.

**`scenario_results/curve_XXXX.h5`**: Output from step 03. Each file must contain a dataset named `annualized_returns` with shape `(N_SEEDS, N_PORTFOLIOS)`.

## Configuration Parameters

All configuration is defined at the top of `main.py`.

### Target Return Thresholds

```python
TARGET_RETURN_THRESHOLDS = [0.0711, 0.0701, 0.0691, ...]
```

**What it means:** The list of annualized return levels used to compute `pct_above` columns. Each value is a decimal (e.g., `0.0711` = 7.11%). For each threshold, one column is added to the output with the name `pct_above_X.XX%`.

**Constraint:** All values must be in `(0, 1)`. The list must contain at least one value.

**How to modify:** Replace or extend the list with the thresholds relevant to your analysis. The order of values does not affect the output; each threshold produces an independent column.

### Percentiles

```python
PERCENTILES = [10, 25, 50, 75, 90]
```

**What it means:** The percentiles computed over the full pool matrix. Each value produces one column in the output named `return_pXX` (e.g., `return_p10`, `return_p50`).

**How to modify:** Add or remove integer percentile values between 0 and 100.

### Sort Order

```python
SORT_BY = "cumulative_risk"
```

**What it means:** Column used to sort the output rows. The default sorts by `cumulative_risk` descending (most aggressive strategies first), with `curve_id` as a tiebreaker.

**How to modify:** Set to any valid column name from the output, or set to `None` to keep the original discovery order.

### Curve Selection

```python
PROCESS_ALL_CURVES = True
CURVES_TO_ANALYZE  = ["curve_0001", "curve_0002"]  # Used only if PROCESS_ALL_CURVES = False
```

**What it means:**

- `PROCESS_ALL_CURVES = True`: processes every `curve_*.h5` file found in `outputs/scenario_results/`, ignoring `CURVES_TO_ANALYZE`. **This is the recommended default.**
- `PROCESS_ALL_CURVES = False`: processes only the curves listed in `CURVES_TO_ANALYZE` that also have a corresponding result file. Curves listed but not found on disk are skipped with a warning.

### Output Label

```python
OUTPUT_LABEL = ""
```

**What it means:** Optional string appended to the output filename. With `OUTPUT_LABEL = ""` the file is named `analysis_full_pool.xlsx`. With `OUTPUT_LABEL = "v2"` it becomes `analysis_full_pool_v2.xlsx`. Useful for keeping multiple versions without overwriting previous runs.

## How to Run

```bash
python -m 04_full_pool_analyzer.main
```

Or, if you are inside the `04_full_pool_analyzer/` directory:

```bash
python main.py
```

## How It Works

### Step 1: Load glidepath parameters and CVaR limits

`loaders.py` reads `glidepaths_universe.xlsx` twice: once for the parameter rows (`t_start`, `t_A`, `A`, `B`, `t_B`, `t_end`) and once for the monthly CVaR limit rows. The monthly CVaR limits are used solely to compute `cumulative_risk` per curve.

### Step 2: Discover available result files

The module scans `outputs/scenario_results/` for files matching `curve_*.h5` and filters them against `CURVES_TO_ANALYZE` (or takes all if `PROCESS_ALL_CURVES = True`).

### Step 3: Compute one row per curve

For each curve, the full `(N_SEEDS, N_PORTFOLIOS)` matrix is loaded as `float32` from the HDF5 file. All statistics are computed directly on this 2D matrix without flattening or averaging:

- **`cumulative_risk`**: sum of all monthly CVaR limits for this curve across the full horizon.
- **`return_mean`, `return_std`, `return_min`, `return_max`**: standard statistics over all `N_SEEDS × N_PORTFOLIOS` values.
- **`return_pXX`**: percentiles over the full pool for each value in `PERCENTILES`.
- **`pct_above_X.XX%`**: for each threshold, the fraction of `(arr >= threshold).mean()` over the full matrix.

If a curve's HDF5 file is missing or corrupted, that curve is skipped and a warning is printed. The run continues with the remaining curves.

### Step 4: Export to Excel

All rows are assembled into a DataFrame, sorted by `SORT_BY`, and written to a single Excel file with one sheet named `full_pool_analysis`.

## Output File

**Location:** `outputs/analysis_full_pool/`

**Filename:** `analysis_full_pool.xlsx` (or `analysis_full_pool_<label>.xlsx` if `OUTPUT_LABEL` is set)

**Structure:** One sheet (`full_pool_analysis`), one row per curve. Column order:

| Group | Columns |
|---|---|
| Curve identity | `curve_id`, `t_start`, `t_A`, `A`, `B`, `t_B`, `t_end` |
| Pool metadata | `n_portfolios`, `n_seeds`, `total_observations`, `horizon_months` |
| Risk summary | `cumulative_risk` |
| Return statistics | `return_mean`, `return_std`, `return_min`, `return_max` |
| Percentiles | `return_p10`, `return_p25`, `return_p50`, `return_p75`, `return_p90` |
| Threshold columns | `pct_above_X.XX%` × N (one per threshold, last columns) |

All statistics are computed over the full `(N_SEEDS × N_PORTFOLIOS)` pool with no intermediate averaging.

## Output Folder Structure

```
outputs/
├── glidepaths_universe.xlsx          ← module 01 (input)
├── hit_and_run_matrices/             ← module 02
├── scenario_results/                 ← module 03 (input)
└── analysis_full_pool/               ← created automatically by main.py
    └── analysis_full_pool.xlsx       ← final deliverable
```
