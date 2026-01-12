# fintual-clapes: CVaR Glidepath Analysis System

A comprehensive Python-based system for analyzing optimal retirement investment strategies using CVaR-constrained portfolio glidepaths.

## What Does This System Do?

This system answers two key questions:

1. **"What investment return do I need to achieve adequate retirement income?"**
2. **"What's the optimal way to adjust portfolio risk as I approach retirement?"**

The system combines pension planning analysis with portfolio optimization to provide data-driven retirement strategies.

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        FINTUAL-CLAPES SYSTEM                         │
│                                                                      │
│  Input: Historical asset returns (returns.csv)                       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │  Step 00: Target Return Calculator                         │      │
│  │  - Calculates required returns for pension adequacy        │      │
│  │  - Models Chilean pension system (AFP)                     │      │
│  │  - Output: target_return.xlsx                              │      │
│  │  Purpose: Provides calibration benchmark for Step 03       │      │
│  └────────────────────────────────────────────────────────────┘      │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │  Step 01: Glidepath Generator                              │      │
│  │  - Generates universe of CVaR glidepath curves             │      │
│  │  - Defines risk limits over investor's lifetime            │      │
│  │  - Output: glidepaths_universe.xlsx                        │      │
│  └────────────────────────────────────────────────────────────┘      │
│                            ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │  Step 02: Portfolio Simulator                              │      │
│  │  - Simulates portfolio trajectories for each glidepath     │      │
│  │  - Uses Hit-and-Run algorithm for CVaR constraints         │      │
│  │  - Output: curve_XXXX_results.xlsx (per curve)             │      │
│  └────────────────────────────────────────────────────────────┘      │
│                            ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │  Step 02_test: Portfolio Diversity Analyzer (OPTIONAL)     │      │ 
│  │  - Analyzes portfolio composition and diversification      │      │
│  │  - Examines asset allocation patterns                      │      │
│  │  - Output: curve_XXXX_diversity.xlsx (per curve)           │      │
│  └────────────────────────────────────────────────────────────┘      │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │  Step 03: Trajectory Analyzer                              │      │
│  │  - Analyzes performance of all trajectories                │      │
│  │  - Ranks glidepaths by success rate                        │      │
│  │  - Calculates cumulative risk from CVaR limits             │      │
│  │  - Identifies best strategies                              │      │
│  │  - Output: trajectory_analysis_summary.xlsx                │      │
│  └────────────────────────────────────────────────────────────┘      │
│                                                                      │
│  Final Output: Optimal glidepath recommendations + supporting data   │
└──────────────────────────────────────────────────────────────────────┘
```

## Module Overview

### 00_target_return - Chilean Pension System Required Return Calculator

**Purpose:** Calculate the investment return needed to achieve adequate retirement income in the Chilean pension system.

**What it does:**
- Models the complete AFP pension lifecycle (contributions + returns + pension payout)
- Simulates 4 demographic profiles (male/female, with/without contribution gaps)
- Finds the required annual return to achieve 60% replacement rate
- Provides benchmark values for calibrating Step 03

**When to use:** Before running Step 03, to determine realistic return thresholds based on pension adequacy.

**Key output:** Required returns for different profiles (e.g., "Male without gaps needs 5.8% annual return")

**Connection to other steps:** The required returns from this module are used as TARGET_RETURN_THRESHOLD in Step 03.

---

### 01_glidepath_generator - CVaR Glidepath Universe Generator

**Purpose:** Generate all possible CVaR glidepath strategies to test.

**What it does:**
- Creates thousands of different "risk reduction rules" (glidepaths)
- Each glidepath defines maximum allowed risk (CVaR) at each age
- Starts with higher risk when young, transitions to lower risk at retirement
- Comprehensive grid search over parameters (A, B, t_A)

**When to use:** First step of the main analysis pipeline.

**Key output:** Excel file with all glidepath curves (each column = one strategy)

---

### 02_portfolio_simulator - Portfolio Trajectory Generator with Hit-and-Run

**Purpose:** Generate actual portfolio trajectories that comply with each glidepath's risk constraints.

**What it does:**
- For each glidepath from Step 01, creates many portfolio paths
- Uses Hit-and-Run algorithm to efficiently sample CVaR-constrained portfolios
- Simulates realistic market conditions using historical returns (MVN or Copula method)
- Each month uses single scenario for fair comparison across portfolios
- Saves monthly returns and CVaR values for each trajectory

**When to use:** After Step 01, to generate the portfolio data for analysis.

**Key output:** Excel files per curve with monthly returns and CVaR for each trajectory

**Note:** Portfolio weights (asset allocations) are NOT saved here - see Step 02_test if you need them.

---

### 02_test - Portfolio Diversity Analyzer (OPTIONAL)

**Purpose:** Analyze the diversity and composition of portfolios generated in Step 02.

**What it does:**
- Re-generates portfolios using same seeds as Step 02
- Extracts portfolio weights (not saved in Step 02)
- Calculates diversity metrics: mean weights, standard deviation, HHI, Euclidean distance
- Provides snapshots at key life stages (ages 25, 45, 65)

**When to use:** After Step 02, when you want to understand portfolio composition (not just returns).

**Key output:** Excel files with diversity analysis per curve (8 sheets per file)

---

### 03_trajectory_analyzer - Portfolio Trajectory Performance Analysis

**Purpose:** Analyze which glidepath strategies lead to the best retirement outcomes.

**What it does:**
- Calculates cumulative annualized returns for all trajectories
- Identifies success rate (% of trajectories exceeding target return)
- Calculates cumulative risk (area under CVaR curve from Step 01)
- Ranks all glidepaths by performance
- Combines results with glidepath parameters for interpretation

**When to use:** After Step 02, to identify optimal strategies.

**Key output:** Single Excel file with 1 sheet ranking all curves by success rate and showing cumulative risk

**Connection to Step 00:** Use TARGET_RETURN_THRESHOLD from Step 00 to define "success"

**Connection to Step 01:** Uses CVaR limits from glidepaths to calculate total risk exposure

---

## Repository Structure

```
fintual-clapes/
├── README.md                        # This file
├── returns.csv                      # Historical asset returns (REQUIRED)
│
├── outputs/                         # All output files
│   ├── target_return.xlsx           # From Step 00
│   ├── glidepaths_universe.xlsx     # From Step 01
│   ├── hit_run_results/             # From Step 02
│   │   ├── curve_0001_results.xlsx
│   │   └── ...
│   ├── portfolio_diversity/         # From Step 02_test (optional)
│   │   ├── curve_0001_diversity.xlsx
│   │   └── ...
│   └── trajectory_analysis_summary.xlsx  # From Step 03
│
├── 00_target_return/                # Pension system analysis
│   ├── parameters.py                # ← Edit parameters here
│   ├── main.py
│   ├── formulas.py
│   ├── exporters.py
│   └── README.md
│
├── 01_glidepath_generator/          # Glidepath generation
│   ├── config.py                    # ← Edit parameters here
│   ├── main.py
│   ├── cvar_piecewise.py
│   ├── param_grid.py
│   ├── universe.py
│   ├── utils.py
│   └── README.md
│
├── 02_portfolio_simulator/          # Portfolio simulation
│   ├── main.py                      # ← Edit parameters here
│   ├── simulate_asset_returns.py
│   ├── cvar_portfolio_sampler.py
│   ├── exporters.py
│   ├── loaders.py
│   ├── make_psd.py
│   ├── routes.py
│   └── README.md
│
├── 02_test/                         # Portfolio diversity (OPTIONAL)
│   ├── test_config.py               # ← Edit parameters here
│   ├── main.py
│   ├── test_portfolio_generator.py
│   ├── test_diversity_metrics.py
│   ├── test_exporters.py
│   ├── test_routes.py
│   └── README.md
│
└── 03_trajectory_analyzer/          # Performance analysis
    ├── main.py                      # ← Edit parameters here
    ├── loaders.py
    ├── metrics.py
    ├── exporters.py
    ├── routes.py
    └── README.md
```
---
