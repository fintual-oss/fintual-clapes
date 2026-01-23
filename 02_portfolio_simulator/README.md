# 02_portfolio_simulator - Portfolio Trajectory Generator with Hit-and-Run

## Overview

This module takes CVaR glidepath curves from step 01 and generates portfolio trajectories that obey the risk constraints. For each glidepath curve, it creates many different portfolio paths where each path represents one possible investment strategy while staying within the CVaR limits.

The key innovation is the Hit-and-Run algorithm, which efficiently samples portfolios that satisfy the CVaR constraint during generation, eliminating the need for post-validation.

## What Does This Module Do?

**Input:** 
- CVaR glidepath curves from step 01 (the risk rules)
- Historical asset returns (to simulate future market conditions)

**Process:** 
- Simulate future market scenarios
- For each month and each glidepath, generate N different portfolios where CVaR < limit
- Calculate returns for each portfolio using a single randomly selected scenario per month
- Build complete trajectories by connecting portfolios across months

**Output:** 
- Excel files (one per glidepath curve) containing monthly returns for all trajectories

## File Structure

```
02_portfolio_simulator/
├── main.py                      # Main execution script (EDIT PARAMETERS HERE)
├── routes.py                    # Path management
├── loaders.py                   # Load glidepaths and historical returns
├── make_psd.py                  # Ensure covariance matrices are positive semi-definite
├── simulate_asset_returns.py    # Simulate future returns (MVN or Copula)
├── cvar_portfolio_sampler.py    # Hit-and-Run algorithm for CVaR portfolios
├── exporters.py                 # Export results to Excel
└── __init__.py                  # Package documentation
```

## Configuration Parameters

All parameters are defined at the top of `main.py`. Edit this file to configure the simulation.

### Simulation Method

```python
SIMULATION_METHOD = "copula"  # Options: "mvn" or "copula"
```

**Options:**

**"mvn" (Multivariate Normal):**
- Assumes asset returns follow a normal distribution
- Faster computation
- Simpler method
- May not capture extreme market events well

**"copula" (Gaussian Copula):**
- Preserves the actual distribution of historical returns for each asset
- Better captures extreme events and tail behavior
- More realistic for financial data
- Slower computation

**Recommendation:** Use "copula" for final analysis, use "mvn" for quick testing.

### CVaR Confidence Level

```python
ALPHA_CVAR = 0.90  # CVaR confidence level
```

**What it means:** This defines which tail of the distribution we care about when measuring risk.

**How to interpret:**
- 0.90 means we look at the worst 10% of scenarios (bottom 10%)
- 0.95 means we look at the worst 5% of scenarios (bottom 5%)

**Note:** The code internally converts this to `confidence_level = 1.0 - ALPHA_CVAR` for the CVaR calculation. So ALPHA_CVAR=0.90 becomes confidence_level=0.10 in the CVaRPortfolioSampler.

### Portfolio Generation

```python
N_PORTFOLIOS_PER_MONTH = 10_000  # Number of portfolios per month
N_TRAJ = 10_000                  # Monte Carlo scenarios
HORIZON_MONTHS = 480             # Total months in simulation
```

**What they mean:**

**N_PORTFOLIOS_PER_MONTH:**
- How many different portfolios to generate for each month
- Each portfolio becomes one trajectory when connected across all months
- More portfolios = more diverse strategies tested
- Default: 10,000 trajectories per curve

**N_TRAJ:**
- Number of Monte Carlo scenarios used during portfolio generation
- More scenarios = more accurate CVaR constraint enforcement
- Must be at least 100 for reasonable accuracy
- Default: 10,000 scenarios

**HORIZON_MONTHS:**
- Total number of months in the investment horizon
- Must match the number of months in step 01
- Formula: (T_END_YEARS - T_START_YEARS) × 12
- Example: (65 - 25) × 12 = 480 months = 40 years
- **CRITICAL:** This must equal the MONTHS value from step 01 config

### Random Seeds

```python
RETURNS_SEED = 111      # Seed for asset return simulation
HIT_RUN_SEED = 222      # Seed for Hit-and-Run algorithm
SCENARIO_SEED = 333     # Seed for scenario selection per month
```

**What they mean:** These control the random number generation to make results reproducible.

**RETURNS_SEED:**
- Controls the simulation of future asset returns
- Same seed = identical market scenarios generated

**HIT_RUN_SEED:**
- Controls the Hit-and-Run algorithm that generates portfolios
- Same seed = identical portfolios generated

**SCENARIO_SEED:**
- Controls which scenario is selected for each month
- Same seed = identical market realizations each month

