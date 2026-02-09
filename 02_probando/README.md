# Portfolio Trajectory Generator - Backward Hit-and-Run

## Overview

This module generates portfolio trajectories using a **backward Hit-and-Run algorithm** that ensures:
- ✅ CVaR compliance for every month
- ✅ Temporal continuity between consecutive months
- ✅ Efficient computation (minimal burn-in)
- ✅ Automatic handling of infeasible points

## Key Innovation: Backward Generation

Unlike the original approach (which generates portfolios independently per month), this module generates **complete trajectories** from the **last month to the first month**:

```
Traditional approach:
  Month 1: Generate N portfolios independently
  Month 2: Generate N portfolios independently
  ...
  Month T: Generate N portfolios independently
  → Build trajectories by connecting portfolio i from each month
  → NO temporal continuity

Backward approach:
  Month T (most restrictive): Generate starting portfolio + burn-in
  Month T-1: Use Month T portfolio as initial point
  Month T-2: Use Month T-1 portfolio as initial point
  ...
  Month 1 (least restrictive): Use Month 2 portfolio as initial point
  → Each trajectory is coherent and evolves naturally
  → TEMPORAL CONTINUITY maintained
```

## Why Backward?

**Problem with forward generation**: 
- CVaR limits typically DECREASE over time (glidepath)
- Starting portfolio might not satisfy future restrictions
- Would require frequent projections and burn-in

**Advantage of backward**:
- CVaR limits INCREASE as we go backward
- Portfolio from more restrictive month automatically satisfies less restrictive months
- Minimal projections needed
- More efficient

## Algorithm

For each trajectory:

1. **Month T (final, most restrictive)**:
   - Find initial feasible point
   - Hit-and-Run with burn-in = 25
   - Result: w_T

2. **Month T-1**:
   - Check if w_T is feasible with returns_{T-1}
   - If YES:
     - Use w_T as initial point
     - Burn-in = 0 (if CVaR limit unchanged) or 5-20 (adaptive, if expanded)
   - If NO (rare):
     - Project w_T to feasible space
     - Burn-in = 10
   - Hit-and-Run → Result: w_{T-1}

3. **Repeat** for months T-2, T-3, ..., 1

4. **Reverse** trajectory to chronological order: [w_1, w_2, ..., w_T]

## Burn-in Strategy

| Situation | Burn-in | Reason |
|-----------|---------|--------|
| Final month (T) | 25 | Ensure different starting points across trajectories |
| Same CVaR limit + feasible | 0 | No need to forget initial point |
| Expanded CVaR limit + feasible | 5 (FIXED) | Explore a bit from previous point |
| Not feasible (rare) | 10 | Explore from projected point |

**Important**: The burn-in when CVaR expands is FIXED at 5 iterations (not adaptive).
This provides a consistent balance between:
- Exploring the expanded feasible space
- Not forgetting the previous portfolio completely
- Computational efficiency

## File Structure

```
02_portfolio_simulator_backward/
├── __init__.py                    # Module description
├── main.py                        # Main execution script
├── trajectory_generator.py        # Core backward generation functions
├── cvar_portfolio_sampler.py      # Hit-and-Run sampler (unchanged)
├── simulate_asset_returns.py      # Asset return simulation (unchanged)
├── loaders.py                     # Load CVaR glidepaths (unchanged)
├── exporters.py                   # Export results to Excel (unchanged)
├── routes.py                      # File path management (unchanged)
├── make_psd.py                    # PSD matrix adjustment (unchanged)
└── README.md                      # This file
```

## Configuration

Edit parameters in `main.py`:

### Trajectory Generation
```python
N_TRAJECTORIES = 10_000          # Number of independent trajectories
N_TRAJ = 10_000                   # Monte Carlo scenarios for asset returns
HORIZON_MONTHS = 420              # Time horizon
```

### Burn-in Parameters
```python
INITIAL_BURN_IN = 25              # Final month (most restrictive)
ADAPTIVE_BURN_IN = 5              # FIXED when CVaR expands (NOT adaptive)
PROJECTION_BURN_IN = 10           # When projection is needed
```

