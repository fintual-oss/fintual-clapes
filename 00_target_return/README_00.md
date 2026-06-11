# 00_target_return - Chilean Pension System Required Return Calculator

## Overview

This module calculates the annual investment return required to achieve a target pension replacement rate in the Chilean AFP pension system. It simulates four demographic profiles (male/female, with/without contribution gaps) and uses binary search to find the exact return that produces a pension equal to a target replacement rate of average pre-retirement salary.

This module is independent of the main pipeline (steps 01–04). Its output is not consumed automatically by any other module. Instead, the required return values it produces serve as reference benchmarks to manually calibrate `TARGET_RETURN_THRESHOLDS` in step 04, which allows interpreting portfolio results in terms of actual pension adequacy.

## What Does This Module Do?

For each of the four demographic profiles, the module:

1. Simulates the full accumulation phase month by month (from start of work to retirement), applying contributions, contribution density, salary growth, and investment returns.
2. Converts the accumulated balance at retirement into a monthly pension using an annuity formula.
3. Uses binary search to find the annual return that makes the pension exactly equal to a target replacement rate of average pre-retirement salary.
4. Exports a comprehensive Excel report with results, monthly detail, sensitivity analysis, and parameters.

## Connection to Step 04

This module provides the calibration input for `TARGET_RETURN_THRESHOLDS` in `04_full_pool_analyzer`. The workflow is:

1. Run this module to obtain the required return for each demographic profile.
2. Use those values as entries in `TARGET_RETURN_THRESHOLDS` in step 04.
3. Interpret step 04 results as: "X% of portfolio trajectories achieve the return needed for this demographic profile to retire with a Y% replacement rate."

## File Structure

```
00_target_return/
├── parameters.py    # Model parameters (EDIT THIS FILE)
├── formulas.py      # Simulation logic and pension calculations
├── exporters.py     # Excel export functionality
├── main.py          # Main execution script
└── __init__.py      # Package documentation
```

## Configuration Parameters

All parameters are defined in `parameters.py`.

### Demographic Parameters

```python
age_start_work_male   = 25    # Age when men start working
age_start_work_female = 25    # Age when women start working
age_retire_male       = 65    # Legal retirement age for men
age_retire_female     = 60    # Legal retirement age for women
life_expectancy_male  = 86    # Life expectancy for men
life_expectancy_female= 90    # Life expectancy for women
```

**What they mean:**
- `age_start_work`: When the person enters the workforce and begins contributing.
- `age_retire`: Legal retirement age in Chile (65 for men, 60 for women). Determines the end of the accumulation phase and the length of the working horizon.
- `life_expectancy`: Expected age at death. Determines the number of months the pension must be paid, which directly affects the monthly pension amount — a longer life expectancy results in a lower monthly pension for the same accumulated balance.

### Economic Parameters

```python
salary_initial_male   = 20.0   # Initial monthly salary in UF
salary_initial_female = 20.0   # Initial monthly salary in UF
contribution_rate     = 0.16   # Mandatory contribution rate (16%)
contribution_ceiling  = 87.8   # Maximum salary subject to contributions (UF)
salary_growth_real    = 0.0125 # Real annual salary growth (1.25%)
```

**What they mean:**
- `salary_initial`: Starting monthly salary in UF (Chilean inflation-indexed units). All monetary values in this model are in UF, which eliminates the need to model inflation separately — all returns and growth rates are real (above inflation).
- `contribution_rate`: Fraction of salary contributed to the pension fund each month (16% under current Chilean law).
- `contribution_ceiling`: Maximum monthly salary subject to contributions (87.8 UF is the official value). Salaries above this ceiling still grow, but contributions are capped.
- `salary_growth_real`: Annual real salary growth applied at the start of each year. Applies to all profiles regardless of contribution density.

### Return Parameters

```python
return_post_retirement = 0.032  # 3.2% real annual return after retirement
```

**What it means:** The real annual return applied to the remaining pension balance during the retirement phase. The return during the accumulation phase is not a parameter — it is what the binary search solves for.

### Target Parameters

```python
replacement_rate_target       = 0.63  # Target replacement rate (63%)
months_for_replacement_rate   = 120   # Months used to compute average pre-retirement salary
```

**What they mean:**
- `replacement_rate_target`: The pension must equal this fraction of the average pre-retirement salary. 0.63 means the target pension is 63% of the reference salary.
- `months_for_replacement_rate`: The number of months before retirement used to compute the reference salary. With `120`, the reference is the average salary over the last 10 years. With `12`, it is the average over the last year only.

**Effect of `months_for_replacement_rate`:**
- `12` (last year): The reference salary is at its peak, so the target pension is higher in absolute terms, which requires a higher required return.
- `120` (last 10 years): The reference includes lower historical salaries, so the average is lower and the required return is somewhat reduced.

**Replacement rate formula:**
```
Replacement Rate = Monthly Pension / mean(salary over last N months before retirement)
```

### Contribution Density

