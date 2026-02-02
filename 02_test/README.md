# 02_test - Portfolio Diversity Analyzer

## Overview

This module analyzes how diverse the portfolios generated in step 02 are by examining their asset allocations (weights). It re-generates the same portfolios from step 02 using identical random seeds, but this time captures and analyzes the portfolio weights instead of just returns and CVaR values.

The purpose is to understand portfolio composition: Are portfolios well-diversified across assets? Do they concentrate in a few assets? How does diversification change over time as investors age and approach retirement?

## Why This Module Exists

In step 02, we generate portfolios and save their returns and CVaR values. However, we do NOT save the portfolio weights (how much money is allocated to each of the 9 assets). This module:

1. Re-runs the portfolio generation with the SAME random seeds
2. Captures the weights this time (not just returns/CVaR)
3. Calculates diversity metrics to understand portfolio composition
4. Exports the analysis to Excel for review

This is a diagnostic/analysis tool. You can run it to understand your portfolios better, or skip it if you only care about final returns.

## What Does This Module Do?

**Input:** 
- CVaR glidepath curves from step 01
- Historical asset returns
- Random seeds (MUST match step 02)

**Process:** 
1. Re-generate portfolios using exact same seeds as step 02
2. Extract portfolio weights (asset allocations)
3. Calculate diversity metrics for each month
4. Analyze concentration and diversification patterns

**Output:** 
- Excel files (one per curve) with detailed diversity analysis

## File Structure

```
02_test/
├── test_config.py                  # Configuration parameters (EDIT THIS FILE)
├── main.py                         # Main execution script
├── test_routes.py                  # Path management
├── test_portfolio_generator.py     # Re-generates portfolios with same logic as step 02
├── test_diversity_metrics.py       # Calculates diversity metrics
├── test_exporters.py              # Exports results to Excel
├── __init__.py                     # Package documentation
└── README.md                       # This file
```

## Configuration Parameters

All parameters are defined in `test_config.py`. Edit this file to configure the analysis.

### Curve Selection

```python
PROCESS_ALL_CURVES = False
CURVES_TO_ANALYZE = [
    "curve_0001",
    "curve_0002"
]
```

**What it means:**
- `PROCESS_ALL_CURVES = True`: Analyze all curves from step 01
- `PROCESS_ALL_CURVES = False`: Only analyze curves in CURVES_TO_ANALYZE list

### Number of Portfolios

```python
N_PORTFOLIOS_TO_ANALYZE = 1000
```

**What it means:** How many portfolios to analyze per month.

**Important:** This does NOT need to match step 02. You can analyze fewer portfolios for speed.

### Random Seeds (CRITICAL)

```python
RETURNS_SEED = 111      # Must match 02_portfolio_simulator
HIT_RUN_SEED = 222      # Must match 02_portfolio_simulator
SCENARIO_SEED = 333     # Must match 02_portfolio_simulator
```

**CRITICAL:** These seeds MUST be identical to those in `02_portfolio_simulator/main.py`.

**Why this matters:**
- Same seeds = analyzing the EXACT portfolios used in step 02
- Different seeds = analyzing different portfolios (not useful)

**How to set these values:** 
1. Open `02_portfolio_simulator/main.py`
2. Find the values for RETURNS_SEED, HIT_RUN_SEED, and SCENARIO_SEED
3. Copy those exact values to `test_config.py` in this module

### Simulation Parameters (Must Match Step 02)

```python
SIMULATION_METHOD = "copula"  # "mvn" or "copula"
ALPHA_CVAR = 0.90            # CVaR confidence level
N_TRAJ = 10000               # Monte Carlo scenarios
HORIZON_MONTHS = 480         # Investment horizon
```

**What they mean:**
- `SIMULATION_METHOD`: How to simulate future returns (must match step 02)
- `ALPHA_CVAR`: CVaR tail threshold (must match step 02)
- `N_TRAJ`: Number of scenarios for CVaR calculation (must match step 02)
- `HORIZON_MONTHS`: Total months (must match step 02)

**Important:** All these parameters MUST match step 02 exactly.

### Output Directory

```python
OUTPUT_SUBDIR = "portfolio_diversity"
```

**What it means:** Results will be saved in `outputs/portfolio_diversity/`

## How to Run

```bash
python -m 02_test.main
```

Or, if you are inside the `02_test/` directory:

```bash
python main.py
```

### Prerequisites

**Required files:**
1. `returns.csv` at repository root
2. `outputs/glidepaths_universe.xlsx` from step 01

