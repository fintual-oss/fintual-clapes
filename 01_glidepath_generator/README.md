# 01_glidepath_generator - CVaR Glidepath Universe Generator

## Overview

This module generates a comprehensive universe of CVaR (Conditional Value at Risk) glidepath curves for retirement planning. Each curve defines a maximum CVaR limit that varies over time from starting age to retirement age.

The output is an Excel file with all possible glidepath combinations based on your parameter ranges, ready to be used in step 02 for portfolio generation.

## What is a CVaR Glidepath?

A CVaR glidepath is a time-varying risk constraint that:
- **Starts at a higher CVaR limit (A)** when young → more risk tolerance
- **Transitions linearly** to a lower CVaR limit (B) as approaching retirement → less risk tolerance
- **Remains constant at the lower limit (B)** after the transition point

**Visual Example**: A=0.08, B=0.05, t_A=45, t_B=65

```
CVaR Limit
   0.08 |████████████████____________
        |                \           
   0.07 |                 \          
        |                  \         
   0.06 |                   \        
        |                    \       
   0.05 |                     ████████
        |__________________________|_____
        35     45              65    Age (years)
              (t_A)           (t_B)
```

**Phases:**
1. **Age 35-45**: CVaR = 0.08 (constant, higher risk tolerance)
2. **Age 45-65**: CVaR transitions linearly from 0.08 → 0.05
3. **Age 65+**: CVaR = 0.05 (constant, lower risk at retirement)

## Key Features

- **Piecewise Linear Paths**: Smooth transitions between risk levels
- **Comprehensive Grid Search**: Generates all valid parameter combinations
- **Flexible Configuration**: Easy to adjust age ranges and CVaR limits
- **Excel Export**: Clean output format for downstream analysis
- **Automatic Validation**: Ensures A ≥ B and t_A < t_B

## File Structure

```
01_glidepath_generator/
├── __init__.py          # Package metadata and documentation
├── config.py            # Main configuration parameters
├── cvar_piecewise.py    # Piecewise CVaR function definition
├── param_grid.py        # Parameter grid generation
├── universe.py          # Universe builder (all curves)
├── utils.py             # Utility functions
├── main.py              # Main execution script
└── routes.py            # Path management
```

## Configuration Parameters (in config.py)

All parameters can be edited in `config.py`:

### 1. Age Parameters
```python
T_START_YEARS = 25          # Starting age
T_END_YEARS   = 65          # Retirement age
T_B_YEAR = 65               # Transition end age
```

**Description**:
- **T_START_YEARS**: Age when investment begins
  - Typical values: 20-35 years old
  
- **T_END_YEARS**: Age at retirement
  - Typical values: 60-70 years old
  
- **T_B_YEAR**: Age when transition to final CVaR ends
  - Usually equals T_END_YEARS (flat at retirement)
  - Can be less than T_END_YEARS for continued transition

**Derived values** (calculated automatically):
```python
T_START_MONTHS = T_START_YEARS * 12
T_END_MONTHS   = T_END_YEARS * 12
MONTHS = T_END_MONTHS - T_START_MONTHS  # Total horizon
```

**Example**:
- Start: 25 years
- End: 65 years
- Horizon: 480 months (40 years)

### 2. Transition Start Age (t_A)
```python
T_A_YEARS_VALUES = list(range(40, 51))
```

**Description**: Ages when transition from A to B begins
- Creates one glidepath for each t_A value
- Must satisfy: T_START_YEARS < t_A < T_B_YEAR

**Examples**:
- `list(range(40, 51))` → [40, 41, 42, ..., 50] = 11 values
- `list(range(35, 61))` → [35, 36, ..., 60] = 26 values (wider range)
- `[45, 50, 55]` → Only 3 specific transition ages

**Interpretation**:
- **Earlier t_A** (e.g., 40): Transition starts early, more conservative sooner
- **Later t_A** (e.g., 55): Stay aggressive longer, late transition

### 3. CVaR Limit Ranges

#### Initial CVaR Limit (A) - When Young
```python
A_MIN, A_MAX, A_STEP = 0.06, 0.10, 0.01
```

**Description**: CVaR limit at young age (before transition)
- Higher A = more risk tolerance when young
- Range: A_MIN to A_MAX in steps of A_STEP

**Examples**:
- `(0.06, 0.10, 0.01)` → [0.06, 0.07, 0.08, 0.09, 0.10] = 5 values
- `(0.05, 0.15, 0.01)` → [0.05, 0.06, ..., 0.15] = 11 values
- `(0.08, 0.08, 0.01)` → [0.08] = Fixed at 8%