### Random Seeds
```python
RETURNS_SEED = 111       # Seed for simulated returns
TRAJECTORY_SEED = 222    # Seed for Hit-and-Run trajectory generation
SCENARIO_SEED = 333      # Seed for scenario selection per month
```

**Important**: All curves face the **SAME sequence of market scenarios**. This allows fair comparison of different glidepaths under identical market conditions.

### Parallelization
```python
N_PROCESSES = 15                  # Parallel processes (or "auto")
```

### Other Settings
```python
SIMULATION_METHOD = "copula"      # "mvn" or "copula"
ALPHA_CVAR = 0.90                 # CVaR confidence level
VALIDATE_TRAJECTORIES = True      # Validate constraints after generation
VERBOSE_FIRST_TRAJECTORY = True   # Print details for first trajectory
```

## Scenario Selection Strategy

**Key Design Choice**: All curves face the **SAME sequence of market scenarios**.

```python
# Generated once before processing curves:
scenario_rng = np.random.default_rng(SCENARIO_SEED)
scenario_indices = scenario_rng.integers(0, N_TRAJ, size=HORIZON_MONTHS)

# Result: [3456, 8921, 1234, ..., 7890]
#         Month 0: ALL curves use scenario 3456
#         Month 1: ALL curves use scenario 8921
#         Month 2: ALL curves use scenario 1234
#         ...
```

**Why?** This allows **fair comparison** between different CVaR glidepaths:
- All glidepaths experience the same market shocks
- Differences in performance are due to the glidepath strategy, not random luck
- Enables meaningful comparison of risk-return profiles

**Within each month**:
- All trajectories of a curve use the SAME scenario
- This ensures consistency when comparing trajectories within a curve

## Usage

```bash
# Run the module
python -m 02_portfolio_simulator_backward.main

# Or from project root
cd /path/to/project
python -m 02_portfolio_simulator_backward.main
```

## Input Requirements

The module expects:

1. **Historical returns** (`returns.csv`):
   - CSV file at repository root
   - Columns: asset names
   - Rows: historical periods

2. **CVaR glidepaths** (`outputs/glidepaths_universe.xlsx`):
   - From step 01 (glidepath generator)
   - Rows: t_start, t_A, A, B, t_B, t_end, Month_1, ..., Month_T
   - Columns: curve_0001, curve_0002, ...

## Output

For each curve, generates:
- **Excel file**: `outputs/hit_run_results/{curve_name}_results.xlsx`
- **Sheet "returns"**: Monthly returns matrix
  - Rows: trajectories (trajectory_001, trajectory_002, ...)
  - Columns: months (Month_1, Month_2, ..., Month_T)

## Validation

If `VALIDATE_TRAJECTORIES = True`, each trajectory is checked for:

1. **Weight sum = 1**: `sum(w_t) = 1.0` for all months t
2. **Non-negativity**: `w_{t,i} ≥ 0` for all assets i, months t
3. **CVaR compliance**: `CVaR(w_t) < limit_t` for all months t

Violations are reported in the console with details.

## Performance

**Computational cost per trajectory**:
```
1 optimization (w_safe)                    ← once per curve
+ T months × [
    1 CVaR calculation (feasibility check)
    + 0-20 CVaR calculations (projection, if needed)
    + burn_in iterations
  ]

Typical:
- 1 optimization: ~100 CVaR evaluations
- T months: 420 × (1 + 0-5 projection + 0-15 burn-in) ≈ 3,000-7,000 CVaR evaluations

Total per trajectory: ~3,000-7,000 CVaR evaluations
```

**vs. Original approach**:
```
Original: 420 months × (100 burn-in + N samples) × 1 CVaR
        = 420 × 100 = 42,000 CVaR evaluations (for burn-in alone)

Speedup: ~6-14x faster per trajectory
```

**Parallelization**: N_PROCESSES trajectories computed simultaneously.

## Key Functions

### `trajectory_generator.py`

#### `generate_single_trajectory_backward()`
Generates one complete trajectory using backward algorithm.

**Returns**:
- `trajectory`: array of shape (n_months, n_assets)
- `stats`: dict with generation statistics

#### `determine_burn_in_and_initial_point()`
Decides burn-in and initial point based on:
- Feasibility of previous portfolio
- Change in CVaR limit

