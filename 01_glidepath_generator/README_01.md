# 01_glidepath_generator — CVaR Glidepath Universe Generator

## Overview

This module generates all possible CVaR (Conditional Value at Risk) glidepath curves based on the parameters defined in `config.py`. A CVaR glidepath is a rule that says "how much risk am I allowed to take at each age?" The rule starts with higher risk tolerance when young, then gradually transitions to lower risk as the person approaches retirement.

The output is a single Excel file containing all glidepath combinations. Each combination represents a different strategy for reducing risk over time. These glidepaths are consumed by step 02 to generate actual portfolio trajectories.

## What is a CVaR Glidepath?

A CVaR glidepath defines the maximum allowed risk (measured by CVaR) at each point in time. It has three phases:

1. **Constant high-risk phase**: From starting age until transition age (t_A), the CVaR limit stays constant at level A.
2. **Transition phase**: From age t_A to age t_B, the CVaR limit decreases linearly from A to B.
3. **Constant low-risk phase**: From age t_B onwards, the CVaR limit stays constant at level B.

Example with A=0.08, B=0.05, t_A=40, t_B=65:
- Ages 25–40: Maximum CVaR is 8% (constant, higher risk when young)
- Ages 40–65: CVaR decreases gradually from 8% to 5% (linear transition)
- Ages 65+: Maximum CVaR is 5% (constant, lower risk at retirement)

## File Structure

```
01_glidepath_generator/
├── config.py          # Configuration parameters (EDIT THIS FILE)
├── main.py            # Main execution script
├── cvar_piecewise.py  # Calculates CVaR value at any given age in months
├── param_grid.py      # Generates all valid parameter combinations
├── universe.py        # Builds the full DataFrame of glidepath curves
├── utils.py           # Utility: numeric grid generation
├── routes.py          # Output path management
└── __init__.py        # Package documentation
```

## Configuration for Gender Profiles

**This is the most important section if you are switching between male and female runs.**

The two key parameters that differ by gender are:

| Parameter | Men | Women | Meaning |
|-----------|-----|-------|---------|
| `T_END_YEARS` | 65 | 60 | Legal retirement age |
| `T_B_YEAR` | 65 | 60 | Age when CVaR finishes transitioning |

Edit these two values in `config.py` before running:

```python
# For MEN (current default):
T_END_YEARS = 65
T_B_YEAR    = 65

# For WOMEN:
T_END_YEARS = 60
T_B_YEAR    = 60
```

Changing these values automatically adjusts:
- `MONTHS` = (T_END_YEARS − T_START_YEARS) × 12 — total months in the horizon
- The number of monthly CVaR columns in the output file
- The valid range of t_A values (t_A must be less than T_B_YEAR)

You may also want to review `T_A_YEARS_VALUES` to ensure the transition start ages make sense for the chosen retirement age.

## Configuration Parameters

All parameters are defined in `config.py`.

### Age Parameters

```python
T_START_YEARS = 25   # Age when the person starts investing
T_END_YEARS   = 65   # Retirement age (65 for men, 60 for women)
T_B_YEAR      = 65   # Age when the CVaR transition ends (usually = T_END_YEARS)
```

Derived values (calculated automatically from the above):
- `T_START_MONTHS` = T_START_YEARS × 12
- `T_END_MONTHS` = T_END_YEARS × 12
- `MONTHS` = T_END_MONTHS − T_START_MONTHS (total months in the horizon)

### Transition Start Age

```python
T_A_YEARS_VALUES = list(range(30, 66))
```

All possible ages when the transition from high to low risk can begin. The module generates one glidepath per valid combination that includes each value in this list. The constraint t_A < T_B_YEAR is enforced automatically — invalid combinations are silently skipped.

### CVaR Level Ranges

```python
# Initial CVaR (high risk, before transition)
A_MIN, A_MAX, A_STEP = 0.05, 0.10, 0.01   # → [0.05, 0.06, 0.07, 0.08, 0.09, 0.10]

# Final CVaR (low risk, after transition)
B_MIN, B_MAX, B_STEP = 0.03, 0.03, 0.01   # → [0.03]
```

For declining glidepaths, only combinations where A > B are kept. To test a wider range of B values, change B_MAX:

```python
B_MIN, B_MAX, B_STEP = 0.03, 0.07, 0.01   # → [0.03, 0.04, 0.05, 0.06, 0.07]
```

### Flat Glidepath Levels

```python
FLAT_LEVELS = []   # Set to e.g. [0.05, 0.06, 0.07] to enable flat glidepaths
```

Flat glidepaths have A = B (constant risk throughout the horizon). When set to `[]`, no flat glidepaths are generated.

### Output Filename

```python
OUTPUT_XLSX = "glidepaths_universe.xlsx"
```

Name of the Excel file written to `outputs/`.

## How to Run

```bash
python -m 01_glidepath_generator.main
```

Or from inside the module directory:

```bash
python main.py
```

## How It Works

### Step 1 — Generate parameter grid (`param_grid.py`)

Two types of glidepaths are generated:

**Declining (A > B):** all combinations of t_A × A × B where A > B and t_A < T_B_YEAR.

**Flat (A = B):** one curve per level in `FLAT_LEVELS`.

### Step 2 — Calculate monthly CVaR values (`cvar_piecewise.py`, `universe.py`)

For each valid combination, the CVaR limit is computed at every month using the piecewise formula:

```
age_m = age in months at month m

if age_m ≤ t_A_months:          CVaR = A
if t_A_months < age_m ≤ t_B_months:  CVaR = A + slope × (age_m − t_A_months)
                                       where slope = (B − A) / (t_B_months − t_A_months)
if age_m > t_B_months:          CVaR = B
```

### Step 3 — Export to Excel (`main.py`, `routes.py`)

All curves are written to a single Excel sheet where each column is one glidepath and each row is either a parameter or a monthly CVaR value.

## Output File

**Location:** `outputs/glidepaths_universe.xlsx`

**Structure:**

| Row | Content |
|-----|---------|
| `t_start` | Starting age in years |
| `t_A` | Transition start age in years |
| `A` | Initial CVaR limit (decimal) |
| `B` | Final CVaR limit (decimal) |
| `t_B` | Transition end age in years |
| `t_end` | Retirement age in years |
| `Month_1` … `Month_N` | CVaR limit for each month (N = MONTHS) |

Each column is one curve named `curve_0001`, `curve_0002`, etc.

### How many curves are generated?

With the current default configuration (men, T_END_YEARS=65):

| Component | Values |
|-----------|--------|
| t_A values | 36 (range 30–65) |
| A values | 6 (0.05 to 0.10) |
| B values | 1 (0.03) |
| Flat levels | 0 (disabled) |
| **Total** | **36 × 6 × 1 = 216 declining curves** |

For women (T_END_YEARS=60), the valid t_A range shrinks (t_A < 60), which reduces the number of curves. Recount after changing the configuration.

## Next Step

After running this module, proceed to step 02 to generate portfolio trajectories for each glidepath curve.