**Important:** You do NOT need to have run step 02 first. This module re-generates the portfolios independently.

## Output Files

**Location:** `outputs/portfolio_diversity/`

**Files:** One Excel file per curve: `curve_XXXX_diversity.xlsx`

**Example:**
```
outputs/portfolio_diversity/
├── curve_0001_diversity.xlsx
├── curve_0002_diversity.xlsx
└── curve_0003_diversity.xlsx
```

### Excel File Structure

Each Excel file contains 8 sheets:

#### Sheet 1: "summary"

Basic information about the analysis.

```
Parameter                Value
Curve Name              curve_0001
Number of Portfolios    1000
Number of Months        480
Number of Assets        9
Equal-Weight Reference  1/9 = 0.111111
```

**Use case:** Quick overview of what was analyzed.

#### Sheet 2: "weights_mean"

Average portfolio weights for each asset, month by month.

**Format:**
- **Rows:** Months (1, 2, 3, ..., 480)
- **Columns:** Assets (e.g., LKXIP, RACLCORP, IPSA, ...)
- **Values:** Mean weight across all 1000 portfolios

**Example:**
```
       LKXIP  RACLCORP  IPSA  PEBUY  LEGATRUU  LF98TRUU  NDDUWI  NDUEEGF  NDX
Month                                                                         
1      0.12    0.11    0.10   0.11    0.13      0.12     0.10     0.11    0.10
2      0.12    0.11    0.10   0.11    0.13      0.12     0.10     0.11    0.10
...
240    0.08    0.09    0.08   0.10    0.15      0.16     0.12     0.12    0.10
...
480    0.05    0.07    0.05   0.08    0.18      0.20     0.13     0.14    0.10
```

**Interpretation:**
- At month 1 (age 25), on average portfolios allocate 12% to LKXIP, 11% to RACLCORP, etc.
- At month 480 (age 65, retirement), allocations have shifted (e.g., more to LEGATRUU and LF98TRUU)

#### Sheet 3: "weights_std"

Standard deviation of weights across portfolios.

**Format:**
- **Rows:** Months
- **Columns:** Assets
- **Values:** Standard deviation of weight across 1000 portfolios

**Example:**
```
       LKXIP  RACLCORP  IPSA  ...
Month                           
1      0.02    0.03    0.02  ...
2      0.02    0.03    0.02  ...
```


#### Sheet 4: "hhi"

Herfindahl-Hirschman Index (HHI) for each portfolio at each month.

**Format:**
- **Rows:** Portfolios (portfolio_0001, portfolio_0002, ..., portfolio_1000)
- **Columns:** Months (Month_1, Month_2, ..., Month_480)
- **Values:** HHI value (sum of squared weights)

**Example:**
```
             Month_1  Month_2  ...  Month_480
Portfolio                                    
portfolio_0001  0.15    0.15   ...     0.18
portfolio_0002  0.14    0.14   ...     0.19
...
portfolio_1000  0.16    0.16   ...     0.17
```

**What HHI means:**

HHI = Σ(w_i²) where w_i is the weight of asset i

**Interpretation:**
- **Minimum HHI = 1/N = 1/9 ≈ 0.111** (equal-weight portfolio: each asset gets 11.1%)
- **Maximum HHI = 1.0** (all money in one asset: 100% in one asset, 0% in others)
- **Lower HHI = more diversified** (money spread across many assets)
- **Higher HHI = more concentrated** (money concentrated in fewer assets)


**Use case:** Identify which portfolios are well-diversified vs concentrated at different life stages.

#### Sheet 5: "euclidean_distance"

Euclidean distance from equal-weight portfolio for each portfolio at each month.

**Format:**
- **Rows:** Portfolios (portfolio_0001, portfolio_0002, ..., portfolio_1000)
- **Columns:** Months (Month_1, Month_2, ..., Month_480)
- **Values:** Distance from equal-weight (1/9, 1/9, ..., 1/9)

**Example:**
```
             Month_1  Month_2  ...  Month_480
Portfolio                                    
portfolio_0001  0.08    0.08   ...     0.12
portfolio_0002  0.10    0.10   ...     0.15
...
portfolio_1000  0.07    0.07   ...     0.11
```

**What distance means:**

Distance = √[Σ(w_i - 1/N)²] where w_i is the weight of asset i, N = number of assets

#### Sheets 6-8: Weight Snapshots

These sheets show the complete portfolio composition at specific points in time.