```python
contribution_density_male_no_gaps    = 1.0   # 100%
contribution_density_male_with_gaps  = 0.583  # 58.3%
contribution_density_female_no_gaps  = 1.0   # 100%
contribution_density_female_with_gaps= 0.496  # 49.6%
```

**What it means:** The fraction of months in which the person actually makes a pension contribution. Rather than modeling discrete unemployment spells, the density is applied uniformly each month as a multiplier on the base contribution:

```
contribution_effective = contribution_base × contribution_density
```

A density of 0.583 means the person contributes 58.3% of the full amount every month, which is equivalent on average to contributing fully for 58.3% of all months. Salary growth is applied independently of density — a person with gaps still experiences the same career salary progression.

### Binary Search Parameters

```python
return_min     = 0.0    # Lower bound of search interval (0%)
return_max     = 0.20   # Upper bound of search interval (20%)
tolerance      = 0.0001 # Convergence tolerance on replacement rate
max_iterations = 100    # Maximum iterations before stopping
```

**What they mean:** The binary search iterates within `[return_min, return_max]`, halving the interval each step. It stops when the simulated replacement rate is within `tolerance` of the target. If it does not converge within `max_iterations`, it returns the best approximation found.

## How to Run

```bash
python -m 00_target_return.main
```

Or, if you are inside the `00_target_return/` directory:

```bash
python main.py
```

## How It Works

### Step 1: Accumulation phase simulation (`formulas.py`)

For each month from the start of work to retirement:

1. **Salary update** (once per year, at the start of each 12-month block): `salary = salary × (1 + salary_growth_real)`. Applies regardless of contribution density.
2. **Contribution calculation**: `contribution_base = min(salary, contribution_ceiling) × contribution_rate`. Then: `contribution_effective = contribution_base × contribution_density`.
3. **Balance update**: `balance = (balance + contribution_effective) × (1 + monthly_return)`, where `monthly_return = (1 + annual_return)^(1/12) - 1`.
4. **Salary tracking**: The last `months_for_replacement_rate` monthly salaries are stored for the replacement rate calculation.

### Step 2: Pension calculation

At retirement, the accumulated balance is converted to a monthly pension using the ordinary annuity (annuity-immediate) formula:

```
PMT = PV × [r × (1 + r)^n] / [(1 + r)^n - 1]
```

Where:
- `PMT` = monthly pension
- `PV` = accumulated balance at retirement
- `r` = monthly return = `(1 + return_post_retirement)^(1/12) - 1`
- `n` = retirement months = `(life_expectancy - age_retire) × 12`

This formula produces the constant monthly payment that exactly depletes the balance at the end of the retirement period.

### Step 3: Binary search for required return

The binary search finds the accumulation return that makes the replacement rate equal to `replacement_rate_target`:

1. Start with interval `[return_min, return_max]`.
2. Test `return_mid = (return_min + return_max) / 2`.
3. Simulate accumulation, compute pension, compute replacement rate.
4. If replacement rate < target: raise lower bound (`return_min = return_mid`).
5. If replacement rate ≥ target: lower upper bound (`return_max = return_mid`).
6. Repeat until `|replacement_rate - target| < tolerance`.

### Step 4: Export (`exporters.py`)

Results are written to a single Excel file with 7 sheets.

## Output File

**Location:** `outputs/target_return.xlsx`

**7 sheets:**

**`Parameters`**: All parameter values used in the run, one row per parameter.

**`Summary`**: One row per demographic profile with key results.

| Column | Description |
|--------|-------------|
| `Profile` | Profile name |
| `Contribution Density (%)` | Density used for this profile |
| `Required Return (%)` | Annual return that achieves the target — use this in step 04 |
| `Achieved Replacement Rate (%)` | Replacement rate achieved with that return |
| `Final Accumulated Balance (UF)` | Balance at retirement |
| `Monthly Pension (UF)` | Monthly pension payment |
| `Average Salary Last N Months/Years (UF)` | Reference salary (column name reflects `months_for_replacement_rate`) |
| `Effective Contribution Years` | Total months × density / 12 |

**`Male_without_gaps`, `Male_with_gaps`, `Female_without_gaps`, `Female_with_gaps`**: Monthly detail of the accumulation phase for each profile.

| Column | Description |
|--------|-------------|
| `year` | Year number in the working career |
| `month` | Month number (1 to total months) |
| `age` | Age in years |
| `salary_uf` | Monthly salary in UF |
| `contribution_base_uf` | Base contribution before applying density |
| `contribution_density` | Density factor applied |
| `contribution_effective_uf` | Actual contribution credited to the fund |
| `balance_uf` | Accumulated fund balance |

**`Sensitivity Analysis`**: Replacement rate for each profile at annual returns from 0% to 15% in 1% increments. Useful for understanding how sensitive the replacement rate is to the return assumption.

## Profiles Simulated

The module always runs exactly four profiles:

| Profile | Gender | Density |
|---------|--------|---------|
| Male without gaps | Male | 100% |
| Male with gaps | Male | 60% |
| Female without gaps | Female | 100% |
| Female with gaps | Female | 60% |