**Why three separate seeds?**
- Allows you to test different aspects independently
- Example: Keep RETURNS_SEED and SCENARIO_SEED fixed, change HIT_RUN_SEED to test different portfolio strategies under the same market conditions

**Reproducibility:** Using the same three seeds will produce exactly the same results every time.

### Curve Selection

```python
PROCESS_ALL_CURVES = True  # Process all curves or selected subset

CURVES_TO_PROCESS = [      # Only used if PROCESS_ALL_CURVES = False
    "curve_0001",
    "curve_0002",
    "curve_0003"
]
```

**What it means:**

**PROCESS_ALL_CURVES = True:**
- Process every curve from step 01
- Use this for complete analysis

**PROCESS_ALL_CURVES = False:**
- Process only the curves listed in CURVES_TO_PROCESS
- Use this for testing or analyzing specific glidepaths
- Faster when you only want to test a few curves

## How to Run

```bash
python -m 02_portfolio_simulator.main
```

Or, if you are inside the `02_portfolio_simulator/` directory:

```bash
python main.py
```

### Prerequisites

Before running, ensure these files exist:

1. `returns.csv` at the repository root (historical asset returns)
2. `outputs/glidepaths_universe.xlsx` (from step 01)

## Output Files

**Location:** `outputs/hit_run_results/`

**Files:** One Excel file per curve: `curve_XXXX_results.xlsx`

**Structure:** Each Excel file contains 1 sheet:

### Sheet: "returns"

Monthly returns for each trajectory.

**Format (IMPORTANT - matrix is transposed for Excel compatibility):**
- **Rows:** Trajectories (trajectory_001, trajectory_002, ..., trajectory_10000)
- **Columns:** Months (Month_1, Month_2, ..., Month_480)
- **Values:** Return at that month for that trajectory (decimal form)

**Example:**
```
Trajectory      Month_1  Month_2  Month_3  ...  Month_480
trajectory_001  0.0065   0.0064   0.0066  ...    0.0045
trajectory_002  0.0068   0.0067   0.0065  ...    0.0046
trajectory_003  0.0063   0.0062   0.0064  ...    0.0044
...
```

**Interpretation:** The value at row trajectory_001, column Month_120 tells you the return earned by portfolio 1 during month 120.

**Why transposed?** Excel has a limit of 16,384 columns. By putting trajectories in rows and months in columns, we can simulate millions of trajectories (Excel supports 1,048,576 rows) while keeping months (typically 480) well within the column limit.

**Important:** These returns use a single randomly selected scenario per month (not averaged over all scenarios). All portfolios in a given month face the same market condition.

## How It Works

### Overall Process

For each glidepath curve, the simulation follows these steps:

**Step 1: Load CVaR Limits**
- Read the CVaR limit for each month from the glidepath curve
- These limits define the constraints for portfolio generation

**Step 2: Simulate Future Asset Returns**
- Using either MVN or Copula method, simulate N_TRAJ scenarios for each month
- This creates a 3D array: (HORIZON_MONTHS × N_TRAJ × N_ASSETS)
- Example shape: (480 × 10000 × 9) for 480 months, 10000 scenarios, 9 assets

**Step 3: Generate Scenario Selection**
- For each month, randomly select one scenario index (0 to N_TRAJ-1)
- This scenario will be used to calculate returns for all portfolios in that month
- Controlled by SCENARIO_SEED for reproducibility

**Step 4: Generate Portfolios Month by Month**

For each month t:

1. Get the CVaR limit for month t from the glidepath
2. Get the simulated returns for month t (all N_TRAJ scenarios)
3. Use Hit-and-Run algorithm to generate N_PORTFOLIOS_PER_MONTH portfolios where CVaR < limit
4. Calculate each portfolio's return using the single selected scenario for month t
5. Store the return values

**Step 5: Build Trajectories**
- Trajectory i is formed by connecting portfolio i from each month
- Each trajectory has HORIZON_MONTHS return values

**Step 6: Export to Excel**
- Save returns matrix (N_PORTFOLIOS_PER_MONTH × HORIZON_MONTHS) in transposed format

### Key Feature: Single Scenario per Month

Each month uses a single randomly selected scenario instead of averaging over all scenarios.

**How it works:**

```python
# For each month t:
scenario_idx = scenario_indices[t]  # Random index (0 to N_TRAJ-1)
selected_scenario_returns = month_returns[scenario_idx, :]  # One scenario
portfolio_returns = portfolios @ selected_scenario_returns  # Calculate returns
```

**Why use a single scenario?**

