# 00_target_return - Chilean Pension System Required Return Calculator

## Overview

This module calculates the required investment return needed to achieve a target pension replacement rate in the Chilean pension system (AFP). It simulates different demographic profiles (men, women, with and without contribution density reductions) to find what annual return is necessary to retire with a pension equal to, for example, 60% of pre-retirement salary.

The results from this module are used as reference benchmarks to calibrate the TARGET_RETURN_THRESHOLD in step 03 (trajectory_analyzer). This creates a connection between theoretical pension planning and actual portfolio performance analysis.

## What Does This Module Do?

**Input:** 
- Demographic parameters (age, gender, life expectancy)
- Economic parameters (salary, contribution rate, salary growth)
- Contribution density (percentage of months with contributions)
- Target replacement rate (for example: 60%)

**Process:** 
- For each demographic profile, use binary search to find the annual return that achieves the target replacement rate
- Simulate the complete pension lifecycle: accumulation phase + retirement phase
- Account for reduced contribution density (simulating labor market gaps)
- Calculate pension using annuity formula

**Output:** 
- Excel file with required returns for 4 profiles (male/female, with/without density reduction)
- Monthly detail of accumulation for each profile
- Sensitivity analysis showing replacement rates at different return levels
- Parameters used in the simulation

## Connection to Step 03 (Trajectory Analyzer)

**IMPORTANT:** This module provides calibration benchmarks for portfolio analysis.

**How they relate:**
1. Run this module to find required returns (e.g., 5.8% for male without gaps)
2. Use that value as TARGET_RETURN_THRESHOLD in step 03
3. Interpret step 03 results as: "X% of portfolio trajectories achieve the return needed for retirement in the Chilean pension system"

## File Structure

```
00_target_return/
├── parameters.py    # Model parameters (EDIT THIS FILE)
├── formulas.py      # Simulation logic and calculations
├── exporters.py     # Excel export functionality
├── main.py          # Main execution script
└── README.md        # This file
```

## Configuration Parameters

All parameters are defined in `parameters.py`. Edit this file to change the simulation settings.

### Demographic Parameters

```python
age_start_work_male = 25      # Age when men start working
age_start_work_female = 25    # Age when women start working
age_retire_male = 65          # Legal retirement age for men
age_retire_female = 60        # Legal retirement age for women
life_expectancy_male = 86     # Life expectancy for men
life_expectancy_female = 90   # Life expectancy for women
```

**What they mean:**
- `age_start_work_male/female`: When the person enters the workforce and starts contributing (can be different by gender)
- `age_retire_male/female`: Legal retirement age in Chile (65 for men, 60 for women)
- `life_expectancy_male/female`: Expected age at death (determines pension payout period)

### Economic Parameters (in UF)

```python
salary_initial_male = 20.0     # Initial salary for men in UF (approx 800k CLP)
salary_initial_female = 20.0   # Initial salary for women in UF (approx 800k CLP)
contribution_rate = 0.16       # Mandatory contribution rate (16%)
contribution_ceiling = 81.6    # Contribution ceiling in UF
salary_growth_real = 0.0125    # Real annual salary growth (1.25%)
```

**What they mean:**
- `salary_initial_male/female`: Starting monthly salary in UF (Chilean inflation-indexed units), can be different by gender
- `contribution_rate`: Percentage of salary contributed to pension fund (16% in Chile)
- `contribution_ceiling`: Maximum salary subject to contributions (81.6 UF = official Chilean limit)
- `salary_growth_real`: Real salary growth per year (after inflation, in UF terms) - **applies to everyone regardless of contribution density**

**Why UF?**
- UF (Unidad de Fomento) is indexed to inflation
- All calculations in UF are "real" (inflation-adjusted)
- Using UF eliminates need to model inflation separately

### Return Parameters

```python
return_post_retirement = 0.025  # 2.5% real return after retirement
```

**What it means:**
- After retiring, the pension fund continues earning returns
- 2.5% is approximately the real yield on 10-year inflation-indexed government bonds

**Note:** The return during accumulation phase is what the model searches for (not a parameter).

### Target Parameters

```python
replacement_rate_target = 0.60  # 60% replacement rate
```

**What it means:**
- Replacement rate = Monthly pension / Average salary of last 10 working years
- 60% means the pension is 60% of pre-retirement salary

### Contribution Density

```python
# Contribution density: percentage of months with contributions
# 1.0 = contributes every month (100%)
# 0.7 = contributes 70% of the time (simulates gaps)

contribution_density_male_no_gaps = 1.0       # 100% - no gaps
contribution_density_male_with_gaps = 0.583   # 58.3% - with gaps

contribution_density_female_no_gaps = 1.0     # 100% - no gaps
contribution_density_female_with_gaps = 0.496 # 49.6% - with gaps
```

**What they mean:**
- Contribution density simulates labor market participation and gaps distributed throughout the working life
- Instead of modeling discrete unemployment periods, this represents an **average contribution rate**
- Examples:
  - `1.0` (100%): Person contributes every single month
  - `0.583` (58.3%): Person contributes 58.3% of months on average (e.g., informal work, unemployment spells)

### Binary Search Parameters

```python
return_min = 0.0      # Minimum return for search (0%)
return_max = 0.20     # Maximum return for search (20%)
tolerance = 0.0001    # Tolerance for convergence
max_iterations = 100  # Maximum iterations
```

**What they mean:**
- The model uses binary search to find the required return
- Searches within interval [return_min, return_max]
- Stops when replacement rate is within `tolerance` of target
- Gives up after `max_iterations` if no convergence

## How to Run

```bash
python -m 00_target_return.main
```

