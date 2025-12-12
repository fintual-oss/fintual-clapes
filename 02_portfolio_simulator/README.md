# 02_portfolio_simulator - Portfolio Trajectory Generator with Hit-and-Run

## Overview

This module generates feasible portfolio trajectories that comply with CVaR glidepath constraints using the Hit-and-Run algorithm. For each glidepath curve from step 01, it creates multiple portfolio trajectories where each month's portfolio satisfies the CVaR limit for that month.

**Key Feature**: Each month uses a **single randomly selected scenario** (not averaged), ensuring all portfolios in that month face the same market condition for fair comparison.

## What Does This Module Do?

**Input**: CVaR glidepath curves (from step 01) + Historical asset returns  
**Process**: Generate N portfolios per month that satisfy CVaR < CVaR_limit(month)  
**Output**: Portfolio trajectories with monthly CVaR and return values

## Key Features

- **Hit-and-Run Algorithm**: Efficient sampling from CVaR-constrained feasible region
- **Two Simulation Methods**: MVN (faster) or Copula (more realistic)
- **Single Scenario per Month**: All portfolios in month t face the same randomly selected market scenario
- **Multiple Trajectories**: Generate multiple feasible paths per glidepath
- **Comprehensive Output**: Both CVaR values and returns for each trajectory
- **Fully Reproducible**: Seeded random number generation for consistent results

## File Structure

```
02_portfolio_simulator/
├── __init__.py                    # Package metadata
├── main.py                        # Main execution script with configuration
├── routes.py                      # Path management
├── loaders.py                     # Load glidepaths and validate data
├── make_psd.py                    # Ensure covariance matrices are PSD
├── simulate_asset_returns.py      # Asset return simulation (MVN & Copula)
├── cvar_portfolio_sampler.py      # Hit-and-Run algorithm for CVaR portfolios
└── exporters.py                   # Export results to Excel
```

## Configuration Parameters (in main.py)

All parameters can be edited at the top of `main.py`:

### 1. Simulation Method
```python
SIMULATION_METHOD = "copula"  # Options: "mvn" or "copula"
```

**Options:**
- **"mvn"** (Multivariate Normal):
  - ✅ Faster computation
  - ✅ Simple, well-understood
  - ❌ Assumes Gaussian returns (may miss tail behavior)

- **"copula"** (Gaussian Copula):
  - ✅ Preserves empirical marginal distributions
  - ✅ Better captures tail dependencies and asymmetries
  - ✅ More realistic for financial returns
  - ❌ Slower computation

### 2. CVaR Parameters
```python
ALPHA_CVAR = 0.90  # CVaR confidence level
```

**Description**: CVaR confidence level
- `0.90` = worst 10% tail
- `0.95` = worst 5% tail
- Higher α = more conservative (focuses on worse outcomes)

### 3. Portfolio Generation
```python
N_PORTFOLIOS_PER_MONTH = 100  # Number of portfolios per month
N_TRAJ = 1_000                # Monte Carlo scenarios for CVaR estimation
HORIZON_MONTHS = 480          # Total months in simulation
```

**Parameters:**
- **N_PORTFOLIOS_PER_MONTH**: How many different portfolios to generate per month
  - Each becomes a trajectory when connected across months
  - Typical values: 50-200
  
- **N_TRAJ**: Number of Monte Carlo scenarios for simulating asset returns
  - Used for CVaR calculation
  - Higher = more accurate CVaR estimates but slower
  - Minimum recommended: 100
  - Typical values: 1,000-10,000

- **HORIZON_MONTHS**: Total investment horizon in months
  - Must match the glidepaths from step 01
  - Example: 480 months = 40 years (age 25 to 65)

### 4. Random Seeds (for reproducibility)
```python
RETURNS_SEED = 42      # Seed for asset return simulation
HIT_RUN_SEED = 123     # Seed for Hit-and-Run algorithm
SCENARIO_SEED = 999    # Seed for scenario selection per month
```

**Description:**
- **RETURNS_SEED**: Controls the Monte Carlo simulation of asset returns
- **HIT_RUN_SEED**: Controls the Hit-and-Run portfolio generation
- **SCENARIO_SEED**: Controls which scenario is selected for each month
- Same seeds = identical results (reproducibility)
- Change seeds to explore different random realizations

### 5. Curve Selection
```python
PROCESS_ALL_CURVES = True  # Process all curves or selected subset?

CURVES_TO_PROCESS = [      # Only used if PROCESS_ALL_CURVES = False
    "curve_0001",
    "curve_0002",
    "curve_0003",
]
```

**Options:**
- **PROCESS_ALL_CURVES = True**: Process all curves from step 01
- **PROCESS_ALL_CURVES = False**: Only process curves listed in CURVES_TO_PROCESS
  - Useful for testing or analyzing specific glidepaths

