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
- Finds the required annual return to achieve 63% replacement rate
- Provides benchmark values for calibrating Step 03

**When to use:** Before running Step 03, to determine realistic return thresholds based on pension adequacy.

**Key output:** Required returns for different profiles (e.g., "Male without gaps needs 5.8% annual return")

**Connection to other steps:** The required returns from this module are used as TARGET_RETURN_THRESHOLD in Step 03.

**Current configuration:** Uses 120 months (last 10 years) for replacement rate calculation.

---

### 01_glidepath_generator - CVaR Glidepath Universe Generator

**Purpose:** Generate all possible CVaR glidepath strategies to test.

**What it does:**
- Creates hundreds of different "risk reduction rules" (glidepaths)
- Each glidepath defines maximum allowed risk (CVaR) at each age
- Starts with higher risk when young, transitions to lower risk at retirement
- Comprehensive grid search over parameters (A, B, t_A)

**When to use:** First step of the main analysis pipeline.

**Key output:** Excel file with all glidepath curves (each column = one strategy)

**Current configuration:** 
- Female retirement age (60 years)
- Horizon: 420 months (35 years, ages 25-60)
- 378 total curves (372 declining + 6 flat glidepaths)

---

### 02_portfolio_simulator - Portfolio Trajectory Generator with Hit-and-Run

**Purpose:** Generate actual portfolio trajectories that comply with each glidepath's risk constraints.

**What it does:**
- For each glidepath from Step 01, creates many portfolio paths
- Uses Hit-and-Run algorithm to efficiently sample CVaR-constrained portfolios
- Simulates realistic market conditions using historical returns (MVN or Copula method)
- Supports two scenario modes:
  - Fixed mode: All portfolios in a month use same scenario (fair comparison)
  - Random mode: Each portfolio uses different scenario (maximum diversity)
- Saves monthly returns for each trajectory

**When to use:** After Step 01, to generate the portfolio data for analysis.

**Key output:** Excel files per curve with monthly returns for each trajectory (transposed format)

**Current configuration:**
- Copula simulation method
- 10,000 portfolios per month
- 10,000 Monte Carlo scenarios
- 420 months horizon
- Fixed scenario mode (USE_RANDOM_SCENARIOS = False)
- 15 parallel processes

**Note:** Portfolio weights (asset allocations) are NOT saved - only returns are stored.

---

### 03_trajectory_analyzer - Portfolio Trajectory Performance Analysis

**Purpose:** Analyze which glidepath strategies lead to the best retirement outcomes.

**What it does:**
- Calculates cumulative annualized returns for all trajectories
- Supports 7 analysis modes (original, sorted, permuted trajectories, and combinations)
- Identifies success rate (% of trajectories exceeding target return)
- Calculates cumulative risk (area under CVaR curve from Step 01)
- Ranks all glidepaths by performance
- Combines results with glidepath parameters for interpretation

**When to use:** After Step 02, to identify optimal strategies.

**Key output:** Single Excel file with 1 sheet ranking all curves by success rate and showing cumulative risk

**Current configuration:**
- Analysis Mode 3: Permuted trajectories only
- TARGET_RETURN_THRESHOLD: 5.5% (female with gaps profile)
- Random seed: 42 (reproducible permutations)
- Percentiles: [10, 25, 50, 75, 90]

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
│   ├── routes.py
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
└── 03_trajectory_analyzer/          # Performance analysis
    ├── main.py                      # ← Edit parameters here
    ├── loaders.py
    ├── metrics.py
    ├── transformations.py
    ├── exporters.py
    ├── routes.py
    └── README.md
