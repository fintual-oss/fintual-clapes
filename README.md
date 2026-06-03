# CVaR Glidepath Portfolio Simulator

Simulation pipeline for generating and evaluating CVaR-constrained glidepath investment strategies in the context of the Chilean AFP pension system. The pipeline produces a ranked comparison of hundreds of glidepath strategies based on their probability of achieving pension-adequate returns across thousands of simulated market scenarios.

---

## What This Repository Does

The core question this project answers is: **which glidepath investment strategy maximizes the probability that an AFP affiliate achieves a sufficient retirement return?**

A glidepath strategy defines how much investment risk (measured by CVaR) is allowed at each age — higher risk when young, gradually reduced as retirement approaches. This project generates a universe of such strategies, samples portfolios that respect their constraints, evaluates their performance under many simulated market scenarios, and produces a ranked comparison table.

Module `00` provides a separate but related calculation: the annual return that an AFP affiliate actually needs to achieve a 63% pension replacement rate, which calibrates the performance thresholds used in module `04`.

---

## Gender Profile Configuration

Several modules have parameters that depend on whether you are running the pipeline for **men** or **women**. Before running, ensure these values are consistent across all modules:

| Parameter | Men | Women | Where to set it |
|---|---|---|---|
| `T_END_YEARS` | 65 | 60 | `01_glidepath_generator/config.py` |
| `T_B_YEAR` | 65 | 60 | `01_glidepath_generator/config.py` |
| `HORIZON_MONTHS` | 480 | 420 | `02_hit_and_run/main.py` and `03_scenario_evaluator/main.py` |
| Retirement ages / life expectancy | male values | female values | `00_target_return/parameters.py` |

**Rule of thumb:** set the gender profile in module 01 first, then propagate `HORIZON_MONTHS` to modules 02 and 03, and run module 00 with the matching demographic parameters to obtain the correct `TARGET_RETURN_THRESHOLDS` for module 04.

---

## Repository Structure

```
repo_root/
├── returns.csv                          # Historical asset returns (required input)
├── outputs/                             # All generated files (created automatically)
│   ├── target_return.xlsx               # Output of module 00
│   ├── glidepaths_universe.xlsx         # Output of module 01
│   ├── hit_and_run_matrices/            # Output of module 02 (one .h5 per curve)
│   ├── scenario_results/                # Output of module 03 (one .h5 per curve)
│   └── analysis_full_pool/              # Output of module 04
│       └── analysis_full_pool.xlsx
│
├── 00_target_return/                    # Required return calculator (standalone)
│   ├── parameters.py
│   ├── formulas.py
│   ├── exporters.py
│   ├── main.py
│   ├── __init__.py
│   └── README.md
│
├── 01_glidepath_generator/              # CVaR glidepath universe generator
│   ├── config.py
│   ├── main.py
│   ├── cvar_piecewise.py
│   ├── param_grid.py
│   ├── universe.py
│   ├── utils.py
│   ├── routes.py
│   ├── __init__.py
│   └── README.md
│
├── 02_hit_and_run/                      # CVaR-constrained portfolio sampler
│   ├── main.py
│   ├── cvar_portfolio_sampler.py
│   ├── simulate_asset_returns.py
│   ├── make_psd.py
│   ├── loaders.py
│   ├── routes.py
│   ├── __init__.py
│   └── README.md
│
├── 03_scenario_evaluator/               # Portfolio trajectory evaluator
│   ├── main.py
│   ├── simulate_asset_returns.py
│   ├── make_psd.py
│   ├── routes.py
│   ├── __init__.py
│   └── README.md
│
└── 04_full_pool_analyzer/               # Final aggregation and ranking
    ├── main.py
    ├── loaders.py
    ├── routes.py
    ├── __init__.py
    └── README.md
```

---

## Pipeline Overview

The four main modules run in sequence. Module `00` is independent and should be run before module `04` to calibrate the return thresholds.

```
returns.csv
    │
    ▼
┌─────────────────────────┐
│  01_glidepath_generator │  Generates all CVaR glidepath curves
│  config.py              │  → outputs/glidepaths_universe.xlsx
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  02_hit_and_run         │  Samples CVaR-constrained portfolios
│  main.py                │  → outputs/hit_and_run_matrices/curve_XXXX.h5
└────────────┬────────────┘       (one file per curve)
             │
             ▼
┌─────────────────────────┐
│  03_scenario_evaluator  │  Evaluates portfolio trajectories
│  main.py                │  → outputs/scenario_results/curve_XXXX.h5
└────────────┬────────────┘       (one file per curve)
             │
             ▼
┌─────────────────────────┐
│  04_full_pool_analyzer  │  Aggregates and ranks all curves
│  main.py                │  → outputs/analysis_full_pool/analysis_full_pool.xlsx
└─────────────────────────┘

─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─

┌─────────────────────────┐
│  00_target_return       │  Standalone: computes required return
│  main.py                │  → outputs/target_return.xlsx
└─────────────────────────┘  Used to calibrate thresholds in module 04
```

