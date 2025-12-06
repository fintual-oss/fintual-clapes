# fintual-clapes: CVaR Glidepath Analysis System

A comprehensive Python-based system for generating, simulating, and analyzing CVaR-constrained portfolio glidepaths for retirement planning. This repository implements a three-stage pipeline that generates thousands of feasible portfolio trajectories and identifies optimal risk management strategies.

## What Does This System Do?

This system helps answer the question: **"What's the optimal way to adjust portfolio risk as someone approaches retirement?"**

It does this by:
1. **Generating** thousands of different risk reduction paths (glidepaths)
2. **Simulating** portfolio trajectories that comply with each path's risk constraints
3. **Analyzing** which paths lead to the best outcomes

## System Overview

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

## Run the Pipeline

```bash
# Step 1: Generate CVaR glidepath universe
python -m 01_glidepath_generator.main

# Step 2: Simulate portfolio trajectories
python -m 02_portfolio_simulator.main

# Step 3: Analyze and rank trajectories
python -m 03_trajectory_analyzer.main
```

Each step produces output files in the `outputs/` directory.

## Configuration Guide

### Step 01: Glidepath Generator

**Edit**: `01_glidepath_generator/config.py`

**Key Parameters**:
```python
# Age range
T_START_YEARS = 25          # Starting age
T_END_YEARS   = 65          # Retirement age

# Transition ages
T_A_YEARS_VALUES = list(range(40, 51))  # When transition starts

# CVaR limits
A_MIN, A_MAX, A_STEP = 0.06, 0.10, 0.01  # Young age (6%-10%)
B_MIN, B_MAX, B_STEP = 0.05, 0.05, 0.01  # Retirement (5%)
```

### Step 02: Portfolio Simulator

**Edit**: `02_portfolio_simulator/main.py`

**Key Parameters**:
```python
# Simulation method
SIMULATION_METHOD = "copula"  # "copula" (recommended) or "mvn"

# CVaR confidence level
ALPHA_CVAR = 0.90  # 90% = worst 10% tail

# Portfolio generation
N_PORTFOLIOS_PER_MONTH = 100  # Trajectories per curve
N_TRAJ = 1_000                # Monte Carlo scenarios
HORIZON_MONTHS = 480          # Must match step 01

# Random seeds
RETURNS_SEED = 42
HIT_RUN_SEED = 123
SCENARIO_SEED = 999

# Curve selection
PROCESS_ALL_CURVES = True  # Process all or subset
```

**Important**: `HORIZON_MONTHS` must match the months in step 01:
```python
HORIZON_MONTHS = (T_END_YEARS - T_START_YEARS) * 12
```

### Step 03: Trajectory Analyzer

**Edit**: `03_trajectory_analyzer/main.py`

**Key Parameters**:
```python
# Target return threshold
TARGET_RETURN_THRESHOLD = 0.04  # 4% annual return

# Percentiles to calculate
PERCENTILES = [10, 25, 50, 75, 90]

# Curve selection
PROCESS_ALL_CURVES = True
```


## Output Files

### 01_glidepath_generator

**File**: `outputs/glidepaths_universe.xlsx`

**Contains**: All CVaR glidepath curves
- Rows: Parameters + Monthly CVaR limits
- Columns: curve_0001, curve_0002, etc.

### 02_portfolio_simulator

**Directory**: `outputs/hit_run_results/`

**Files**: `curve_XXXX_results.xlsx` (one per curve)

**Each file has 2 sheets**:
- **cvar**: Monthly CVaR values for each trajectory
- **returns**: Monthly returns for each trajectory (single scenario per month)

### 03_trajectory_analyzer

**File**: `outputs/trajectory_analysis_summary.xlsx`

**Contains**: Performance analysis and ranking
- One row per curve
- Sorted by success rate and mean return
- Columns: parameters, performance metrics, percentiles

## Key Features

### Step 01: Glidepath Generator
- ✅ Comprehensive grid search over parameter space
- ✅ Automatic validation (A ≥ B, t_A < t_B)
- ✅ Piecewise linear CVaR paths

### Step 02: Portfolio Simulator
- ✅ **Hit-and-Run algorithm** for CVaR-constrained portfolios
- ✅ **Single scenario per month** (not averaged) for fair comparison
- ✅ **Two simulation methods**: MVN (fast) or Copula (realistic)
- ✅ Fully reproducible with random seeds

### Step 03: Trajectory Analyzer
- ✅ Cumulative annualized returns
- ✅ Success rate analysis (% above target)
- ✅ Complete distribution via percentiles
- ✅ Automated ranking of strategies

## Important Notes

### Horizon Consistency

If you change the horizon in step 01:
```python
# 01_glidepath_generator/config.py
T_START_YEARS = 30  # Changed from 25
T_END_YEARS   = 65
# This creates 420 months (35 years)
```

You **must** update step 02:
```python
# 02_portfolio_simulator/main.py
HORIZON_MONTHS = 420  # Must match!
```

### Random Seeds

All three seeds in step 02 control different randomness:
- `RETURNS_SEED`: Asset return simulation
- `HIT_RUN_SEED`: Portfolio generation
- `SCENARIO_SEED`: **Which scenario is used each month**

Same seeds = identical results (reproducibility)

### Simulation Method

**Copula (Recommended)**:
- Preserves empirical distributions from historical data
- Better tail behavior
- More realistic for financial returns
- Slower

**MVN (Alternative)**:
- Assumes Gaussian returns
- Faster computation
- Good for testing

## 📖 Detailed Documentation

Each module has comprehensive documentation:

- [**01_glidepath_generator/README.md**](01_glidepath_generator/README.md): Full parameter guide, examples, formulas
- [**02_portfolio_simulator/README.md**](02_portfolio_simulator/README.md): Algorithm details, simulation methods, configuration
- [**03_trajectory_analyzer/README.md**](03_trajectory_analyzer/README.md): Metrics explanation, interpretation guide

## Repository Structure

```
fintual-clapes/
├── returns.csv                      # Historical asset returns (required)
├── outputs/                         # All output files
│   ├── glidepaths_universe.xlsx
│   ├── hit_run_results/
│   │   ├── curve_0001_results.xlsx
│   │   └── ...
│   └── trajectory_analysis_summary.xlsx
├── 01_glidepath_generator/
│   ├── config.py                    # ← Edit parameters here
│   ├── main.py
│   └── ...
├── 02_portfolio_simulator/
│   ├── main.py                      # ← Edit parameters here
│   └── ...
└── 03_trajectory_analyzer/
    ├── main.py                      # ← Edit parameters here
    └── ...
```

---
