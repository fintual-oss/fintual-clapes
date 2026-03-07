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
- Calculate returns for each portfolio using selected scenario(s) based on USE_RANDOM_SCENARIOS mode
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
HORIZON_MONTHS = 420             # Total months in simulation (35 years)
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
- Minimum recommended: 100 scenarios, but ideally 1000+ for stable results
- With ALPHA_CVAR=0.90 (worst 10%), you need enough scenarios so that 10% gives at least 10 observations
- Default: 10,000 scenarios

**HORIZON_MONTHS:**
- Total number of months in the investment horizon
- Must match the number of months in step 01
- Formula: (T_END_YEARS - T_START_YEARS) × 12
- Current configuration: (60 - 25) × 12 = 420 months = 35 years (female retirement age)
- **CRITICAL:** This must equal the MONTHS value from step 01 config

**Important:** The code does not automatically validate this. You must manually ensure:
- Step 01: MONTHS = (T_END_YEARS - T_START_YEARS) × 12
- Step 02: HORIZON_MONTHS = same value

**Example:** If step 01 uses ages 25-60 (35 years = 420 months), then HORIZON_MONTHS must be 420.

**Note on gender configuration:** Current configuration uses female retirement age (60 years, 420 months total). For male profiles with retirement at 65, HORIZON_MONTHS would be 480 (40 years × 12 months).

### Scenario Selection Mode

```python
USE_RANDOM_SCENARIOS = False  # Scenario assignment mode
```

**Options:**

**USE_RANDOM_SCENARIOS = False (Default - Fixed Scenario Mode):**
- All portfolios in month t use the same randomly selected scenario
- All curves share the same month-to-month scenario sequence
- Controlled by SCENARIO_SEED for reproducibility
- Ensures fair comparison: all portfolios face identical market conditions

**USE_RANDOM_SCENARIOS = True (Random Scenario Mode):**
- Each portfolio in month t uses a different randomly selected scenario
- Each curve has its own independent random scenario sequence
- Controlled by RANDOM_SCENARIO_SEED for reproducibility
- Maximizes scenario diversity across portfolios and curves

**Which mode to use:**
- Fixed mode: When comparing portfolio strategies under identical market conditions
- Random mode: When maximizing exploration of different market realizations

### Random Seeds

```python
RETURNS_SEED = 111           # Seed for asset return simulation
HIT_RUN_SEED = 222           # Seed for Hit-and-Run algorithm
SCENARIO_SEED = 333          # Seed for fixed scenario mode
RANDOM_SCENARIO_SEED = 444   # Seed for random scenario mode
```

**What they mean:** These control the random number generation to make results reproducible.

**RETURNS_SEED:**
- Controls the simulation of future asset returns
- Same seed = identical market scenarios generated

**HIT_RUN_SEED:**
- Controls the Hit-and-Run algorithm that generates portfolios
- Same seed = identical portfolios generated

**SCENARIO_SEED:**
- Only used when USE_RANDOM_SCENARIOS = False
- Controls which scenario is selected for each month
- Same seed = identical market realizations each month
- All curves share the same month-to-month scenario sequence

**RANDOM_SCENARIO_SEED:**
- Only used when USE_RANDOM_SCENARIOS = True
- Controls the random scenario assignment for each portfolio
- Same seed = identical random scenario assignments
- Each curve gets a different but reproducible scenario sequence

**Why separate seeds?**
- Allows you to test different aspects independently
- Example: Keep RETURNS_SEED fixed, change HIT_RUN_SEED to test different portfolio strategies under the same market scenarios
- Example: Keep RETURNS_SEED and HIT_RUN_SEED fixed, change RANDOM_SCENARIO_SEED to test different market realization patterns

**Reproducibility:** Using the same seeds will produce exactly the same results every time.

### Parallelization Configuration

```python
N_PROCESSES = 15  # Number of parallel processes
```

**What it means:** Controls how many months are processed simultaneously within each curve.

**Options:**
- `None` or `"auto"`: Uses all available CPU cores minus 1 (recommended)
- Integer (e.g., 1, 4, 8, 15): Uses exactly that many processes
- `1`: Disables parallelization (sequential month processing)

**How it works:**
- Curves are processed sequentially (one at a time)
- Within each curve, months are processed in parallel
- This is efficient because months are independent within a curve

**Memory consideration:**
- Each parallel process loads the month's return scenarios (N_TRAJ × N_ASSETS)
- More processes = more memory needed
- Generally safe with "auto" for typical workloads

