# fintual-clapes: CVaR Glidepath Analysis System

A comprehensive Python-based system for generating, simulating, and analyzing CVaR-constrained portfolio glidepaths for retirement planning. This repository implements a three-stage pipeline that generates thousands of feasible portfolio trajectories and identifies optimal risk management strategies.

## 🎯 What Does This System Do?

This system helps answer the question: **"What's the optimal way to adjust portfolio risk as someone approaches retirement?"**

It does this by:
1. **Generating** thousands of different risk reduction paths (glidepaths)
2. **Simulating** portfolio trajectories that comply with each path's risk constraints
3. **Analyzing** which paths lead to the best outcomes

## Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     FINTUAL-CLAPES SYSTEM                        │
│                                                                  │
│  Input: Historical asset returns (returns.csv)                   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐      │
│  │  Step 01: Glidepath Generator                          │      │
│  │  - Generates universe of CVaR glidepath curves         │      │
│  │  - Output: glidepaths_universe.xlsx                    │      │
│  └────────────────────────────────────────────────────────┘      │
│                            ↓                                     │
│  ┌────────────────────────────────────────────────────────┐      │
│  │  Step 02: Portfolio Simulator                          │      │
│  │  - Simulates feasible portfolio trajectories           │      │
│  │  - Uses Hit-and-Run algorithm                          │      │
│  │  - Output: curve_XXXX_results.xlsx (per curve)         │      │
│  └────────────────────────────────────────────────────────┘      │
│                            ↓                                     │
│  ┌────────────────────────────────────────────────────────┐      │
│  │  Step 03: Trajectory Analyzer                          │      │
│  │  - Analyzes performance of all trajectories            │      │
│  │  - Ranks glidepaths by success rate                    │      │
│  │  - Output: trajectory_analysis_summary.xlsx            │      │
│  └────────────────────────────────────────────────────────┘      │
│                                                                  │
│  Final Output: Optimal glidepath recommendations                 │
└──────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Basic Usage

```bash
# Step 1: Generate CVaR glidepath universe
python -m 01_glidepath_generator.main

# Step 2: Simulate portfolio trajectories
python -m 02_portfolio_simulator.main

# Step 3: Analyze and rank trajectories
python -m 03_trajectory_analyzer.main
```

## 📖 Detailed Module Documentation

Each module has its own comprehensive README:

- [**01_glidepath_generator**](01_glidepath_generator/README.md): Generate CVaR glidepath universe
- [**02_portfolio_simulator**](02_portfolio_simulator/README.md): Simulate portfolio trajectories with Hit-and-Run
- [**03_trajectory_analyzer**](03_trajectory_analyzer/README.md): Analyze and rank trajectories

## Configuration

### Global Parameters

**Horizon** (in `01_glidepath_generator/config.py`):
```python
T_START_YEARS = 35    # Starting age
T_END_YEARS   = 65    # Retirement age
# Results in 360 months (30 years)
```

**Important**: If you change the horizon, also update `HORIZON_MONTHS` in `02_portfolio_simulator/main.py`

**CVaR Ranges** (in `01_glidepath_generator/config.py`):
```python
A_MIN, A_MAX, A_STEP = 0.06, 0.10, 0.01  # Young age CVaR limits
B_MIN, B_MAX, B_STEP = 0.05, 0.05, 0.01  # Retirement CVaR limit
T_A_YEARS_VALUES = list(range(40, 51))    # Transition start ages
```

### Simulation Method

**In `02_portfolio_simulator/main.py`**:
```python
SIMULATION_METHOD = "copula"  # or "mvn"
```

- **"copula"**: Preserves empirical distributions (recommended, slower)
- **"mvn"**: Assumes Gaussian returns (faster, less realistic)

### Target Return

**In `03_trajectory_analyzer/main.py`**:
```python
TARGET_RETURN_THRESHOLD = 0.04  # 4% annual return
```

Trajectories above this are considered "successful"


## Output Files

### 1. glidepaths_universe.xlsx

**Location**: `outputs/glidepaths_universe.xlsx`

**Contains**: All CVaR glidepath curves with parameters

**Format**:
- Rows: Parameters (t_start, t_A, A, B, t_B, t_end) + Monthly values (Month_1...Month_360)
- Columns: curve_0001, curve_0002, ..., curve_XXXX

### 2. curve_XXXX_results.xlsx

**Location**: `outputs/hit_run_results/curve_XXXX_results.xlsx`

**Contains**: Simulation results for one curve

**Sheets**:
- **cvar**: Monthly CVaR values (360 months × N trajectories)
- **returns**: Monthly expected returns (360 months × N trajectories)

### 3. trajectory_analysis_summary.xlsx

**Location**: `outputs/trajectory_analysis_summary.xlsx`

**Contains**: Performance analysis of all curves

**Columns**:
- Curve parameters (t_A, A, B, etc.)
- Performance metrics (return_mean, return_std, etc.)
- Success rate (pct_above_target)
- Percentiles (return_p10, return_p25, return_p50, return_p75, return_p90)

**Sorted by**: Success rate (descending), then mean return (descending)

---

For detailed module documentation, see individual README files in each subdirectory.