---

## Module Descriptions

### `00_target_return` — Required Return Calculator

**Standalone module.** Simulates the complete AFP pension lifecycle for four demographic profiles (male/female, with/without contribution gaps) and uses binary search to find the annual investment return required to achieve a 63% pension replacement rate.

**Input:** No external files. All inputs are parameters defined in `parameters.py`.

**Output:** `outputs/target_return.xlsx` with 7 sheets: parameters, summary of required returns, monthly accumulation detail per profile, and a sensitivity analysis.

**How it connects to the pipeline:** The `Required Return (%)` values in the Summary sheet are used to manually set `TARGET_RETURN_THRESHOLDS` in `04_full_pool_analyzer/main.py`. This allows interpreting the final results as: "what fraction of portfolio trajectories achieve the return needed for pension adequacy?"

**Key parameters to edit (`parameters.py`):**
- `age_retire_male` / `age_retire_female`: retirement ages (65 for men, 60 for women)
- `life_expectancy_male` / `life_expectancy_female`: life expectancy by gender
- `salary_initial_male` / `salary_initial_female`: starting salary in UF
- `contribution_rate`, `contribution_ceiling`: AFP contribution rules
- `contribution_density_*_with_gaps` / `*_no_gaps`: fraction of months contributing
- `replacement_rate_target`: target pension replacement rate (default: 63%)
- `months_for_replacement_rate`: reference window for average salary (12 or 120 months)

---

### `01_glidepath_generator` — CVaR Glidepath Universe Generator

Generates all valid combinations of CVaR glidepath parameters and exports them as a single Excel file. Each glidepath defines a maximum CVaR limit for every month of the investment horizon, following a three-phase shape: constant high risk → linear transition → constant low risk.

**Input:** No external files. All inputs are parameters defined in `config.py`.

**Output:** `outputs/glidepaths_universe.xlsx`. One column per curve (`curve_0001`, `curve_0002`, ...). Rows: 6 parameter rows (`t_start`, `t_A`, `A`, `B`, `t_B`, `t_end`) followed by one row per month (`Month_1` ... `Month_N`).

**Key parameters to edit (`config.py`):**
- `T_END_YEARS`, `T_B_YEAR`: retirement age — **65 for men, 60 for women**
- `T_START_YEARS`: starting age (default: 25)
- `T_A_YEARS_VALUES`: possible transition start ages
- `A_MIN`, `A_MAX`, `A_STEP`: range of initial CVaR limits (high-risk phase)
- `B_MIN`, `B_MAX`, `B_STEP`: range of final CVaR limits (low-risk phase)
- `FLAT_LEVELS`: CVaR levels for constant-risk glidepaths (set to `[]` to disable)

---

### `02_hit_and_run` — CVaR-Constrained Portfolio Sampler

For each glidepath curve and each month in the horizon, generates a large sample of portfolio weight vectors whose CVaR is strictly below the curve's CVaR limit for that month. Uses the Hit-and-Run MCMC algorithm to sample uniformly from the feasible region.

**Input:**
- `returns.csv`: historical asset returns (CSV, date index, one column per asset)
- `outputs/glidepaths_universe.xlsx`: output of module 01

**Output:** One HDF5 file per curve at `outputs/hit_and_run_matrices/curve_XXXX.h5`. Each file contains a dataset `weights` of shape `(HORIZON_MONTHS, N_PORTFOLIOS, N_ASSETS)`.

**Key parameters to edit (`main.py`):**
- `HORIZON_MONTHS`: **480 for men (40 years), 420 for women (35 years)** — must match module 01 output
- `SIMULATION_METHOD`: `"copula"` (recommended) or `"mvn"`
- `ALPHA_CVAR`: CVaR confidence level (e.g., `0.90` = worst 10% tail)
- `N_PORTFOLIOS_PER_MONTH`: portfolios sampled per month per curve
- `N_TRAJ`: Monte Carlo scenarios used for CVaR evaluation
- `RETURNS_SEED`: **must be kept identical in module 03**
- `CURVE_START`, `CURVE_END`: set to `None` to process all curves (or a curve name to resume)
- `N_PROCESSES`: number of parallel CPU processes

**Critical:** `RETURNS_SEED` and `SIMULATION_METHOD` must be identical to the values used in module 03.

---

### `03_scenario_evaluator` — Portfolio Trajectory Evaluator

For each glidepath curve, evaluates the annualized cumulative return of every portfolio trajectory under many independent market scenario draws. Produces a matrix of `(N_SEEDS × N_PORTFOLIOS)` annualized returns per curve.

**Input:**
- `returns.csv`: same file used in module 02
- `outputs/hit_and_run_matrices/curve_XXXX.h5`: output of module 02