Or, if you are inside the `00_target_return/` directory:

```bash
python main.py
```

## Output File

**Location:** `outputs/target_return.xlsx`

**Structure:** 7 sheets

### Sheet 1: "Parameters"

Lists all parameters used in the simulation.

**Format:**
- Column 1: Parameter name
- Column 2: Value

### Sheet 2: "Summary"

One row per demographic profile with key results.

**Columns:**

| Column | Description | Example |
|--------|-------------|---------|
| `Profile` | Demographic profile description | Male without gaps |
| `Contribution Density (%)` | Percentage of months contributing | 100.0% |
| `Required Return (%)` | Annual return needed to achieve target | 5.82% |
| `Achieved Replacement Rate (%)` | Actual replacement rate with that return | 60.00% |
| `Final Accumulated Balance (UF)` | Total fund at retirement | 4,523.45 UF |
| `Monthly Pension (UF)` | Monthly pension payment | 18.56 UF |
| `Average Salary Last 10 Years (UF)` | Avg monthly salary before retirement | 30.93 UF |
| `Effective Contribution Years` | Years actually contributing (years × density) | 40.0 years |

**Interpretation:**
- Required Return: This is the key output - use this value in step 03
- Lower return = easier to achieve (less demanding on portfolio)
- Effective Contribution Years = Total working years × Contribution density

### Sheets 3-6: "Male_without_gaps", "Male_with_gaps", etc.

Monthly detail of the accumulation phase for each profile.

**Columns:**

| Column | Description |
|--------|-------------|
| `year` | Year number (1, 2, ..., 40) |
| `month` | Month number (1, 2, ..., 480) |
| `age` | Age in years (25.00, 25.08, ..., 64.92) |
| `salary_uf` | Monthly salary in UF |
| `contribution_base_uf` | Base contribution before density (16% of salary, capped) |
| `contribution_density` | Contribution density factor (1.0, 0.7, 0.6, etc.) |
| `contribution_effective_uf` | Actual contribution (base × density) |
| `balance_uf` | Accumulated balance in UF |

### Sheet 7: "Sensitivity Analysis"

Shows how replacement rate varies with different return levels.

**Columns:**
- `Return (%)`: Annual return tested (0%, 1%, 2%, ..., 15%)
- For each profile: `[Profile] - Replacement Rate (%)`

## How It Works

### Overall Process

For each of the 4 demographic profiles, the model:

**Step 1: Initialize Search Range**
- Start with return interval [0%, 20%]

**Step 2: Binary Search Loop**

For each iteration:

1. Test median return: `return_test = (return_min + return_max) / 2`
2. Simulate accumulation phase with that return
3. Calculate pension with accumulated balance
4. Calculate replacement rate
5. Compare to target (60%):
   - If too low: need higher return → `return_min = return_test`
   - If too high: need lower return → `return_max = return_test`
6. Repeat until convergence (replacement rate within 0.01% of target)

**Step 3: Record Results**
- Save required return, final balance, pension, etc.

### Accumulation Phase Simulation

This is the core of the model. For each month from start of work to retirement:

**Step 1: Get Parameters by Gender**
```
age_start = age_start_work_male (or female)
age_retirement = age_retire_male (or female)
salary_initial = salary_initial_male (or female)
contribution_density = density_male_with_gaps (or no_gaps, or female variants)
```

**Step 2: Salary Update (once per year)**
```
If month is January (month % 12 == 0):
    salary = salary × (1 + salary_growth_real)
    
Note: Salary ALWAYS grows, regardless of contribution density
```

**Step 3: Calculate Contribution**
```
# Calculate base contribution (what you'd contribute at 100% density)
taxable_salary = min(salary, contribution_ceiling)
contribution_base = taxable_salary × contribution_rate

# Apply density
contribution_effective = contribution_base × contribution_density

# Add to balance
balance = balance + contribution_effective
```

**Step 4: Apply Returns**
```
monthly_return = (1 + annual_return)^(1/12) - 1
balance = balance × (1 + monthly_return)
```

**Step 5: Track Last 10 Years Salaries**
```
If age >= retirement_age - 10:
    Save salary for replacement rate calculation
```

### Pension Calculation

At retirement, the accumulated balance is converted to a monthly pension using the **annuity immediate formula** (ordinary annuity).

#### Annuity Formula Explained

**Type of annuity:** Ordinary annuity (annuity immediate) with capital depletion

**Formula:**
```
PMT = PV × [r(1+r)^n] / [(1+r)^n - 1]
```

Where:
- **PMT** = Monthly pension payment (what we're solving for)
- **PV** = Present Value = Accumulated balance at retirement
- **r** = Monthly interest rate = (1 + annual_return)^(1/12) - 1
- **n** = Number of periods = (life_expectancy - retirement_age) × 12

**What this formula represents:**

This is the payment formula for an ordinary annuity, which answers:
> "If I have PV pesos today earning r% per period, what constant payment PMT can I receive for n periods such that my balance reaches exactly zero at period n?"

**Derivation (for reference):**

The present value of an annuity formula is:
```
PV = PMT × [(1+r)^n - 1] / [r(1+r)^n]
```

Solving for PMT:
```
PMT = PV × [r(1+r)^n] / [(1+r)^n - 1]
```

## Next Steps

After running this module:

1. **Review Summary sheet:** Understand required returns for each profile
2. **Check Sensitivity:** See how robust results are to return assumptions
3. **Calibrate step 03:** Use required returns as TARGET_RETURN_THRESHOLD
4. **Interpret step 03 results:** X% success rate = X% of portfolios meet pension goals

This module provides the "target" that portfolio strategies in steps 01-03 are trying to hit.
