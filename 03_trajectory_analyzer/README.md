# 03_trajectory_analyzer - Portfolio Trajectory Performance Analysis

## Overview

This module analyzes the performance of all portfolio trajectories generated in step 02. It calculates how well each glidepath strategy performed by measuring cumulative returns, success rates, and cumulative risk exposure. The output is a single-sheet Excel report that helps identify which glidepath parameters lead to the best investment outcomes.

The module supports seven different analysis modes that allow transforming trajectories before analysis: original trajectories, sorted trajectories, permuted trajectories, and various combinations thereof.

The module calculates the cumulative risk of each glidepath by summing the CVaR limits from step 01. This represents the total risk exposure (area under the CVaR curve) inherent to each glidepath strategy.

## What Does This Module Do?

**Input:** 
- Portfolio trajectories from step 02 (monthly returns)
- Glidepath parameters from step 01 (A, B, t_A, t_B)
- CVaR limit curves from step 01 (monthly CVaR limits for each glidepath)

**Process:** 
- Apply trajectory transformation based on selected analysis mode
- Calculate cumulative annualized returns for each trajectory
- Calculate success rate (percentage of trajectories exceeding target return)
- Calculate cumulative risk from CVaR limits (area under the curve)
- Combine performance metrics with glidepath parameters
- Rank all curves by performance

**Output:** 
- Single Excel file with 1 sheet: summary of all curves with statistics and cumulative risk

## File Structure

```
03_trajectory_analyzer/
├── main.py              # Main execution script (EDIT PARAMETERS HERE)
├── routes.py            # Path management
├── loaders.py           # Load data from steps 01 and 02
├── metrics.py           # Calculate returns, statistics, percentiles
├── transformations.py   # Transform trajectories (permutation, sorting)
├── exporters.py         # Export results to Excel (1 sheet)
├── __init__.py          # Package documentation
└── README.md            # This file
```

## Configuration Parameters

All parameters are defined at the top of `main.py`. Edit this file to configure the analysis.

### Analysis Mode

```python
ANALYSIS_MODE = 3  # OPTIONS: 1, 2, 3, 4, 5, 6, or 7
```

The module supports seven analysis modes that apply different transformations to trajectories:

**Mode 1: Original Trajectories**
- Analyze trajectories exactly as generated in step 02
- No transformation applied
- Total trajectories: N

**Mode 2: Sorted Trajectories Only**
- Generate sorted trajectories by ranking returns within each month
- Trajectory 1 takes maximum return from each month
- Trajectory N takes minimum return from each month
- Total trajectories: N

**Mode 3: Permuted Trajectories Only (Current default)**
- Apply random permutation to returns within each month
- Maintains CVaR compliance (same pool of valid returns, different assignment)
- Total trajectories: N

**Mode 4: Permuted + Sorted Trajectories**
- Generate permuted trajectories (N)
- Generate sorted trajectories (N)
- Total trajectories: 2N

**Mode 5: Original + Sorted Trajectories**
- Maintain original trajectories (N)
- Generate sorted trajectories (N)
- Total trajectories: 2N

**Mode 6: Original + Permuted Trajectories**
- Maintain original trajectories (N)
- Generate permuted trajectories (N)
- Total trajectories: 2N

**Mode 7: Original + Sorted + Permuted Trajectories**
- Maintain original trajectories (N)
- Generate sorted trajectories (N)
- Generate permuted trajectories (N)
- Total trajectories: 3N

**Note on CVaR compliance:** Random permutation within each month maintains CVaR compliance because all returns for a given month satisfy that month's CVaR constraint. Permutation only changes which trajectory receives which return, preserving the distribution of valid returns.

### Random Seed

```python
RANDOM_SEED = 42  # Set to None for different results each run
```

**Purpose:** Controls randomness in permutation (modes 3, 4, 6, and 7 only)

**Usage:**
- Set to an integer (e.g., 42) for reproducible results
- Set to None for different permutations each run
- Not used in modes 1, 2, and 5

### Target Return Threshold

```python
TARGET_RETURN_THRESHOLD = 0.055  # 5.5% annual return
```

**What it means:** The minimum acceptable annualized return. This is used to determine if a trajectory is "successful" or not.

**How it's used:**
- Trajectories with annualized return > TARGET_RETURN_THRESHOLD are considered successful
- Used to calculate success rate (percentage of successful trajectories)

**How to set this value:** Use the required return from step 00 for the relevant demographic profile. The required return is the annual return needed to achieve a 63% replacement rate in the Chilean pension system.

**Current configuration:** 5.5% represents an approximate required return for a female profile with specific contribution density parameters. Adjust this value based on results from step 00 for your specific demographic profile of interest.

