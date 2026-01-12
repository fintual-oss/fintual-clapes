# 03_trajectory_analyzer - Portfolio Trajectory Performance Analysis

## Overview

This module analyzes the performance of all portfolio trajectories generated in step 02. It calculates how well each glidepath strategy performed by measuring cumulative returns, success rates, and cumulative risk exposure. The output is a single-sheet Excel report that helps identify which glidepath parameters lead to the best investment outcomes.

The module calculates the cumulative risk of each glidepath by summing the CVaR limits from step 01. This represents the total risk exposure (area under the CVaR curve) inherent to each glidepath strategy.

## What Does This Module Do?

**Input:** 
- Portfolio trajectories from step 02 (monthly returns and CVaR values)
- Glidepath parameters from step 01 (A, B, t_A, t_B)
- CVaR limit curves from step 01 (monthly CVaR limits for each glidepath)

**Process:** 
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
├── main.py           # Main execution script (EDIT PARAMETERS HERE)
├── routes.py         # Path management
├── loaders.py        # Load data from steps 01 and 02
├── metrics.py        # Calculate returns, statistics, percentiles
├── exporters.py      # Export results to Excel (1 sheet)
├── __init__.py       # Package documentation
└── README.md         # This file
```

## Configuration Parameters

All parameters are defined at the top of `main.py`. Edit this file to configure the analysis.

### Target Return Threshold

```python
TARGET_RETURN_THRESHOLD = 0.06  # 6% annual return
```

**What it means:** The minimum acceptable annualized return. This is used to determine if a trajectory is "successful" or not.

**How it's used:**
- Trajectories with annualized return > 6% are considered successful
- Used to calculate success rate (percentage of successful trajectories)

**Recommended value:** Use the required return from step 00 (target_return) for pension-relevant analysis.

**Format:** Decimal (0.06 = 6% annual return)

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
- `t_B`: Transition end age in years (e.g., 65)
- `t_end`: Retirement age in years (e.g., 65)

**Data Summary:**
- `n_trajectories`: Number of trajectories analyzed (e.g., 1000)
- `horizon_months`: Investment horizon in months (e.g., 480)

**Risk Metric:**
- `cumulative_risk`: Total risk exposure (area under CVaR curve from step 01) (e.g., 28.45)

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

**Example:**
```
curve_id  t_A   A      B      cumulative_risk  return_mean  pct_above_target  return_p50
curve_0042  45  0.08  0.03      28.45           0.0523         0.87            0.0519
curve_0015  46  0.09  0.03      30.12           0.0498         0.82            0.0495
curve_0089  44  0.07  0.03      26.78           0.0545         0.91            0.0542
```

**Sorting:** Rows are sorted by:
1. `pct_above_target` (descending) - curves with more successful trajectories first
2. `return_mean` (descending) - higher average returns second

**Interpretation:**
- The first row shows the best performing glidepath based on success rate
- Compare `A` and `t_A` values across top rows to identify optimal parameters
- Look at `pct_above_target` to see reliability of each strategy
- Look at `cumulative_risk` to understand total risk exposure of each glidepath
- Look at percentiles to understand risk/reward distribution

## How It Works

### Step-by-Step Process

**Step 1: Load Glidepath Parameters**
- Read `glidepaths_universe.xlsx` from step 01
- Extract parameters (t_start, t_A, A, B, t_B, t_end) for all curves

**Step 2: Load CVaR Limit Curves**
- Read `glidepaths_universe.xlsx` from step 01
- Extract monthly CVaR limits (Month_1 through Month_480) for all curves
- These are the CVaR constraints that each glidepath imposes

**Step 3: Find Available Curves**
- Scan the `hit_run_results/` directory
- Identify which curves have trajectory results from step 02
- Only curves with results will be analyzed

**Step 4: Analyze Each Curve**

For each curve with results:

**a. Load Trajectory Data**
```
Load two matrices from curve_XXXX_results.xlsx:
- Files are stored as (N_TRAJECTORIES × MONTHS) - rows=trajectories, columns=months
- After loading, data is TRANSPOSED to (MONTHS × N_TRAJECTORIES) for calculations
- returns_df: monthly returns (480 rows × 1000 columns after transpose)
- cvar_df: monthly CVaR (480 rows × 1000 columns after transpose)