**Returns**:
- `initial_point`: starting portfolio for Hit-and-Run
- `burn_in`: number of burn-in iterations
- `feasibility_status`: 'feasible', 'projected', or 'same_limit'

#### `linear_path_projection()`
Projects infeasible portfolio to feasible space using bisection.

**Method**: Binary search on line segment [w_safe, w_previous]

#### `validate_trajectory()`
Validates all constraints for a complete trajectory.

**Returns**: List of violations (empty if valid)

## Debugging

### Verbose Mode
```python
VERBOSE_FIRST_TRAJECTORY = True
```

Prints for first trajectory:
```
Mes 419: INICIAL - Burn-in = 25
Mes 418: feasible - Burn-in = 5
Mes 417: same_limit - Burn-in = 0
Mes 350: PROYECCIÓN - CVaR_prev=0.0654 > límite=0.0650, Burn-in=10
...
```

### Statistics
After each curve, reports:
```
Generation statistics:
  Successful trajectories: 10,000/10,000
  Total projections needed: 234
  Avg projections per trajectory: 0.02
  Total burn-in iterations: 87,450
  Avg burn-in per trajectory: 8.7
```

### Validation
If violations found:
```
⚠️ VALIDATION WARNINGS:
  Total violations: 5
  cvar_violation: 3 violations
    Trajectory 42, Month 156: CVaR = 0.0851 >= limit = 0.0850
    Trajectory 89, Month 203: CVaR = 0.0701 >= limit = 0.0700
    ...
  weight_sum: 2 violations
    Trajectory 123, Month 45: Sum of weights = 1.0001 ≠ 1.0
    ...
```

## Troubleshooting

### "No feasible point found"
**Cause**: CVaR limit too restrictive, no portfolio satisfies it.

**Solution**:
- Check CVaR limits in glidepath file
- Ensure limits are achievable with given assets
- Try increasing `target_cvar` slightly

### "Projection failed"
**Cause**: w_safe doesn't satisfy restriction.

**Solution**:
- Algorithm will try to find minimum CVaR portfolio
- If still fails, CVaR limit is impossible with these assets
- Review asset universe or relax limits

### Memory issues
**Cause**: Too many trajectories or scenarios in parallel.

**Solution**:
```python
N_PROCESSES = 1          # Disable parallelization
N_TRAJECTORIES = 1000    # Generate fewer trajectories
N_TRAJ = 5000            # Use fewer scenarios
```

## Comparison with Original Approach

| Aspect | Original | Backward |
|--------|----------|----------|
| Generation order | Month 1 → T | Month T → 1 |
| Trajectories | Built by indexing | Generated as units |
| Temporal continuity | ❌ No | ✅ Yes |
| Burn-in per month | 100 (fixed) | 0-25 (adaptive) |
| Projections needed | Frequent (forward) | Rare (backward) |
| CVaR evaluations/traj | ~42,000 | ~3,000-7,000 |
| Parallelization | By month | By trajectory |
| Output format | Same | Same |

## Examples

### Minimal Configuration (Testing)
```python
N_TRAJECTORIES = 100
N_TRAJ = 1000
HORIZON_MONTHS = 120
PROCESS_ALL_CURVES = False
CURVES_TO_PROCESS = ["curve_0001"]
N_PROCESSES = 4
```

### Production Configuration
```python
N_TRAJECTORIES = 10_000
N_TRAJ = 10_000
HORIZON_MONTHS = 420
PROCESS_ALL_CURVES = True
N_PROCESSES = 15
VALIDATE_TRAJECTORIES = True
```

### High-Performance Configuration
```python
N_TRAJECTORIES = 50_000
N_TRAJ = 20_000
HORIZON_MONTHS = 480
PROCESS_ALL_CURVES = True
N_PROCESSES = "auto"  # Use all cores - 1
VALIDATE_TRAJECTORIES = False  # Skip validation for speed
```

## Citation

Based on the Hit-and-Run algorithm with backward generation for CVaR-constrained portfolio trajectories.

Key innovation: Leveraging decreasing CVaR glidepath by generating backward to minimize burn-in and projections while maintaining temporal continuity.