**Format:** Decimal (0.055 = 5.5% annual return)

### Percentiles

```python
PERCENTILES = [10, 25, 50, 75, 90]
```

**What it means:** Which percentiles of the return distribution to calculate.

**How to modify:**
- For more detail: `[5, 10, 25, 50, 75, 90, 95]`
- For less detail: `[25, 50, 75]` (just quartiles)
- Values must be integers between 0 and 100

### Curve Selection

```python
PROCESS_ALL_CURVES = True  # Analyze all available curves

CURVES_TO_ANALYZE = [      # Only used if PROCESS_ALL_CURVES = False
    "curve_0001",
    "curve_0002",
    "curve_0003"
]
```

**What it means:**

**PROCESS_ALL_CURVES = True:**
- Analyze every curve that has results from step 02
- Use this for complete analysis

**PROCESS_ALL_CURVES = False:**
- Analyze only the curves listed in CURVES_TO_ANALYZE
- Use this for quick checks or specific curve analysis

## How to Run

```bash
python -m 03_trajectory_analyzer.main
```

Or, if you are inside the `03_trajectory_analyzer/` directory:

```bash
python main.py
```

### Prerequisites

Before running, ensure these files exist:

1. `outputs/glidepaths_universe.xlsx` (from step 01)
2. `outputs/hit_run_results/curve_XXXX_results.xlsx` (from step 02)

## Output File

**Location:** `outputs/trajectory_analysis_summary.xlsx`

**Structure:** 1 sheet

### Sheet: "results" - Summary of All Curves

This sheet has one row per curve, sorted by performance. It combines glidepath parameters with performance metrics and cumulative risk.

**Columns:**

**Glidepath Parameters:**
- `curve_id`: Curve identifier (e.g., curve_0001)
- `t_start`: Starting age in years (e.g., 25)
- `t_A`: Transition start age in years (e.g., 45)
- `A`: Initial CVaR limit when young (e.g., 0.08)
- `B`: Final CVaR limit at retirement (e.g., 0.03)
- `t_B`: Transition end age in years (e.g., 60 for female, 65 for male)
- `t_end`: Retirement age in years (e.g., 60 for female, 65 for male)

**Data Summary:**
- `n_trajectories`: Number of trajectories analyzed (N, 2N, or 3N depending on mode)
- `horizon_months`: Investment horizon in months (e.g., 420 for female profile)
- `analysis_mode`: Analysis mode used (1, 2, 3, 4, 5, 6, or 7)

**Risk Metric:**
- `cumulative_risk`: Sum of all monthly CVaR limits from step 01 (area under the CVaR curve)

**Performance Metrics:**
- `return_mean`: Average annualized return across all trajectories (e.g., 0.0523 = 5.23%)
- `return_std`: Standard deviation of returns (e.g., 0.0087 = 0.87%)
- `return_min`: Worst trajectory return (e.g., 0.0312 = 3.12%)
- `return_max`: Best trajectory return (e.g., 0.0701 = 7.01%)
- `pct_above_target`: Percentage of trajectories exceeding target (e.g., 0.87 = 87%)

**Return Distribution:**
- `return_p10`: 10th percentile return (e.g., 0.0401 = 4.01%)
- `return_p25`: 25th percentile return (e.g., 0.0456 = 4.56%)
- `return_p50`: 50th percentile return / median (e.g., 0.0519 = 5.19%)
- `return_p75`: 75th percentile return (e.g., 0.0589 = 5.89%)
- `return_p90`: 90th percentile return (e.g., 0.0643 = 6.43%)

**Example (female profile with 420 months):**
```
curve_id  t_A   A      B      cumulative_risk  return_mean  pct_above_target  return_p50  analysis_mode
curve_0042  45  0.08  0.03      24.80           0.0523         0.87            0.0519           3
curve_0015  46  0.09  0.03      26.25           0.0498         0.82            0.0495           3
curve_0089  44  0.07  0.03      23.35           0.0545         0.91            0.0542           3
```

**Note:** cumulative_risk values are lower for 420-month horizon (female) compared to 480-month horizon (male).

**Sorting:** Rows are sorted by:
1. `pct_above_target` (descending) - curves with more successful trajectories first
2. `return_mean` (descending) - higher average returns second

**Interpretation:**
- Rows are sorted by success rate (pct_above_target) and mean return
- Compare parameters (A, t_A, B) across top rows to identify optimal strategies
- Review cumulative_risk to understand total risk exposure
- Examine percentiles to understand return distribution

## How It Works

### Step-by-Step Process