```

## Quick Start

### Prerequisites

- Python 3.8+
- Required libraries: pandas, numpy, scipy, xlsxwriter, openpyxl

### Installation

```bash
pip install pandas numpy scipy xlsxwriter openpyxl
```

### Required Input File

Place your historical asset returns in `returns.csv` at the repository root. Format:
- Rows: Time periods (months)
- Columns: Assets
- Values: Monthly returns (decimal format, e.g., 0.02 for 2%)

### Running the System

**Step 0: Calculate Required Returns (Optional but Recommended)**

```bash
python -m 00_target_return.main
```

This generates `outputs/target_return.xlsx` with required returns for pension adequacy.

**Step 1: Generate Glidepaths**

```bash
python -m 01_glidepath_generator.main
```

This generates `outputs/glidepaths_universe.xlsx` with all CVaR glidepath curves.

**Step 2: Simulate Portfolios**

```bash
python -m 02_portfolio_simulator.main
```

This generates `outputs/hit_run_results/curve_XXXX_results.xlsx` files for each glidepath.

**Step 3: Analyze Trajectories**

```bash
python -m 03_trajectory_analyzer.main
```

This generates `outputs/trajectory_analysis_summary.xlsx` with performance analysis and rankings.

### Output Files

After running all steps, you will have:

1. `outputs/target_return.xlsx` - Required returns by demographic profile
2. `outputs/glidepaths_universe.xlsx` - All CVaR glidepath definitions
3. `outputs/hit_run_results/curve_XXXX_results.xlsx` - Monthly returns for each curve
4. `outputs/trajectory_analysis_summary.xlsx` - Final performance rankings

## Configuration

### System-Wide Parameters

The system is currently configured for **female retirement profiles** (60 years retirement age):

- **Horizon:** 420 months (35 years, ages 25-60)
- **Replacement rate target:** 63%
- **Contribution density:** 49.6% (female with gaps)

### To Switch to Male Profile

Update these parameters across modules:

**Step 00 (00_target_return/parameters.py):**
- No changes needed - module calculates both profiles

**Step 01 (01_glidepath_generator/config.py):**
```python
T_END_YEARS = 65
T_B_YEAR = 65
```

**Step 02 (02_portfolio_simulator/main.py):**
```python
HORIZON_MONTHS = 480  # 40 years
```

**Step 03 (03_trajectory_analyzer/main.py):**
```python
TARGET_RETURN_THRESHOLD = 0.058  # Male without gaps (from step 00)
```

### Key Configuration Files

- `00_target_return/parameters.py` - Pension parameters
- `01_glidepath_generator/config.py` - Glidepath parameters
- `02_portfolio_simulator/main.py` - Simulation parameters
- `03_trajectory_analyzer/main.py` - Analysis parameters

## Understanding the Output

### Step 00 Output: target_return.xlsx

**What it tells you:** The annual return needed for each demographic profile to achieve adequate retirement income.

**Key metrics:**
- Required Return (%): Annual return needed
- Achieved Replacement Rate (%): Resulting pension as % of pre-retirement salary
- Final Accumulated Balance (UF): Total savings at retirement
- Monthly Pension (UF): Monthly pension payment

**How to use:** Use the Required Return for your profile of interest as TARGET_RETURN_THRESHOLD in Step 03.

### Step 01 Output: glidepaths_universe.xlsx

**What it tells you:** All possible CVaR glidepath strategies to test.

**Structure:**
- Each column = one glidepath strategy
- First 6 rows = parameters (t_start, t_A, A, B, t_B, t_end)
- Remaining rows = monthly CVaR limits (Month_1 through Month_420)

**How to use:** This file is automatically loaded by Steps 02 and 03.

### Step 02 Output: curve_XXXX_results.xlsx (per curve)

**What it tells you:** Monthly returns for all portfolio trajectories following this glidepath.

**Structure (TRANSPOSED):**
- Rows = trajectories (trajectory_001, trajectory_002, etc.)
- Columns = months (Month_1 through Month_420)
- Values = monthly returns (decimal format)

**How to use:** This file is automatically loaded by Step 03 for analysis.

### Step 03 Output: trajectory_analysis_summary.xlsx

**What it tells you:** Which glidepath strategies perform best.

**Key columns:**
- `pct_above_target`: Success rate (% of trajectories exceeding target return)
- `return_mean`: Average annualized return
- `cumulative_risk`: Total CVaR exposure (area under glidepath curve)
- `A`, `B`, `t_A`: Glidepath parameters

**How to interpret:**
- Rows sorted by success rate (best strategies first)
- Compare `cumulative_risk` to understand total risk taken
- Analyze top rows to identify optimal glidepath characteristics

## Technical Details

### CVaR Glidepath Structure

A CVaR glidepath has three phases:

1. **Constant high risk (ages 25 to t_A):** CVaR limit = A
2. **Linear transition (ages t_A to t_B):** CVaR decreases from A to B
3. **Constant low risk (ages t_B to 60):** CVaR limit = B

Example: A=0.08, B=0.03, t_A=40, t_B=60
- Ages 25-40: Maximum CVaR is 8%
- Ages 40-60: CVaR decreases from 8% to 3%
- Age 60+: Maximum CVaR is 3%

### Hit-and-Run Algorithm

The Hit-and-Run algorithm efficiently generates random portfolios satisfying:
- Weights sum to 1
- No short selling (w ≥ 0)
- CVaR below monthly limit

This eliminates the need for post-generation validation, as portfolios are guaranteed CVaR-compliant.

### Scenario Selection Modes

**Fixed Mode (Default):** All portfolios in a month use the same randomly selected scenario. Ensures fair comparison across strategies.

**Random Mode:** Each portfolio uses a different random scenario. Maximizes exploration of market conditions.

### Analysis Modes (Step 03)

The system supports 7 analysis modes for trajectory transformation:

1. Original trajectories only
2. Sorted trajectories only (best case per month)
3. Permuted trajectories only (random reassignment)
4. Permuted + Sorted
5. Original + Sorted
6. Original + Permuted
7. Original + Sorted + Permuted

**Current default:** Mode 3 (Permuted trajectories)

## License

This project is developed by the Fintual-Clapes research team.

## Contact

For questions or issues, please contact the Fintual-Clapes team.