After transpose:
- Each column is one trajectory
- Each row is one month
```

**b. Calculate Cumulative Annualized Returns**

For each trajectory (each column of returns_df):

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

   Example: If cumulative return over 480 months is 1.50 (150%), then:
   ```
   annualized = (1 + 1.50)^(12/480) - 1 = (2.50)^0.025 - 1 = 0.0238 = 2.38% per year
   ```

This produces one annualized return value per trajectory.

**c. Calculate Summary Statistics**

Using the annualized returns:
```
return_mean = average of all annualized returns
return_std = standard deviation of annualized returns
return_min = minimum annualized return
return_max = maximum annualized return
pct_above_target = (count of returns > TARGET_RETURN_THRESHOLD) / total count
```

**d. Calculate Percentiles**

Sort the annualized returns and find values at specified percentiles.

Example with 1000 trajectories and percentile 10:
```
Sort returns: [0.02, 0.025, 0.028, ..., 0.065, 0.070]
p10 = value at position 100 (10% of 1000)
```

**e. Calculate Cumulative Risk from Step 01**

For this curve, get the CVaR limits from step 01:
```
cvar_limits = [Month_1, Month_2, ..., Month_480]
cumulative_risk = sum(cvar_limits)
```

Example: If CVaR limits are [0.08, 0.08, 0.08, ..., 0.03], then:
```
cumulative_risk = 0.08 + 0.08 + 0.08 + ... + 0.03 = 28.45
```

**Important:** This is calculated from the glidepath definition (step 01), NOT from the realized CVaR values of trajectories (step 02). It represents the inherent risk profile of the glidepath strategy itself.

**f. Combine with Parameters**

Merge the performance metrics with the glidepath parameters (A, B, t_A, etc.) and cumulative risk for this curve.

**Step 5: Create Summary DataFrame**

Combine results from all curves into a single DataFrame with all columns:
- Glidepath parameters (t_start, t_A, A, B, t_B, t_end)
- Data summary (n_trajectories, horizon_months)
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
- A 40-year return of 150% is different from a 20-year return of 150%
- Annualizing puts everything on "per year" basis

**Formula:**
```
Step 1: Cumulative return = ∏(1 + r_t) - 1
Step 2: Annualized return = (1 + cumulative)^(12/T) - 1
```

**Example:**
- Monthly returns for 480 months compound to cumulative return of 2.50 (250%)
- Annualized: (1 + 2.50)^(12/480) - 1 = (3.50)^0.025 - 1 = 0.0326 = 3.26% per year

### Success Rate (pct_above_target)

**Purpose:** Measure the probability of achieving your investment goal.

**Formula:**
```
pct_above_target = (number of trajectories with return > target) / total trajectories
```

**Interpretation:**
- 0.87 = 87% of trajectories exceeded the target
- Higher is better (more reliable strategy)
- Compare across curves to find most reliable glidepaths

**Example:**
- Target return: 6%
- 1000 trajectories tested
- 870 trajectories achieved > 6%
- Success rate: 870/1000 = 0.87 = 87%

**Connection to Step 00:**
If you use the required return from step 00 as TARGET_RETURN_THRESHOLD, then:
- pct_above_target = probability of achieving adequate retirement income
- A curve with 87% success rate means 87% chance of meeting pension goals

### Cumulative Risk (Area Under CVaR Curve)

**Purpose:** Measure the total risk exposure inherent to each glidepath strategy.

**Formula:**
```
cumulative_risk = Σ CVaR_limit_t  for t = 1 to T
```

This is the sum of all monthly CVaR limits from step 01, also called "area under the CVaR curve."


### Return Percentiles

**Purpose:** Understand the distribution of outcomes beyond just the mean.

**Interpretation:**
- `return_p10`: Only 10% of trajectories did worse than this
- `return_p25`: First quartile (25% did worse)
- `return_p50`: Median return (half did better, half did worse)
- `return_p75`: Third quartile (75% did worse, 25% did better)
- `return_p90`: Only 10% of trajectories did better than this

## Next Steps

After running this analysis:

1. **Identify top performing glidepaths** based on success rate and risk
2. **Examine the parameters** of top curves to find patterns
3. **Use insights to refine** glidepath parameter ranges in step 01 if needed
4. **Consider the trade-offs** between success rate and risk exposure
