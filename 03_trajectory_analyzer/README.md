# 03_trajectory_analyzer - Portfolio Trajectory Performance Analysis

## Overview

This module analyzes the performance of portfolio trajectories generated in step 02. It calculates cumulative annualized returns, success rates (percentage of trajectories exceeding target return), and comprehensive statistics for each CVaR glidepath curve.

The output is a single Excel file with all curves ranked by performance, making it easy to identify the best glidepath strategies.

## What Does This Module Do?

**Input**: Portfolio trajectories (from step 02) + Glidepath parameters (from step 01)  
**Process**: Calculate performance metrics and statistics for each curve  
**Output**: Consolidated Excel report with all curves ranked by performance

## Key Features

- **Cumulative Annualized Returns**: Converts monthly returns to annualized performance
- **Success Rate Analysis**: % of trajectories exceeding target return threshold
- **Comprehensive Statistics**: Mean, std dev, min, max for each curve
- **Percentile Analysis**: Distribution of returns (p10, p25, p50, p75, p90)
- **Parameter Integration**: Combines results with glidepath parameters (A, B, t_A, etc.)
- **Ranked Output**: Sorts curves by performance metrics
- **Clean Excel Export**: Single-sheet, easy-to-analyze format

## File Structure

```
03_trajectory_analyzer/
├── __init__.py          # Package metadata
├── main.py              # Main execution script with configuration
├── routes.py            # Path management
├── loaders.py           # Load data from steps 01 and 02
├── metrics.py           # Calculate returns, statistics, percentiles
└── exporters.py         # Export results to Excel
```

## Configuration Parameters (in main.py)

All parameters can be edited at the top of `main.py`:

### 1. Target Return Threshold
```python
TARGET_RETURN_THRESHOLD = 0.04  # 4% annual return
```

**Description**: Minimum acceptable annualized return
- Trajectories with return > threshold are considered "successful"
- Used to calculate `pct_above_target` metric
- Expressed as decimal (0.04 = 4%)
- Typical values: 0.03-0.06 (3%-6%)

### 2. Percentiles
```python
PERCENTILES = [10, 25, 50, 75, 90]
```

**Description**: Which percentiles to calculate for return distribution
- Helps understand the full distribution, not just the mean
- Values should be integers between 0 and 100

**Common configurations**:
- **Standard**: `[10, 25, 50, 75, 90]` (quintiles + median)
- **Detailed**: `[5, 10, 25, 50, 75, 90, 95]`
- **Simple**: `[25, 50, 75]` (quartiles only)

**Interpretation**:
- `p10`: 10% of trajectories perform worse than this
- `p50`: Median (half perform better, half worse)
- `p90`: Only top 10% of trajectories exceed this

### 3. Curve Selection
```python
PROCESS_ALL_CURVES = True  # Analyze all available curves

CURVES_TO_ANALYZE = [      # Only used if PROCESS_ALL_CURVES = False
    "curve_0001",
    "curve_0002",
    "curve_0003"
]
```

**Options**:
- **PROCESS_ALL_CURVES = True**: Analyze all curves with results from step 02
- **PROCESS_ALL_CURVES = False**: Only analyze curves listed in CURVES_TO_ANALYZE
  - Useful for focusing on specific glidepaths

## Usage

### Basic Usage

```bash
cd 03_trajectory_analyzer
python main.py
```

### Prerequisites

**Required files**:
1. `outputs/glidepaths_universe.xlsx` - From step 01 (glidepath parameters)
2. `outputs/hit_run_results/curve_XXXX_results.xlsx` - From step 02 (trajectory returns)

### Output

**File**: `outputs/trajectory_analysis_summary.xlsx`

**Sheet**: "results"

**Structure**: One row per curve, sorted by performance

**Columns**:

| Column | Description | Example |
|--------|-------------|---------|
| `curve_id` | Curve identifier | curve_0001 |
| `t_start` | Starting age (years) | 25 |
| `t_A` | Transition start age (years) | 45 |
| `A` | Initial CVaR limit (young) | 0.08 |
| `B` | Final CVaR limit (retirement) | 0.05 |
| `t_B` | Transition end age (years) | 65 |
| `t_end` | Retirement age (years) | 65 |
| `n_trajectories` | Number of trajectories analyzed | 100 |
| `horizon_months` | Investment horizon (months) | 480 |
| `return_mean` | Mean annualized return | 0.0523 |
| `return_std` | Standard deviation | 0.0087 |
| `return_min` | Worst trajectory | 0.0312 |
| `return_max` | Best trajectory | 0.0701 |
| `pct_above_target` | % trajectories > target | 0.87 |
| `return_p10` | 10th percentile | 0.0401 |
| `return_p25` | 25th percentile | 0.0456 |
| `return_p50` | 50th percentile (median) | 0.0519 |
| `return_p75` | 75th percentile | 0.0589 |
| `return_p90` | 90th percentile | 0.0643 |

