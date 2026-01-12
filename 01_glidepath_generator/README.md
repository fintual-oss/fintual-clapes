# 01_glidepath_generator - CVaR Glidepath Universe Generator

## Overview

This module generates all possible CVaR (Conditional Value at Risk) glidepath curves based on the parameters you define. A CVaR glidepath is a rule that says "how much risk am I allowed to take at each age?" The rule starts with higher risk tolerance when you are young, then gradually transitions to lower risk as you approach retirement.

The output is a single Excel file containing all the different glidepath combinations. Each combination represents a different strategy for reducing risk over time. These glidepaths will be used in step 02 to generate actual portfolio trajectories.

## What is a CVaR Glidepath?

A CVaR glidepath defines the maximum allowed risk (measured by CVaR) at each point in time. It has three phases:

1. **Constant high risk phase**: From starting age until transition age (t_A), the CVaR limit stays constant at level A
2. **Transition phase**: From age t_A to age t_B, the CVaR limit decreases linearly from A to B
3. **Constant low risk phase**: From age t_B onwards, the CVaR limit stays constant at level B

For example, with A=0.08, B=0.05, t_A=45 years, t_B=65 years:
- Ages 25-45: Maximum CVaR is 8% (constant, higher risk when young)
- Ages 45-65: CVaR decreases gradually from 8% to 5% (transition to safety)
- Ages 65+: Maximum CVaR is 5% (constant, lower risk at retirement)

## File Structure

```
01_glidepath_generator/
├── config.py            # Configuration parameters (EDIT THIS FILE)
├── main.py              # Main execution script
├── cvar_piecewise.py    # Function that calculates CVaR at any age
├── param_grid.py        # Generates all valid parameter combinations
├── universe.py          # Builds the full universe of curves
├── utils.py             # Utility function for creating numeric grids
├── routes.py            # Path management
└── __init__.py          # Package documentation
```

## Configuration Parameters

All parameters are defined in `config.py`. Edit this file to change the glidepath universe.

### Age Parameters

```python
T_START_YEARS = 25   # Starting age (when investment begins)
T_END_YEARS = 65     # Retirement age (when investment ends)
T_B_YEAR = 65        # Age when transition to final CVaR ends
```

**What they mean:**
- `T_START_YEARS`: The age when the person starts investing (typically 20-35)
- `T_END_YEARS`: The age when the person retires (typically 60-70)
- `T_B_YEAR`: The age when the CVaR finishes transitioning to its final value (usually equals retirement age)

**Derived values** (calculated automatically):
- `T_START_MONTHS`: Starting age in months (T_START_YEARS × 12)
- `T_END_MONTHS`: Retirement age in months (T_END_YEARS × 12)
- `MONTHS`: Total number of months in the horizon (T_END_MONTHS - T_START_MONTHS)

**Example:** If T_START_YEARS=25 and T_END_YEARS=65, then MONTHS=480 (40 years × 12 months/year)

### Transition Start Age

```python
T_A_YEARS_VALUES = list(range(35, 51))
```

**What it means:** This defines all the possible ages when the transition from high risk to low risk can begin. The code will create one glidepath for each value in this list.

**Current setting:** `list(range(35, 51))` creates the values [35, 36, 37, ..., 50], which is 16 different ages.

**Constraint:** t_A must be less than T_B_YEAR (transition must start before it ends)

### Initial CVaR Limit (when young)

```python
A_MIN, A_MAX, A_STEP = 0.05, 0.10, 0.01
```

**What it means:** This defines the range of possible CVaR limits for young ages (before the transition begins).

**Current setting:** Creates values [0.05, 0.06, 0.07, 0.08, 0.09, 0.10], which is 6 different levels.

**Components:**
- `A_MIN`: Minimum CVaR limit (0.05 = 5% risk)
- `A_MAX`: Maximum CVaR limit (0.10 = 10% risk)
- `A_STEP`: Step size between values (0.01 = 1% increments)

**How to modify:**
- For a single fixed value: `A_MIN=0.08, A_MAX=0.08, A_STEP=0.01` creates only [0.08]
- For finer steps: `A_MIN=0.06, A_MAX=0.10, A_STEP=0.005` creates [0.060, 0.065, 0.070, ...]

### Final CVaR Limit (at retirement)

```python
B_MIN, B_MAX, B_STEP = 0.03, 0.03, 0.01
```

**What it means:** This defines the range of possible CVaR limits at retirement age (after the transition is complete).

**Current setting:** Creates only [0.03], which means all glidepaths will end at 3% CVaR.

**Components:**
- `B_MIN`: Minimum CVaR limit (0.03 = 3% risk)
- `B_MAX`: Maximum CVaR limit (0.03 = 3% risk)
- `B_STEP`: Step size between values

**How to modify:**
- For multiple values: `B_MIN=0.03, B_MAX=0.07, B_STEP=0.01` creates [0.03, 0.04, 0.05, 0.06, 0.07]
- For a single value: Keep B_MIN = B_MAX