1. **Fair comparison:** All portfolios in month t face the same market condition. Portfolio A didn't get lucky with good scenarios while Portfolio B got unlucky.

2. **Comparable trajectories:** You can directly compare trajectory performance because they all experienced the same market path.

3. **Reproducible:** Using the same SCENARIO_SEED gives the same market realizations every time.

**Note:** CVaR constraint enforcement uses all N_TRAJ scenarios during the Hit-and-Run generation process. Only the final returns use a single scenario.

### Hit-and-Run Algorithm

The Hit-and-Run algorithm efficiently generates random portfolios that satisfy three constraints:

**Constraints:**
1. Weights sum to 1: Σw_i = 1
2. No short selling: w_i ≥ 0 for all i
3. CVaR is below limit: CVaR(w) < CVaR_limit

**How it works:**

1. **Find starting point:** Find any portfolio that satisfies all three constraints

2. **Repeat N_PORTFOLIOS_PER_MONTH times:**
   - Choose a random direction on the simplex (the set of all valid portfolios)
   - Find the longest line segment in that direction that stays within the feasible region
   - Pick a random point along that line segment
   - Move to that new portfolio

3. **Burn-in period:** Discard the first 50 portfolios to ensure we're sampling from the entire feasible region

4. **Collect samples:** Keep the next N_PORTFOLIOS_PER_MONTH portfolios

**Efficiency:** CVaR is only calculated during the Hit-and-Run process to validate feasibility. Once portfolios are generated, they are guaranteed to satisfy the constraint, so no post-validation is needed.

### CVaR Calculation (During Generation)

For a portfolio with weights w, CVaR is calculated as:

1. Calculate portfolio returns for all N_TRAJ scenarios: r_p = R · w
2. Convert returns to losses: L = -r_p
3. Find the worst α tail (e.g., worst 10% if α=0.90)
4. CVaR = average of the losses in that tail

**Example with α=0.90 and N_TRAJ=10000:**
- Sort the 10000 portfolio returns from worst to best
- Take the worst 1000 scenarios (bottom 10%)
- CVaR = average loss in those 1000 worst scenarios

### Asset Return Simulation Methods

#### Method 1: MVN (Multivariate Normal)

**Process:**
1. Estimate mean vector μ and covariance matrix Σ from historical returns
2. Ensure Σ is positive semi-definite using `f_make_psd()`
3. For each month, draw N_TRAJ samples from N(μ, Σ)

**Assumptions:**
- Returns are normally distributed
- Correlations are linear and constant
- No skewness or heavy tails

**When to use:** Quick testing, baseline comparisons

#### Method 2: Copula (Gaussian Copula)

**Process:**
1. Transform historical returns to uniform [0,1] using empirical CDF
2. Transform uniforms to Gaussian space: Z = Φ^(-1)(U)
3. Estimate correlation matrix in Gaussian space
4. For each month:
   - Simulate correlated Gaussian variables
   - Transform back to uniforms
   - Transform to returns using empirical inverse CDF

**Advantages:**
- Preserves exact marginal distributions from historical data
- Captures skewness, kurtosis, and other non-normal features
- Better models tail dependencies

**When to use:** Final analysis, realistic scenarios

### Making Covariance Matrix Positive Semi-Definite

The `f_make_psd()` function ensures the covariance matrix is valid:

1. Compute eigenvalues and eigenvectors of Σ
2. Replace any negative eigenvalues with a small positive value (eps=1e-12)
3. Reconstruct the matrix using the corrected eigenvalues

**Why this is needed:**
- Numerical errors can cause estimated covariance matrices to have tiny negative eigenvalues
- A covariance matrix must be positive semi-definite to be mathematically valid
- Without this correction, the MVN simulation would fail

## Important Notes

### Horizon Consistency

The HORIZON_MONTHS parameter must match the number of months in step 01.

**Example:**
- Step 01: T_START_YEARS=25, T_END_YEARS=65 → 480 months
- Step 02: HORIZON_MONTHS must equal 480

**What happens if they don't match:**
- If HORIZON_MONTHS is too small: Not all glidepath months will be simulated
- If HORIZON_MONTHS is too large: Code will fail because glidepath doesn't have enough months

### Validation

The code includes built-in validation:
- Checks that SIMULATION_METHOD is either "mvn" or "copula"
- Checks that ALPHA_CVAR is between 0 and 1
- Checks that N_PORTFOLIOS_PER_MONTH ≥ 1
- Warns if N_TRAJ < 100 (may produce unstable results)

## Next Step

After running this module, proceed to step 03 (trajectory_analyzer) to analyze the performance of all generated trajectories and identify the best glidepath strategies.