**Sorting**: Rows are sorted by:
1. `pct_above_target` (descending) - curves with more successful trajectories first
2. `return_mean` (descending) - higher average returns first

## How It Works

### Step-by-Step Process

**1. Load Glidepath Parameters**
- Reads `glidepaths_universe.xlsx` from step 01
- Extracts parameters (A, B, t_A, t_B) for each curve

**2. Find Available Curves**
- Scans `hit_run_results/` directory
- Identifies which curves have trajectory results from step 02

**3. Analyze Each Curve**

For each curve with results:

#### a. Load Trajectory Data
```python
# Load returns matrix: (HORIZON_MONTHS × N_PORTFOLIOS)
returns_df = load_trajectory_results(curve_name)
# Example shape: (480, 100) = 480 months × 100 trajectories
```

#### b. Calculate Cumulative Annualized Returns
For each trajectory (column):
```python
# Step 1: Cumulative return (compound monthly returns)
cumulative_return = ∏(1 + r_monthly) - 1

# Step 2: Annualize (convert to yearly rate)
T = number of months
annualized_return = (1 + cumulative_return)^(12/T) - 1
```

**Example**:
- Monthly returns: [0.01, 0.02, -0.005, 0.015, ...]
- After 480 months: cumulative = 1.85 (185% total gain)
- Annualized: (1 + 1.85)^(12/480) - 1 = 0.0523 = 5.23% per year

#### c. Calculate Statistics
```python
return_mean = mean(annualized_returns)        # Average
return_std = std(annualized_returns)          # Volatility
return_min = min(annualized_returns)          # Worst case
return_max = max(annualized_returns)          # Best case
pct_above_target = % returns > TARGET_RETURN  # Success rate
```

#### d. Calculate Percentiles
```python
return_p10 = 10th percentile of annualized_returns
return_p25 = 25th percentile
return_p50 = 50th percentile (median)
return_p75 = 75th percentile
return_p90 = 90th percentile
```

#### e. Combine with Parameters
Merge performance metrics with curve parameters (A, B, t_A, etc.)

**4. Export Results**
- Consolidate all curves into single DataFrame
- Sort by performance (pct_above_target, then return_mean)
- Export to Excel

## Metrics Explained

### 1. Cumulative Annualized Return

**Purpose**: Compare trajectories of different lengths on equal footing

**Formula**:
```
Cumulative = ∏(1 + r_monthly) - 1
Annualized = (1 + cumulative)^(12/T) - 1
```

**Example**:
- Investment period: 40 years (480 months)
- Total gain: 285% (cumulative return = 2.85)
- Annualized: (1 + 2.85)^(12/480) - 1 = 0.0533 = 5.33% per year

### 2. Success Rate (pct_above_target)

**Purpose**: Measure probability of meeting investment goal

**Formula**:
```
pct_above_target = (# trajectories with return > TARGET_RETURN) / (total trajectories)
```

**Interpretation**:
- `0.87` = 87% of trajectories exceeded target return
- Higher is better (more reliable strategy)
- Helps identify robust glidepaths

**Example**:
- Target return: 4%
- 100 trajectories analyzed
- 87 trajectories have annualized return > 4%
- Success rate = 0.87 = 87%

### 3. Return Statistics

**return_mean**: Average performance across all trajectories
- Central tendency of the strategy
- Higher is generally better

**return_std**: Standard deviation of returns
- Measures consistency/volatility
- Lower = more predictable outcomes

**return_min / return_max**: Range of outcomes
- Shows best and worst case scenarios
- Helps assess risk

### 4. Percentiles

**Purpose**: Understand the full distribution, not just the average

**Interpretation**:

| Percentile | Meaning | Use Case |
|------------|---------|----------|
| `p10` | 10% of trajectories are worse | Pessimistic scenario |
| `p25` | Lower quartile | Below-average outcome |
| `p50` | Median (half better, half worse) | Typical outcome |
| `p75` | Upper quartile | Above-average outcome |
| `p90` | Only top 10% exceed this | Optimistic scenario |

**Example**:
- `p10 = 0.0401` → In 90% of cases, return exceeds 4.01%
- `p50 = 0.0519` → Typical outcome is 5.19%
- `p90 = 0.0643` → Best 10% exceed 6.43%

---