## Usage

### Basic Usage

```bash
cd 02_portfolio_simulator
python main.py
```

### Prerequisites

**Required files**:
1. `returns.csv` - Historical monthly returns for assets (at repo root)
2. `outputs/glidepaths_universe.xlsx` - From step 01

### Output

**Location**: `outputs/hit_run_results/`

**Files**: `curve_XXXX_results.xlsx` (one per curve)

**Structure**: Each Excel file has 2 sheets:

#### Sheet 1: "cvar"
Monthly CVaR values for each trajectory
```
       trajectory_001  trajectory_002  trajectory_003  ...
Month                                                   
1            0.0587          0.0592          0.0581   ...
2            0.0588          0.0593          0.0582   ...
...
480          0.0499          0.0498          0.0500   ...
```

#### Sheet 2: "returns"
Monthly returns for each trajectory (single scenario, not averaged)
```
       trajectory_001  trajectory_002  trajectory_003  ...
Month                                                   
1            0.0065          0.0068          0.0063   ...
2            0.0064          0.0067          0.0062   ...
...
480          0.0045          0.0046          0.0044   ...
```

## How It Works

### Overall Process

For each glidepath curve:

1. **Load CVaR limits** for all months (from step 01)
2. **Simulate asset returns** for all months using chosen method (MVN or Copula)
3. **Generate random scenario indices** - one per month (controlled by SCENARIO_SEED)
4. **For each month t**:
   - Get CVaR limit for month t
   - Get scenario index for month t
   - Use Hit-and-Run to generate N portfolios where CVaR < limit
   - Calculate returns using the **single selected scenario** for that month
5. **Trajectory i** = portfolio i connected across all months
6. **Export** CVaR and returns matrices to Excel

### Key Modification: Single Scenario per Month

**Important**: This implementation uses a **single randomly selected scenario** per month instead of averaging over all scenarios.

**How it works**:
```python
# For each month t:
scenario_idx = scenario_indices[t]  # Random index (0 to N_TRAJ-1)
selected_scenario_returns = month_returns[scenario_idx, :]  # One scenario
portfolio_returns = portfolios @ selected_scenario_returns  # Not averaged
```

**Why this approach?**
- ✅ **Fair comparison**: All portfolios in month t face the same market condition
- ✅ **More realistic**: Markets have one actual realization per period
- ✅ **Comparable trajectories**: Can directly compare portfolio performance
- ✅ **Reproducible**: Same SCENARIO_SEED gives same market realizations

**Note**: CVaR is still calculated using **all N_TRAJ scenarios** to ensure portfolios satisfy risk constraints. Only the final returns use a single scenario.

### Hit-and-Run Algorithm

Samples uniformly from the feasible region defined by:
- **Constraint 1**: Σw_i = 1 (weights sum to 1)
- **Constraint 2**: w_i ≥ 0 (no short-selling)
- **Constraint 3**: CVaR(w) < CVaR_limit (risk constraint)

**Steps**:
1. Find initial feasible portfolio
2. Repeat N_PORTFOLIOS_PER_MONTH times:
   - Choose random direction on the simplex
   - Find feasible line segment along this direction
   - Sample uniformly from the segment
   - Move to new portfolio
3. Collect samples after burn-in period

### CVaR Calculation

For a portfolio with weights **w**:

1. Calculate portfolio returns: r_p = **R** · **w** (for all N_TRAJ scenarios)
2. Convert to losses: L = -r_p
3. Find worst α tail (e.g., worst 10% if α=0.90)
4. CVaR = average of losses in the tail

**Example** (α=0.90, N_TRAJ=1000):
- CVaR = average of worst 100 scenarios

### Simulation Methods

#### MVN (Multivariate Normal)

```python
# Estimate from historical data
μ = mean(historical_returns)
Σ = covariance(historical_returns)

# Simulate for each month
R_future ~ N(μ, Σ)
```

**Assumptions**:
- Returns are normally distributed
- Constant mean and covariance
- Linear correlations

#### Copula (Gaussian Copula)

```python
# Step 1: Transform historical returns to uniform [0,1]
U = empirical_cdf(historical_returns)

# Step 2: Transform to Gaussian space
Z = Φ⁻¹(U)

# Step 3: Estimate correlation in Gaussian space
ρ_copula = correlation(Z)

# Step 4: Simulate
Z_future ~ N(0, ρ_copula)
U_future = Φ(Z_future)
R_future = inverse_empirical_cdf(U_future)
```

**Advantages**:
- Preserves exact marginal distributions from historical data
- Captures non-Gaussian features (skewness, kurtosis)
- Better tail dependence modeling

---

**Next Step**: Run `03_trajectory_analyzer` to analyze and rank the generated trajectories