**Step 1: Load Glidepath Parameters**
- Read `glidepaths_universe.xlsx` from step 01
- Extract parameters: t_start, t_A, A, B, t_B, t_end

**Step 2: Load CVaR Limits**
- Read monthly CVaR limits from step 01
- These are used to calculate cumulative risk (area under curve)

**Step 3: Find Available Trajectories**
- Scan `outputs/hit_run_results/` for result files
- List all curves with available trajectory data

**Step 4: Analyze Each Curve**

For each curve:

**a. Load Trajectory Data**

```
File format:
- File is stored as (N_TRAJECTORIES × MONTHS) - rows=trajectories, columns=months
- After loading, data is TRANSPOSED to (MONTHS × N_TRAJECTORIES) for calculations
- returns_df: monthly returns (420 rows × 10000 columns after transpose for female profile)

After transpose:
- Each column is one trajectory
- Each row is one month
```

**b. Apply Transformation**

Based on ANALYSIS_MODE:

**Mode 1: No transformation**
```
Use original trajectories as-is
```

**Mode 2: Generate sorted trajectories**
```
For each month:
  Sort returns across all trajectories (descending)
  Sorted trajectory 1 gets: max return from each month
  Sorted trajectory 2 gets: 2nd max return from each month
  ...
  Sorted trajectory N gets: min return from each month
```

**Mode 3: Generate permuted trajectories (Current default)**
```
For each month:
  Randomly shuffle returns across trajectories
  This maintains CVaR compliance (same returns, different assignment)
```

**Mode 4: Generate permuted + sorted trajectories**
```
Step 1: Random permutation
  For each month:
    Randomly shuffle returns across trajectories

Step 2: Generate sorted trajectories
  Apply same sorting logic as Mode 2

Result: 2N trajectories total (N permuted + N sorted)
```

**Mode 5: Generate original + sorted trajectories**
```
Step 1: Keep original trajectories

Step 2: Generate sorted trajectories
  Apply same sorting logic as Mode 2

Result: 2N trajectories total (N original + N sorted)
```

**Mode 6: Generate original + permuted trajectories**
```
Step 1: Keep original trajectories

Step 2: Generate permuted trajectories
  For each month: Randomly shuffle returns

Result: 2N trajectories total (N original + N permuted)
```

**Mode 7: Generate original + sorted + permuted trajectories**
```
Step 1: Keep original trajectories

Step 2: Generate sorted trajectories
  Apply same sorting logic as Mode 2

Step 3: Generate permuted trajectories
  For each month: Randomly shuffle returns

Result: 3N trajectories total (N original + N sorted + N permuted)
```

**Why permutation respects CVaR constraints:**

In step 02, all portfolios generated for a given month satisfy that month's CVaR limit. The specific return each portfolio achieves is determined by:
1. The portfolio weights (which satisfy CVaR)
2. The scenario/path taken through the return distribution

By permuting returns within a month, we:
- Keep the same pool of valid returns (all CVaR-compliant)
- Just reassign which trajectory gets which return
- This is equivalent to having chosen different scenarios in step 02

**c. Calculate Cumulative Annualized Returns**

For each trajectory (each column of transformed returns):

1. Calculate cumulative return by compounding monthly returns:
   ```
   cumulative_return = ∏(1 + r_monthly) - 1
   ```
   Example: If monthly returns are [0.01, 0.02, -0.01], then:
   ```
   cumulative = (1.01)(1.02)(0.99) - 1 = 0.0198
   ```

2. Annualize the cumulative return:
   ```
   annualized_return = (1 + cumulative_return)^(12/T) - 1
   ```
   where T is the number of months

   Example with 420 months (female profile): If cumulative return over 420 months is 1.50 (150%), then:
   ```
   annualized = (1 + 1.50)^(12/420) - 1 = (2.50)^0.0286 - 1 = 0.0267 = 2.67% per year
   ```

This produces one annualized return value per trajectory.

**d. Calculate Summary Statistics**

Using the annualized returns:
```
return_mean = average of all annualized returns
return_std = standard deviation of annualized returns
return_min = minimum annualized return
return_max = maximum annualized return
pct_above_target = (count of returns > TARGET_RETURN_THRESHOLD) / total count
```

**e. Calculate Percentiles**

Sort the annualized returns and find values at specified percentiles.

Example with 1000 trajectories and percentile 10:
```
Sort returns: [0.02, 0.025, 0.028, ..., 0.065, 0.070]
p10 = value at position 100 (10% of 1000)
```

**f. Calculate Cumulative Risk from Step 01**

For this curve, sum the CVaR limits from step 01:
```
cvar_limits = [Month_1, Month_2, ..., Month_420]  # For female profile
cumulative_risk = sum(cvar_limits)
```