**Constraint:** A must be greater than or equal to B (risk must decrease or stay constant, never increase)

### Output Filename

```python
OUTPUT_XLSX = "glidepaths_universe.xlsx"
```

**What it means:** The name of the Excel file that will be created in the `outputs/` directory.

## Automatic Constraints

The code automatically enforces two important rules:

1. **A ≥ B**: The CVaR limit must decrease or stay constant as you age (it cannot increase)
2. **t_A < t_B**: The transition must start before it ends

Any combination that violates these rules is automatically excluded from the output.

## How to Run

```bash
python -m 01_glidepath_generator.main
```

Or, if you are inside the `01_glidepath_generator/` directory:

```bash
python main.py
```

## Output File

**Location:** `outputs/glidepaths_universe.xlsx`

**Structure:**

The Excel file has one sheet with the following structure:
- **Columns:** Each column represents one glidepath curve (curve_0001, curve_0002, etc.)
- **Rows:** Parameter values followed by monthly CVaR limits

**Row contents:**
1. `t_start`: Starting age in years (same for all curves)
2. `t_A`: Transition start age in years (varies across curves)
3. `A`: Initial CVaR limit as decimal (varies across curves)
4. `B`: Final CVaR limit as decimal (varies across curves)
5. `t_B`: Transition end age in years (same for all curves)
6. `t_end`: Retirement age in years (same for all curves)
7. `Month_1`: CVaR limit for month 1
8. `Month_2`: CVaR limit for month 2
9. ... (continues for all months in the horizon)
10. `Month_N`: CVaR limit for month N (where N = MONTHS, e.g., 480 for a 40-year horizon)

**Example:**

```
              curve_0001  curve_0002  curve_0003  curve_0004
t_start            25          25          25          25
t_A                35          35          35          35
A                0.05        0.06        0.07        0.08
B                0.03        0.03        0.03        0.03
t_B                65          65          65          65
t_end              65          65          65          65
Month_1          0.05        0.06        0.07        0.08
Month_2          0.05        0.06        0.07        0.08
...               ...         ...         ...         ...
Month_480        0.03        0.03        0.03        0.03
```

## How It Works

### Step 1: Generate Parameter Grid

The code creates all valid combinations of (t_A, A, B) by:

1. Taking each value from T_A_YEARS_VALUES
2. Taking each value from A range (A_MIN to A_MAX in steps of A_STEP)
3. Taking each value from B range (B_MIN to B_MAX in steps of B_STEP)
4. Keeping only combinations where A ≥ B and t_A < T_B_YEAR

**Example:** If you have:
- 16 values for t_A (ages 35-50)
- 6 values for A (0.05 to 0.10)
- 1 value for B (0.03)

Then you get 16 × 6 × 1 = 96 total curves (all valid because A ≥ B is always satisfied)

### Step 2: Calculate Monthly CVaR Values

For each valid combination, the code calculates the CVaR limit at each month using this logic:

```
For each month m (from month 1 to month MONTHS):
    Calculate age_m = age in months at month m
    
    If age_m ≤ t_A (in months):
        CVaR(m) = A  (constant before transition)
    
    Else if t_A < age_m ≤ t_B (in months):
        CVaR(m) = A + slope × (age_m - t_A)
        where slope = (B - A) / (t_B - t_A)
        (linear transition from A to B)
    
    Else (age_m > t_B):
        CVaR(m) = B  (constant after transition)
```

**Example:** For A=0.08, B=0.05, t_A=45 years (540 months from birth), t_B=65 years (780 months from birth):
- If starting at age 25 (300 months from birth):
  - Months 1-240 (ages 25-45): CVaR = 0.08
  - Months 241-480 (ages 45-65): CVaR decreases linearly from 0.08 to 0.05
  - Beyond month 480 (age 65+): CVaR = 0.05 (if extended beyond retirement)

### Step 3: Export to Excel

All curves are saved in a single Excel file where:
- Each column is one complete glidepath
- Each row contains either a parameter value or a monthly CVaR limit
- The file can be easily loaded by step 02 for portfolio simulation

## Understanding the Output

### How many curves are generated?

Total number of curves = (number of t_A values) × (number of A values) × (number of B values)

**With current default settings:**
- t_A values: 16 (from 35 to 50)
- A values: 6 (from 0.05 to 0.10)
- B values: 1 (only 0.03)
- Total: 16 × 6 × 1 = 96 curves

### What do the monthly values represent?

Each monthly value is the maximum CVaR allowed for a portfolio at that month. In step 02, the portfolio simulator will generate portfolios that satisfy this constraint.

For example, if `Month_120 = 0.07` for a curve, this means that at month 120 (age 35 if starting at 25), any portfolio generated must have CVaR less than or equal to 7%.

### Values are in decimal form

- 0.05 = 5%
- 0.08 = 8%
- 0.10 = 10%

## Next Step

After running this module, proceed to step 02 (portfolio_simulator) to generate portfolio trajectories for each glidepath curve.
