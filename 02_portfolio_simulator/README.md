# 02_portfolio_simulator - Portfolio Trajectory Generator with Hit-and-Run

## Overview

This module generates feasible portfolio trajectories that comply with CVaR glidepath constraints using the Hit-and-Run algorithm. For each glidepath curve from step 01, it creates multiple portfolio trajectories where each month's portfolio satisfies the CVaR limit for that month.

## What Does This Module Do?

**Input**: CVaR glidepath curves (from step 01) + Historical asset returns  
**Process**: Generate N portfolios per month that satisfy CVaR < CVaR_limit(month)  
**Output**: Portfolio trajectories with monthly CVaR and return values

## Key Features

- **Hit-and-Run Algorithm**: Efficient sampling from CVaR-constrained feasible region
- **Two Simulation Methods**: 
  - MVN (Multivariate Normal) - faster, assumes Gaussian returns
  - Copula (Gaussian Copula) - preserves empirical distributions, better tail behavior
- **Multiple Trajectories**: Generate multiple feasible paths per glidepath
- **Comprehensive Output**: Both CVaR values and expected returns for each trajectory
- **Reproducible**: Seeded random number generation for consistent results

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

## Configuration (in main.py)

### Simulation Method
```python
SIMULATION_METHOD = "copula"  # "mvn" or "copula"
```

**MVN (Multivariate Normal)**:
- ✅ Faster computation
- ✅ Simple, well-understood
- ❌ Assumes Gaussian returns (may miss tail behavior)

**Copula (Gaussian Copula)**:
- ✅ Preserves empirical marginal distributions
- ✅ Better captures tail dependencies and asymmetries
- ✅ More realistic for financial returns
- ❌ Slower computation

### CVaR Parameters
```python
ALPHA_CVAR = 0.90  # CVaR confidence level (90% = worst 10% tail)
```

### Portfolio Generation
```python
N_PORTFOLIOS_PER_MONTH = 10   # Number of trajectories per glidepath
N_TRAJ = 1_000                # Monte Carlo scenarios for CVaR estimation
HORIZON_MONTHS = 360          # Total months (30 years)
```

### Random Seeds
```python
RETURNS_SEED = 42      # Seed for asset return simulation
HIT_RUN_SEED = 123     # Seed for Hit-and-Run algorithm
```

### Curve Selection
```python
PROCESS_ALL_CURVES = False    # Process all curves or selected subset?

CURVES_TO_PROCESS = [         # If PROCESS_ALL_CURVES=False, process these:
    "curve_0001",
    "curve_0002"
]
```

## Usage

### Basic Usage

```bash
cd fintual-clapes
python -m 02_portfolio_simulator.main
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
360          0.0499          0.0498          0.0500   ...
```

#### Sheet 2: "returns"
Monthly expected returns for each trajectory
```
       trajectory_001  trajectory_002  trajectory_003  ...
Month                                                   
1            0.0065          0.0068          0.0063   ...
2            0.0064          0.0067          0.0062   ...
...
360          0.0045          0.0046          0.0044   ...
```

## Algorithm Details

### Overall Process

For each glidepath curve:
1. Load CVaR limits for all 360 months
2. Simulate asset returns for 360 months using chosen method
3. For each month t:
   - Get CVaR limit for month t
   - Use Hit-and-Run to generate N portfolios where CVaR < limit
   - Calculate CVaR and expected return for each portfolio
4. Trajectory i = connecting portfolio i across all months
5. Export matrices to Excel

### Hit-and-Run Algorithm

The Hit-and-Run algorithm samples uniformly from the feasible region defined by:
- **Constraint 1**: Σw_i = 1 (weights sum to 1)
- **Constraint 2**: w_i ≥ 0 (no short-selling)
- **Constraint 3**: CVaR(w) < CVaR_limit (risk constraint)

**Steps**:
1. Find initial feasible point (portfolio satisfying all constraints)
2. Repeat N times:
   - Choose random direction on the simplex
   - Find feasible line segment along this direction
   - Sample uniformly from the segment
   - Move to new portfolio
3. Collect samples after burn-in period

**Advantages**:
- Explores full feasible region uniformly
- Handles complex non-convex CVaR constraints
- Provably converges to uniform distribution

### CVaR Calculation

For a portfolio with weights **w**:

1. Calculate portfolio returns: r_p = **R** · **w** (for all scenarios)
2. Sort returns (ascending)
3. VaR_α = α-quantile of r_p
4. CVaR_α = mean of returns below VaR_α

For ALPHA_CVAR = 0.90:
- CVaR = average of worst 10% of outcomes

### Simulation Methods

#### MVN (Multivariate Normal)

```python
# Estimate parameters from historical data
μ = mean(historical_returns)
Σ = covariance(historical_returns)

# Simulate future returns
R_future ~ N(μ, Σ)  # for each month
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
- Preserves exact marginal distributions
- Captures non-Gaussian features (skewness, kurtosis)
- Better tail dependence modeling

---