**Example:** With N_PROCESSES=15 and HORIZON_MONTHS=420:
- Process 15 months simultaneously
- Complete all 420 months in 28 batches (420/15)
- Much faster than sequential processing

### Curve Selection

```python
PROCESS_ALL_CURVES = True  # Process all curves or only selected ones
CURVES_TO_PROCESS = ["curve_0001", "curve_0002"]  # Used if PROCESS_ALL_CURVES=False
```

**PROCESS_ALL_CURVES:**
- `True`: Process every curve from step 01
- `False`: Only process curves listed in CURVES_TO_PROCESS

**CURVES_TO_PROCESS:**
- Only used when PROCESS_ALL_CURVES = False
- List of curve names to process (must match names from step 01)

**Use cases:**
- Set PROCESS_ALL_CURVES = True for full analysis
- Set PROCESS_ALL_CURVES = False for testing or debugging specific curves

## How to Run

```bash
python -m 02_portfolio_simulator.main
```

Or, if you are inside the `02_portfolio_simulator/` directory:

```bash
python main.py
```

## Output Files

**Location:** `outputs/hit_run_results/`

**Files:** One Excel file per glidepath curve: `curve_XXXX_results.xlsx`

**Structure:** Each file has one sheet named "returns":

**Format (TRANSPOSED for large simulations):**
- **Rows:** Trajectories (trajectory_001, trajectory_002, ..., trajectory_N)
- **Columns:** Months (Month_1, Month_2, ..., Month_420)

**Why transposed?**
- Excel has a 16,384 column limit but over 1 million row limit
- With standard orientation (months as rows): Limited to ~16,000 trajectories
- With transposed orientation (months as columns): Can store millions of trajectories
- This format allows simulating 100,000+ trajectories without hitting Excel limits

**Example structure:**

```
              Month_1   Month_2   Month_3   ...   Month_420
trajectory_001  0.0234   0.0156  -0.0089   ...    0.0123
trajectory_002  0.0187   0.0201   0.0076   ...   -0.0034
trajectory_003 -0.0045   0.0134   0.0198   ...    0.0156
...               ...      ...      ...    ...       ...
trajectory_N    0.0167  -0.0023   0.0145   ...    0.0089
```

**Values:** Monthly returns as decimals (0.0234 = 2.34% return)

## How It Works

### Overall Process

**Step 1: Load Historical Returns**
- Read historical asset returns from `returns.csv`
- Estimate mean vector and covariance matrix

**Step 2: Make Covariance PSD**
- Ensure the covariance matrix is positive semi-definite
- Replace any negative eigenvalues with small positive values

**Step 3: Simulate Future Returns**
- Generate N_TRAJ scenarios for each of HORIZON_MONTHS months
- Use either MVN or Copula method
- Result: 3D array of shape (HORIZON_MONTHS, N_TRAJ, N_ASSETS)

**Step 4: Generate Scenario Selection**
- **Fixed mode:** Pre-generate HORIZON_MONTHS random scenario indices using SCENARIO_SEED
- **Random mode:** Generate scenario indices on-the-fly for each portfolio and curve

**Step 5: Load Glidepath Curves**
- Load CVaR limits for each curve from step 01

**Step 6: Process Each Curve (months in parallel)**

For each month t:
1. Get the CVaR limit for month t from the glidepath
2. Get the simulated returns for month t (all N_TRAJ scenarios)
3. Use Hit-and-Run algorithm to generate N_PORTFOLIOS_PER_MONTH portfolios where CVaR < limit
4. Calculate each portfolio's return based on scenario selection mode:
   - Fixed mode: All portfolios use the single pre-selected scenario for month t
   - Random mode: Each portfolio uses its own randomly assigned scenario
5. Store the return values

**Step 7: Build Trajectories**
- Trajectory i is formed by connecting portfolio i from each month
- Each trajectory has HORIZON_MONTHS return values

**Step 8: Export to Excel**
- Save returns matrix (N_PORTFOLIOS_PER_MONTH × HORIZON_MONTHS) in transposed format

### Scenario Selection Modes

The module supports two modes for assigning market scenarios to portfolios when calculating returns.

#### Fixed Scenario Mode (USE_RANDOM_SCENARIOS = False)

Each month uses a single randomly selected scenario for all portfolios.

**How it works:**

```python
# Pre-generate scenario indices once (at start of simulation)
scenario_indices = rng_scenario.integers(0, N_TRAJ, size=HORIZON_MONTHS)

# For each month t:
scenario_idx = scenario_indices[t]  # Single pre-selected index (0 to N_TRAJ-1)
selected_scenario_returns = month_returns[scenario_idx, :]  # One scenario
portfolio_returns = portfolios @ selected_scenario_returns  # All portfolios use same scenario
```