**Output:** One HDF5 file per curve at `outputs/scenario_results/curve_XXXX.h5`. Each file contains a dataset `annualized_returns` of shape `(N_SEEDS, N_PORTFOLIOS)`.

**Key parameters to edit (`main.py`):**
- `HORIZON_MONTHS`: **480 for men, 420 for women** — must match module 02 exactly
- `RETURNS_SEED`, `SIMULATION_METHOD`, `N_TRAJ`: **must match module 02 exactly**
- `SCENARIO_SEEDS`: list of seeds for market scenario draws (default: 1–10,000)
- `SHUFFLE_SEED`: seed for within-month portfolio permutation (keep fixed at 42)
- `PROCESS_ALL_CURVES`: set to `True` to process all available curves (recommended default)

**Why the shuffle matters:** The Hit-and-Run algorithm produces autocorrelated portfolios within each month. Shuffling independently within each month (with a fixed seed) breaks this autocorrelation so that each trajectory across months is statistically independent.

---

### `04_full_pool_analyzer` — Full Pool Scenario Analyzer

Reads all scenario result files from module 03 and produces a single Excel file summarizing each curve's performance. All statistics are computed over the full `(N_SEEDS × N_PORTFOLIOS)` pool of observations without intermediate averaging, treating every `(scenario, portfolio)` pair as an independent outcome.

**Input:**
- `outputs/glidepaths_universe.xlsx`: output of module 01 (for curve parameters and CVaR limits)
- `outputs/scenario_results/curve_XXXX.h5`: output of module 03

**Output:** `outputs/analysis_full_pool/analysis_full_pool.xlsx`. One row per curve. Columns: curve parameters, pool metadata, `cumulative_risk`, return statistics (mean, std, min, max, percentiles), and one `pct_above_X%` column per threshold.

**Key parameters to edit (`main.py`):**
- `TARGET_RETURN_THRESHOLDS`: set using the `Required Return (%)` values from module 00 — each threshold becomes one `pct_above_X.XX%` column interpretable as pension adequacy probability
- `PERCENTILES`: percentiles computed over the full pool
- `SORT_BY`: column used to sort the output rows (default: `"cumulative_risk"`)
- `PROCESS_ALL_CURVES`: `True` to process all available curves (recommended default)
- `OUTPUT_LABEL`: optional suffix appended to the output filename

---

## Required Input File

### `returns.csv`

Place this file at the repository root before running modules 02 and 03.

- **Format:** CSV with comma separator
- **Index:** First column must be a date (parsed automatically)
- **Columns:** One column per asset; column headers become asset names throughout the pipeline
- **Values:** Monthly returns as decimals (e.g., `0.012` for 1.2%)
- **Minimum:** At least 2 asset columns

---

## Execution Order

```bash
# Step 0 (standalone): compute required returns for pension calibration
# Run this before step 4 to get the TARGET_RETURN_THRESHOLDS values
python -m 00_target_return.main

# Step 1: generate glidepath universe
python -m 01_glidepath_generator.main

# Step 2: sample portfolios (computationally intensive)
python -m 02_hit_and_run.main

# Step 3: evaluate scenarios (computationally intensive)
python -m 03_scenario_evaluator.main

# Step 4: aggregate and export final results
python -m 04_full_pool_analyzer.main
```

Modules 02 and 03 are the most computationally demanding. Module 02 supports resuming interrupted runs via `CURVE_START` / `CURVE_END`. Module 03 supports partial processing via `CURVES_TO_PROCESS`. Both allow distributing work across machines.

---

## Seed Consistency Requirements

These parameters must be kept identical across modules 02 and 03:

| Parameter | Module 02 | Module 03 | Effect if mismatched |
|---|---|---|---|
| `RETURNS_SEED` | 111 | 111 | Different return scenarios; CVaR constraints become inconsistent with evaluation |
| `SIMULATION_METHOD` | `"copula"` | `"copula"` | Different return distributions; results not comparable |
| `N_TRAJ` | 10_000 | 10_000 | Different scenario count; index selection breaks |
| `HORIZON_MONTHS` | 480 | 480 | Shape mismatch; module 03 will crash |

`HIT_RUN_SEED` (module 02) and `SHUFFLE_SEED`, `SCENARIO_SEEDS` (module 03) are independent of each other.

---

## Output Summary

| File | Module | Description |
|---|---|---|
| `outputs/target_return.xlsx` | 00 | Required returns by demographic profile |
| `outputs/glidepaths_universe.xlsx` | 01 | Full universe of CVaR glidepath curves |
| `outputs/hit_and_run_matrices/curve_XXXX.h5` | 02 | Weight tensors `(HORIZON_MONTHS × N_portfolios × N_assets)` per curve |
| `outputs/scenario_results/curve_XXXX.h5` | 03 | Annualized return matrices `(N_seeds × N_portfolios)` per curve |
| `outputs/analysis_full_pool/analysis_full_pool.xlsx` | 04 | Final ranked comparison of all curves |