#### Final CVaR Limit (B) - At Retirement
```python
B_MIN, B_MAX, B_STEP = 0.05, 0.05, 0.01
```

**Description**: CVaR limit at retirement (after transition)
- Lower B = more conservative at retirement
- Range: B_MIN to B_MAX in steps of B_STEP

**Examples**:
- `(0.05, 0.05, 0.01)` → [0.05] = Fixed at 5%
- `(0.03, 0.07, 0.01)` → [0.03, 0.04, 0.05, 0.06, 0.07] = 5 values
- `(0.04, 0.06, 0.005)` → [0.04, 0.045, 0.05, 0.055, 0.06] = 5 values


### 4. Output Filename
```python
OUTPUT_XLSX = "glidepaths_universe.xlsx"
```

**Description**: Name of the output Excel file
- Saved in `outputs/` directory
- Default: "glidepaths_universe.xlsx"

### 5. Automatic Constraints

The system automatically enforces:
- **A ≥ B**: CVaR limit must decrease or stay constant (never increase)
- **t_A < t_B**: Transition must start before it ends

Only valid combinations are generated.

## Usage

### Basic Usage

```bash
cd 01_glidepath_generator
python main.py
```

### Output

**File**: `outputs/glidepaths_universe.xlsx`

**Structure**:
- **Columns**: Each curve (curve_0001, curve_0002, ..., curve_XXXX)
- **Rows**: 
  - Parameter rows: `t_start`, `t_A`, `A`, `B`, `t_B`, `t_end`
  - Monthly values: `Month_1`, `Month_2`, ..., `Month_480`

**Example**:
```
              curve_0001  curve_0002  curve_0003
t_start            25          25          25
t_A                40          40          40
A                0.06        0.07        0.08
B                0.05        0.05        0.05
t_B                65          65          65
t_end              65          65          65
Month_1          0.06        0.07        0.08
Month_2          0.06        0.07        0.08
...
Month_480        0.05        0.05        0.05
```

## How It Works

### Step-by-Step Process

**1. Generate Parameter Grid**
```python
# All valid combinations of (t_A, A, B)
# Subject to: A ≥ B and t_A < t_B

For each t_A in T_A_YEARS_VALUES:
    For each A in [A_MIN, A_MIN+A_STEP, ..., A_MAX]:
        For each B in [B_MIN, B_MIN+B_STEP, ..., B_MAX]:
            if A ≥ B and t_A < T_B_YEAR:
                Create curve (t_A, A, B)
```

**2. Build Each Curve**

For each valid combination, generate monthly CVaR values:

```python
For month m in [1, 2, ..., MONTHS]:
    age_m = T_START_MONTHS + m
    
    if age_m ≤ t_A_months:
        CVaR(m) = A  # Before transition
        
    elif t_A_months < age_m ≤ t_B_months:
        # Linear transition
        slope = (B - A) / (t_B_months - t_A_months)
        CVaR(m) = A + slope * (age_m - t_A_months)
        
    else:  # age_m > t_B_months
        CVaR(m) = B  # After transition
```

**3. Export to Excel**

All curves saved in single Excel file with clear structure.

## Understanding the Output

### Parameter Values

Each curve has these parameters:

| Parameter | Description | Units | Example |
|-----------|-------------|-------|---------|
| `t_start` | Starting age | years | 25 |
| `t_A` | Transition start age | years | 45 |
| `A` | Initial CVaR limit | decimal | 0.08 (8%) |
| `B` | Final CVaR limit | decimal | 0.05 (5%) |
| `t_B` | Transition end age | years | 65 |
| `t_end` | Retirement age | years | 65 |

### Monthly CVaR Values

- Each `Month_X` contains the maximum allowed CVaR for that month
- Values are in decimal form (0.06 = 6%)
- These limits will constrain portfolio generation in step 02

**Example trajectory for one curve**:
- Months 1-240 (age 25-45): CVaR = 0.08 (constant)
- Months 241-480 (age 45-65): CVaR decreases linearly from 0.08 to 0.05
- After month 480: CVaR = 0.05 (if extended)

## Validation

The module performs automatic validation:
- ✅ A ≥ B (CVaR decreases or stays constant)
- ✅ t_A < t_B (valid transition window)
- ✅ All values are numeric and positive
- ✅ Grid generation uses robust floating-point handling

Invalid combinations are automatically excluded.

---

**Next Step**: Run `02_portfolio_simulator` to generate portfolio trajectories for each glidepath curve