Example with 420 months: If CVaR limits are [0.08, 0.08, 0.08, ..., 0.03], then:
```
cumulative_risk = 0.08 + 0.08 + 0.08 + ... + 0.03 = 24.80
```

This represents the area under the CVaR glidepath curve from step 01.

**Note:** Cumulative risk values are lower for shorter horizons (420 months vs 480 months).

**g. Combine with Parameters**

Merge the performance metrics with the glidepath parameters (A, B, t_A, etc.) and cumulative risk for this curve.

**Step 5: Create Summary DataFrame**

Combine results from all curves into a single DataFrame with all columns:
- Glidepath parameters (t_start, t_A, A, B, t_B, t_end)
- Data summary (n_trajectories, horizon_months, analysis_mode)
- Cumulative risk (from step 01)
- Performance metrics (return_mean, return_std, return_min, return_max, pct_above_target)
- Return percentiles (return_p10, return_p25, return_p50, return_p75, return_p90)

**Step 6: Sort Results**

Sort the DataFrame by:
1. `pct_above_target` (descending) - most successful curves first
2. `return_mean` (descending) - highest average return as tiebreaker

**Step 7: Export to Excel**

Write 1 sheet to Excel file:
- Sheet: 'results' - Summary of all curves with statistics and cumulative risk

## Metrics Explained

### Cumulative Annualized Return

**Purpose:** Convert a multi-year investment into a single comparable number.

**Why annualize?**
- Different horizons are hard to compare directly
- A 35-year return of 150% is different from a 20-year return of 150%
- Annualizing puts everything on "per year" basis

**Formula:**
```
Step 1: Cumulative return = ∏(1 + r_t) - 1
Step 2: Annualized return = (1 + cumulative)^(12/T) - 1
```

### Success Rate (pct_above_target)

**Purpose:** Measure the probability of achieving your investment goal.

**Formula:**
```
pct_above_target = (number of trajectories with return > target) / total trajectories
```

**Interpretation:**
- Higher values indicate more successful strategy
- Compare across curves to identify most reliable glidepaths

### Cumulative Risk (Area Under CVaR Curve)

**Purpose:** Quantify the total CVaR exposure of each glidepath strategy.

**Formula:**
```
cumulative_risk = Σ CVaR_limit_t  for t = 1 to T
```

This is the sum of all monthly CVaR limits from the glidepath curve in step 01.

**Interpretation:**
- Higher cumulative risk = glidepath allows more risk throughout the investment horizon
- Lower cumulative risk = glidepath is more conservative overall
- Values scale with horizon length (420 months produces lower values than 480 months)

### Return Percentiles

**Purpose:** Understand the distribution of outcomes beyond just the mean.

**Interpretation:**
- `return_p10`: Only 10% of trajectories did worse than this
- `return_p25`: First quartile (25% did worse)
- `return_p50`: Median return (half did better, half did worse)
- `return_p75`: Third quartile (75% did worse, 25% did better)
- `return_p90`: Only 10% of trajectories did better than this

## Analysis Output Interpretation

After running this analysis:

1. Review the summary statistics (mean, percentiles) to understand return distribution
2. Compare `pct_above_target` across curves to identify strategies meeting investment goals
3. Examine `cumulative_risk` to understand total CVaR exposure
4. Analyze top-performing curves' parameters (A, B, t_A) to identify optimal glidepath characteristics

## Configuration for Different Gender Profiles

**Current configuration:** Female retirement age (60 years, 420 months)

**Expected values:**
- `horizon_months`: 420
- `t_B` and `t_end`: 60
- `cumulative_risk`: Lower values (approximately 24-26 range for typical glidepaths)

**To configure for male profiles:**
- Ensure steps 01 and 02 use T_END_YEARS = 65
- `horizon_months` will be 480
- `t_B` and `t_end` will be 65
- `cumulative_risk` will be higher (approximately 28-30 range for typical glidepaths)
- Adjust `TARGET_RETURN_THRESHOLD` based on step 00 results for male profile

## Connection to Step 00 (Target Return Calculator)

The TARGET_RETURN_THRESHOLD should be calibrated using results from step 00:

1. Run step 00 to find the required return for your demographic profile of interest
2. Use that value as TARGET_RETURN_THRESHOLD in this module
3. Interpret `pct_above_target` as: "X% of portfolio trajectories achieve the return needed for adequate retirement in the Chilean pension system"

**Example:** If step 00 shows a female with gaps needs 5.5% annual return for 63% replacement rate, set TARGET_RETURN_THRESHOLD = 0.055.