**Characteristics:**
- All portfolios in month t face the same market condition
- All curves share the same HORIZON_MONTHS-length scenario sequence
- Pre-selected scenarios are generated once using SCENARIO_SEED

**Advantages:**

1. **Fair comparison:** Portfolio A and Portfolio B face identical market conditions. No portfolio gets lucky or unlucky with random scenario assignment.

2. **Comparable trajectories:** Direct performance comparison is meaningful because all trajectories experienced the same market path.

3. **Reproducible:** Using the same SCENARIO_SEED gives the same market realizations every time.

**Use when:** Comparing portfolio strategies under identical market conditions.

#### Random Scenario Mode (USE_RANDOM_SCENARIOS = True)

Each portfolio uses a different randomly selected scenario.

**How it works:**

```python
# For each month t and each portfolio i:
random_scenario_idx = random_integers(0, N_TRAJ-1)  # Different for each portfolio
selected_scenario_returns = month_returns[random_scenario_idx, :]
portfolio_returns[i] = portfolio[i] @ selected_scenario_returns
```

**Characteristics:**
- Each portfolio in month t faces a different market condition
- Each curve has its own independent random scenario sequence
- Scenarios are generated on-the-fly using curve-specific and month-specific seeds

**Advantages:**

1. **Maximum diversity:** Explores N_PORTFOLIOS_PER_MONTH different market realizations per month.

2. **Independent curves:** Each curve experiences different market paths, avoiding systematic bias.

3. **Reproducible:** Using the same RANDOM_SCENARIO_SEED gives the same random assignments every time.

**Use when:** Maximizing exploration of different market realizations across portfolios and curves.

#### Comparison

| Aspect | Fixed Mode | Random Mode |
|--------|-----------|-------------|
| Portfolios per month | Same scenario | Different scenarios |
| Curves | Share scenario sequence | Independent scenario sequences |
| Total scenarios used | HORIZON_MONTHS (shared across all curves) | N_PORTFOLIOS × HORIZON_MONTHS per curve |
| Best for | Strategy comparison | Maximum diversity |

**Note:** CVaR constraint enforcement uses all N_TRAJ scenarios during the Hit-and-Run generation process in both modes. The scenario selection mode only affects the final return calculation.

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

3. **Burn-in period:** Discard the first 20 portfolios to ensure we're sampling from the entire feasible region

4. **Collect samples:** Keep the next N_PORTFOLIOS_PER_MONTH portfolios

**Efficiency:** CVaR is only calculated during the Hit-and-Run process to validate feasibility. Once portfolios are generated, they are guaranteed to satisfy the constraint, so no post-validation is needed.

### CVaR Calculation (During Generation)

CVaR (Conditional Value at Risk) measures the average loss in the worst-case scenarios.

For a portfolio with weights w, CVaR is calculated as:

1. Calculate portfolio returns for all N_TRAJ scenarios: r_p = R · w
2. Convert returns to losses: L = -r_p
3. Find the worst α tail (e.g., worst 10% if α=0.90)
4. CVaR = average of the losses in that tail (reported as positive magnitude)

**Example with α=0.90 and N_TRAJ=10000:**
- Calculate 10000 portfolio returns
- Convert to losses (multiply by -1)
- Sort losses from largest to smallest
- Take the worst 1000 scenarios (top 10% largest losses)
- CVaR = average of those 1000 worst losses

**Important:** CVaR is reported as a positive value representing the magnitude of the average loss in the tail. For example:
- CVaR = 0.07 means "average loss in worst 10% scenarios is 7%"
- Target CVaR = 0.08 means "allow up to 8% average loss"
- Constraint CVaR < target_cvar compares magnitudes: 0.07 < 0.08 ✓

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

**Example with current configuration (female retirement):**
- Step 01: T_START_YEARS=25, T_END_YEARS=60 → MONTHS=420
- Step 02: HORIZON_MONTHS must equal 420

**Example with male retirement:**
- Step 01: T_START_YEARS=25, T_END_YEARS=65 → MONTHS=480
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

### Configuration for Different Gender Profiles

**Current configuration:** Female retirement age (60 years, 420 months)

**To configure for male profiles:**
```python
HORIZON_MONTHS = 480  # 40 years (65 - 25)
```

This must match the corresponding change in step 01.

## Next Step

After running this module, proceed to step 03 (trajectory_analyzer) to analyze the performance of all generated trajectories and identify the best glidepath strategies.
