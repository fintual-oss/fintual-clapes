# 03_trajectory_analyzer - Portfolio Trajectory Performance Analysis

## Overview

This module analyzes the performance of portfolio trajectories generated in step 02. It calculates cumulative annualized returns, success rates (percentage of trajectories exceeding target return), and comprehensive statistics for each CVaR glidepath curve.

## What Does This Module Do?

**Input**: Portfolio trajectories (from step 02) + Glidepath parameters (from step 01)  
**Process**: Calculate performance metrics and statistics  
**Output**: Consolidated Excel report with all curves ranked by performance

## Key Features

- **Cumulative Annualized Returns**: Converts monthly returns to annualized performance
- **Success Rate Analysis**: % of trajectories exceeding target return threshold
- **Comprehensive Statistics**: Mean, std dev, min, max, percentiles
- **Parameter Integration**: Combines results with glidepath parameters
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

## Configuration (in main.py)

### Target Return Threshold
```python
TARGET_RETURN_THRESHOLD = 0.04  # 4% annual return
```
Trajectories with annualized return > 4% are considered "successful"

### Percentiles
```python
PERCENTILES = [10, 25, 50, 75, 90]
```
Calculate these percentiles of the return distribution

### Curve Selection
```python
PROCESS_ALL_CURVES = True  # Analyze all available curves

# If False, only analyze these:
CURVES_TO_ANALYZE = [
    "curve_0001",
    "curve_0002"
]
```

## Usage

### Prerequisites

**Required files**:
1. `outputs/glidepaths_universe.xlsx` - From step 01
2. `outputs/hit_run_results/curve_XXXX_results.xlsx` - From step 02

### Output

**File**: `outputs/trajectory_analysis_summary.xlsx`

**Sheet**: "results"

**Columns**:
- **Curve identification**: `curve_id`
- **Glidepath parameters**: `t_start`, `t_A`, `A`, `B`, `t_B`, `t_end`
- **Simulation info**: `n_trajectories`, `horizon_months`
- **Return statistics**: 
  - `return_mean`: Average annualized return
  - `return_std`: Standard deviation
  - `return_min`: Worst performing trajectory
  - `return_max`: Best performing trajectory
  - `pct_above_target`: % trajectories > target return
- **Return percentiles**: `return_p10`, `return_p25`, `return_p50`, `return_p75`, `return_p90`

**Rows**: One row per curve, sorted by `pct_above_target` (descending), then `return_mean` (descending)

## Algorithm Details

### Step 1: Load Glidepath Parameters

Load curve parameters (A, B, t_A, etc.) from step 01 output

### Step 2: Find Available Curves

Scan `hit_run_results/` directory for curves with simulation results

### Step 3: Analyze Each Curve

For each curve:

#### 3a. Load Trajectory Data
- Load returns matrix (360 months × N trajectories)
- Load CVaR matrix (for reference, not used in current analysis)

#### 3b. Calculate Cumulative Returns
For each trajectory:
```python
# Monthly compounding
cumulative_return = ∏(1 + r_monthly) - 1

# Annualize
annualized_return = (1 + cumulative_return)^(12/T) - 1
```

#### 3c. Calculate Statistics
- Mean, std dev, min, max
- Percentiles (p10, p25, p50, p75, p90)
- % above target return

#### 3d. Combine with Parameters
Merge performance metrics with curve parameters (A, B, t_A, etc.)

### Step 4: Export Results

Create consolidated Excel file with all curves ranked by performance

## Metrics Explained

### Cumulative Annualized Return

**Purpose**: Compare trajectories of different lengths on equal footing

**Formula**:
```
Step 1: Cumulative = ∏(1 + r_monthly) - 1
Step 2: Annualized = (1 + cumulative)^(12/T) - 1
```

**Example**:
- Month 1 return: +2%
- Month 2 return: +3%
- Month 3 return: -1%

Cumulative = (1.02 × 1.03 × 0.99) - 1 = 0.0406 = 4.06%  
Annualized (3 months) = (1.0406)^(12/3) - 1 = 0.167 = 16.7%

### Success Rate (pct_above_target)

**Purpose**: Measure probability of meeting investment goal

**Formula**:
```
pct_above_target = (# trajectories with return > target) / (total trajectories)
```

**Example**:
- 10 trajectories
- 8 have return > 4%
- Success rate = 8/10 = 0.80 = 80%

### Percentiles

**Purpose**: Understand full distribution, not just average

**Interpretation**:
- `return_p10`: 10% of trajectories perform worse than this
- `return_p25`: 25% perform worse (lower quartile)
- `return_p50`: 50% perform worse (median)
- `return_p75`: 75% perform worse (upper quartile)
- `return_p90`: 90% perform worse (only best 10% exceed this)