**Sheet 6: "weights_month_001"** - Beginning of investment (age 25, month 1)
**Sheet 7: "weights_month_240"** - Middle of investment (age 45, month 240)
**Sheet 8: "weights_month_XXX"** - Retirement (age 65, last month)

**Format for all snapshot sheets:**
- **Rows:** Portfolios (portfolio_0001, portfolio_0002, ..., portfolio_1000)
- **Columns:** Assets (LKXIP, RACLCORP, IPSA, PEBUY, LEGATRUU, LF98TRUU, NDDUWI, NDUEEGF, NDX)
- **Values:** Weight allocated to each asset (decimal form, e.g., 0.15 = 15%)

**Example (weights_month_001):**
```
             LKXIP  RACLCORP  IPSA  PEBUY  LEGATRUU  LF98TRUU  NDDUWI  NDUEEGF  NDX
Portfolio                                                                           
portfolio_0001  0.12    0.11    0.10   0.11    0.13      0.12     0.10     0.11    0.10
portfolio_0002  0.11    0.12    0.09   0.12    0.12      0.13     0.11     0.10    0.10
portfolio_0003  0.13    0.10    0.11   0.10    0.14      0.11     0.09     0.12    0.10
...
portfolio_1000  0.12    0.11    0.10   0.11    0.13      0.12     0.10     0.11    0.10
```

**Interpretation:**
- Each row is one complete portfolio showing all asset allocations
- Weights in each row should sum to approximately 1.0 (100%)
- Compare across months to see how portfolio composition changes over life cycle

## How It Works

### Overall Process

For each curve:

**Step 1: Load Data**
- Load CVaR limits from step 01
- Load historical returns

**Step 2: Re-generate Portfolios**
- Use EXACT same code as step 02
- Use EXACT same seeds as step 02
- This ensures we're analyzing the ACTUAL portfolios from step 02
- But now capture weights (not saved in step 02)

**Step 3: Calculate Metrics**

For each month t (1 to 480):
- Extract weights for all 1000 portfolios at month t
- Calculate mean and std across portfolios for each asset
- Calculate HHI and Euclidean distance for each portfolio

**Step 4: Extract Snapshots**
- Save complete weight matrices for months 1, 240, and last month

**Step 5: Export to Excel**
- Create Excel file with 8 sheets
- Format for easy analysis

### Why Re-generate Instead of Saving Weights in Step 02?

**Advantages:**
1. **Modularity**: Step 02 stays focused on its core task (returns/CVaR)
2. **Storage**: Weights are large (480 × 1000 × 9 = 4.3M values per curve)
3. **Flexibility**: Can analyze subset of portfolios without re-running all of step 02
4. **Optional**: Easy to skip this analysis if not needed

**Disadvantage:**
- Takes time to re-run (but reproducible with seeds)

## Important Notes

### Seeds Must Match Step 02

**CRITICAL:** If seeds don't match, you're analyzing different portfolios.

**How to verify:**
```python
# In test_config.py
RETURNS_SEED = 42
HIT_RUN_SEED = 123
SCENARIO_SEED = 999

# In 02_portfolio_simulator/main.py
RETURNS_SEED = 42  # Must match!
HIT_RUN_SEED = 123  # Must match!
SCENARIO_SEED = 999  # Must match!
```

### This Module is Optional

You can skip this entirely if you only care about portfolio returns (from step 03). This is purely for understanding portfolio composition.

### Number of Portfolios Can Differ

N_PORTFOLIOS_TO_ANALYZE does NOT need to match N_PORTFOLIOS_PER_MONTH from step 02.

**Example:**
- Step 02: Generate 1000 portfolios per month
- This module: Analyze first 100 portfolios (faster)

This works because the first 100 portfolios generated with the same seeds are identical.

### Output Files Can Be Large

With 1000 portfolios and 480 months:
- weights_mean, weights_std: Small (480 rows × 9 columns)
- HHI, euclidean_distance: Large (1000 rows × 480 columns)
- Weight snapshots: Medium (1000 rows × 9 columns × 3 snapshots)

Total file size per curve: ~5-10 MB


## Next Steps

After analyzing diversity:

1. **Validate portfolios look reasonable**: Check weights_mean for sensible allocations
2. **Compare across curves**: Which glidepath parameters lead to better diversification?
3. **Use insights in step 01**: Adjust glidepath parameters if portfolios are too concentrated

This module provides portfolio-level insights that complement the return-level analysis in step 03.
