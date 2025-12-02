# 01_glidepath_generator - CVaR Glidepath Universe Generator

## Overview

This module generates a comprehensive universe of CVaR (Conditional Value at Risk) glidepath curves for retirement planning. Each curve defines a maximum CVaR limit that varies over time from starting age to retirement age.

## What is a CVaR Glidepath?

A CVaR glidepath is a time-varying risk constraint that:
- Starts at a higher CVaR limit (A) when young (more risk tolerance)
- Transitions linearly to a lower CVaR limit (B) as approaching retirement (less risk tolerance)
- Remains constant at the lower limit (B) after the transition point

## Key Features

- **Piecewise Linear Paths**: Smooth transitions between risk levels
- **Comprehensive Grid Search**: Generates all valid parameter combinations
- **Flexible Configuration**: Easy to adjust age ranges and CVaR limits
- **Excel Export**: Clean output format for downstream analysis

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

## Configuration (in config.py)

### Age Parameters
```python
T_START_YEARS = 35       # Starting age (e.g., 35 years old)
T_END_YEARS   = 65       # Retirement age (e.g., 65 years old)
T_B_YEAR = 65            # Transition end age (usually = retirement age)
```

### Transition Start Age (t_A)
```python
T_A_YEARS_VALUES = list(range(40, 51))  # Test ages 40, 41, ..., 50
```

### CVaR Limit Ranges
```python
# CVaR cap when young (A)
A_MIN, A_MAX, A_STEP = 0.06, 0.10, 0.01  # Range: 6% to 10% in 1% steps

# CVaR cap at retirement (B)
B_MIN, B_MAX, B_STEP = 0.05, 0.05, 0.01  # Fixed at 5%
```

### Constraints
- **A ≥ B**: CVaR limit must decrease or stay constant (never increase)
- **t_A < t_B**: Transition must start before it ends

## How CVaR Glidepaths Work

### Example Curve: A=0.08, B=0.05, t_A=45, t_B=65

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

## Usage

### Basic Usage

```bash
cd fintual-clapes
python -m 01_glidepath_generator.main
```

### Output

**File**: `outputs/glidepaths_universe.xlsx`

**Structure**:
- **Rows**: 
  - Parameter rows: `t_start`, `t_A`, `A`, `B`, `t_B`, `t_end`
  - Monthly values: `Month_1`, `Month_2`, ..., `Month_360`
- **Columns**: `curve_0001`, `curve_0002`, ..., `curve_XXXX`

**Example**:
```
              curve_0001  curve_0002  curve_0003
t_start            35          35          35
t_A                40          40          40
A                0.06        0.07        0.08
B                0.05        0.05        0.05
t_B                65          65          65
t_end              65          65          65
Month_1          0.06        0.07        0.08
Month_2          0.06        0.07        0.08
...
Month_360        0.05        0.05        0.05
```

## Customization Examples

### Example 1: Wider Age Range for t_A
```python
# config.py
T_A_YEARS_VALUES = list(range(35, 61))  # Ages 35-60
```

### Example 2: More CVaR Levels
```python
# config.py
A_MIN, A_MAX, A_STEP = 0.05, 0.15, 0.01  # 11 values: 5% to 15%
B_MIN, B_MAX, B_STEP = 0.03, 0.07, 0.01  # 5 values: 3% to 7%
```
**Result**: Many more curves (e.g., 26 ages × 11 A values × 5 B values = **1,430 curves**)

### Example 3: Different Horizon
```python
# config.py
T_START_YEARS = 30       # Start at age 30
T_END_YEARS   = 70       # Retire at age 70
# MONTHS will be automatically calculated as 480 months (40 years)
```

**Important**: If you change the horizon, also update `HORIZON_MONTHS` in step 02.

## Output Interpretation

### Parameter Values

- **t_start**: Starting age (years) - usually 35
- **t_A**: Age when transition begins (years) - e.g., 40-50
- **A**: CVaR limit when young (decimal) - e.g., 0.08 = 8%
- **B**: CVaR limit at retirement (decimal) - e.g., 0.05 = 5%
- **t_B**: Age when transition ends (years) - usually 65
- **t_end**: Retirement age (years) - usually 65

### Monthly CVaR Values

- Each `Month_X` row contains the maximum allowed CVaR for that specific month
- Values are in decimal form (0.06 = 6%)
- Portfolio CVaR in subsequent steps must stay below these limits

## Validation

The module performs automatic validation:
- ✅ A ≥ B (CVaR decreases or stays constant)
- ✅ t_A < t_B (valid transition window)
- ✅ All values are numeric and positive
- ✅ Grid generation uses robust floating-point handling

---
