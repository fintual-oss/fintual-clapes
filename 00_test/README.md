# 00_test - Portfolio Diversity Analyzer

## Overview

This module analyzes the diversity of portfolios generated in step 02 (portfolio simulator). It re-generates portfolios using the **exact same random seeds** as step 02 to extract portfolio weights (which are not saved in step 02) and calculates comprehensive diversity metrics.

**Purpose**: Understand how diverse the generated portfolios are month-by-month and across trajectories.

## What Does This Module Do?

**Input**: CVaR glidepath curves (from step 01) + Historical returns  
**Process**: 
1. Re-generate portfolios using SAME seeds as step 02
2. Extract portfolio weights (asset allocations)
3. Calculate diversity metrics for each month
**Output**: Excel files with diversity analysis (one per curve)

## Key Features

- **Exact Reproducibility**: Uses same seeds as step 02 → analyzes the actual portfolios used
- **Comprehensive Metrics**: Mean, std dev, range, percentiles, concentration measures
- **Month-by-Month Analysis**: Track how portfolio composition evolves over 480 months
- **Parametrizable**: Choose number of portfolios to analyze (100 for testing, 1000 for final)
- **Independent Module**: Easy to delete if not needed in final analysis

## File Structure

```
00_test/
├── __init__.py                      # Package metadata
├── test_config.py                   # Configuration parameters (EDIT HERE)
├── main.py                          # Main execution script
├── test_routes.py                   # Path management
├── test_portfolio_generator.py      # Re-generates portfolios with same seeds
├── test_diversity_metrics.py        # Calculates diversity metrics
├── test_exporters.py               # Exports results to Excel
└── README.md                        # This file
```

## Configuration (test_config.py)

### 1. Curve Selection
```python
PROCESS_ALL_CURVES = False
CURVES_TO_ANALYZE = [
    "curve_0001",
    "curve_0002",
    "curve_0003",
]
```

### 2. Number of Portfolios
```python
N_PORTFOLIOS_TO_ANALYZE = 100  # 100 for testing, 1000 for final analysis
```
- Fewer portfolios = faster execution, good for testing
- More portfolios = more comprehensive analysis

### 3. Random Seeds (CRITICAL - Must Match Step 02)
```python
RETURNS_SEED = 42       # Must match 02_portfolio_simulator
HIT_RUN_SEED = 123      # Must match 02_portfolio_simulator
SCENARIO_SEED = 999     # Must match 02_portfolio_simulator
```
**⚠️ IMPORTANT**: These seeds MUST be identical to those used in `02_portfolio_simulator/main.py` to ensure reproducibility.

### 4. Simulation Parameters (Must Match Step 02)
```python
SIMULATION_METHOD = "copula"  # Must match step 02
ALPHA_CVAR = 0.90            # Must match step 02
N_TRAJ = 10_000              # Must match step 02
HORIZON_MONTHS = 480         # Must match step 02
```

### 5. Diversity Metrics
```python
PERCENTILES = [10, 25, 50, 75, 90]  # Percentiles to calculate
```

## Usage

### Basic Usage

```bash
cd 00_test
python main.py
```

### Prerequisites

**Required files**:
1. `returns.csv` - Historical returns (at repo root)
2. `outputs/glidepaths_universe.xlsx` - From step 01

**Important**: This module does NOT require step 02 to be run first. It re-generates the portfolios independently using the same logic and seeds.

## Output

### Location
```
outputs/portfolio_diversity/
├── curve_0001_diversity.xlsx
├── curve_0002_diversity.xlsx
└── curve_0003_diversity.xlsx
```

### Excel File Structure

Each Excel file contains multiple sheets:

#### Sheet 1: "summary"
Overview of the analysis
```
Parameter                Value
Curve Name              curve_0001
Number of Portfolios    100
Number of Months        480
Number of Assets        9
```

#### Sheet 2: "weights_mean"
**Mean portfolio weights for each asset, month by month**
```
       LKXIP  RACLCORP  IPSA  PEBUY  LEGATRUU  LF98TRUU  NDDUWI  NDUEEGF  NDX
Month                                                                         
1      0.15    0.12    0.10   0.11    0.13      0.11     0.09     0.10    0.09
2      0.15    0.12    0.10   0.11    0.13      0.11     0.09     0.10    0.09
3      0.15    0.11    0.10   0.12    0.13      0.11     0.09     0.10    0.09
...
480    0.05    0.08    0.05   0.08    0.18      0.20     0.12     0.14    0.10
```
**Interpretation**: Shows the average allocation to each asset across all 100 trajectories

#### Sheet 3: "weights_std"
**Standard deviation of weights**
```
       LKXIP  RACLCORP  IPSA  ...
Month                           
1      0.02    0.03    0.02  ...
```
**Interpretation**: Higher values = more variation in allocations across trajectories

#### Sheet 4: "weights_range"
**Range (max - min) of weights**
```
       LKXIP  RACLCORP  IPSA  ...
Month                           
1      0.08    0.11    0.07  ...
```
**Interpretation**: Shows the spread between highest and lowest allocation

#### Sheet 5: "concentration"
**Portfolio concentration metrics (averaged across trajectories)**
```
        HHI     Entropy  N_Effective_Assets
Month                                       
1      0.15     2.05        6.7
2      0.15     2.06        6.8
...
480    0.18     1.85        5.5
```

**Metrics explained**:
- **HHI (Herfindahl-Hirschman Index)**: Σ(w_i²)
  - Range: [0.11, 1.0] for 9 assets
  - Lower = more diversified
  - 0.11 = perfectly equal weights (1/9 each)
  - 1.0 = all money in one asset

- **Entropy**: -Σ(w_i × log(w_i))
  - Higher = more diversified
  - Maximum = log(9) ≈ 2.20 for equal weights

- **N_Effective_Assets**: 1 / Σ(w_i²)
  - Range: [1, 9]
  - Higher = more diversified
  - Interpretation: "effective number" of assets used

#### Sheets 6-10: Percentiles
- **weights_p10**: 10th percentile (90% of portfolios have higher allocation)
- **weights_p25**: 25th percentile
- **weights_p50**: Median allocation
- **weights_p75**: 75th percentile
- **weights_p90**: 90th percentile (only top 10% exceed this)

#### Sheets 11-12: Extremes
- **weights_min**: Minimum weight observed across all trajectories
- **weights_max**: Maximum weight observed across all trajectories

## Diversity Metrics Explained

### 1. Weight Statistics (Per Asset)

**Mean**: Average allocation across trajectories
- Shows "typical" portfolio composition
- Most important metric for understanding overall strategy

**Standard Deviation**: Variability in allocations
- High std = portfolios are very different from each other
- Low std = portfolios are similar

**Range**: Difference between max and min
- Shows the full spread of allocations
- Complements std dev

**Percentiles**: Distribution of allocations
- p50 (median) = typical allocation
- p10/p90 = extreme cases

### 2. Concentration Metrics (Portfolio-Level)

These measure how "spread out" the portfolio is across assets.

**Example interpretations**:

```
Month 1: HHI=0.15, Entropy=2.05, N_Effective=6.7
→ Portfolio is well diversified, using ~7 assets effectively

Month 240: HHI=0.16, Entropy=2.00, N_Effective=6.3
→ Slightly less diversified (mid-career)

Month 480: HHI=0.18, Entropy=1.85, N_Effective=5.5
→ More concentrated at retirement (fewer effective assets)
```

### 3. How to Use These Metrics

**Check if portfolios are diverse enough**:
- Low std/range = all portfolios are similar (might be too constrained)
- High std/range = portfolios are very different (good exploration)

**Understand portfolio evolution**:
- Track mean weights over time
- See how diversification changes (HHI, Entropy trends)

**Compare curves**:
- Which curve allows more diversification?
- Which curve leads to more concentrated retirement portfolios?

## Example Analysis Workflow

1. **Start with small sample**:
   ```python
   N_PORTFOLIOS_TO_ANALYZE = 100
   CURVES_TO_ANALYZE = ["curve_0001"]
   ```
   Run to test (fast: ~2-5 minutes per curve)

2. **Review results**:
   - Check weights_mean: Does allocation make sense?
   - Check concentration: Is diversification reasonable?
   - Check weights_std: Are portfolios sufficiently diverse?

3. **Scale up for final analysis**:
   ```python
   N_PORTFOLIOS_TO_ANALYZE = 1000
   PROCESS_ALL_CURVES = True
   ```
   Run for comprehensive analysis (~20-40 minutes per curve)

4. **Compare across curves**:
   - Which curves have most stable allocations?
   - Which allow better diversification?
   - How does concentration change with different (A, B, t_A)?

## Technical Details

### How It Works

1. **Load Data**: 
   - Historical returns from `returns.csv`
   - CVaR limits from step 01 glidepaths

2. **Re-generate Portfolios**:
   - Uses EXACT same code as `02_portfolio_simulator`
   - Same seeds → identical portfolios
   - But now captures weights instead of just returns

3. **Calculate Metrics**:
   - For each month: statistics across N portfolios
   - For each asset: mean, std, range, percentiles
   - For portfolio: concentration measures

4. **Export to Excel**:
   - One file per curve
   - Multiple sheets with different metrics
   - Clean, easy-to-analyze format

### Why Re-generate Instead of Saving Weights in Step 02?

- **Modularity**: Step 02 stays focused on returns/CVaR
- **Storage**: Weights are large (480 × 1000 × 9 per curve)
- **Flexibility**: Can analyze subset without re-running all of step 02
- **Clean separation**: Easy to delete this analysis later

## Performance

### Execution Time (Approximate)

| Portfolios | Curves | Time per Curve | Total Time |
|------------|--------|----------------|------------|
| 100        | 1      | 2-5 min       | 2-5 min    |
| 100        | 10     | 2-5 min       | 20-50 min  |
| 1000       | 1      | 20-40 min     | 20-40 min  |
| 1000       | 10     | 20-40 min     | 3-7 hours  |

**Tip**: Start with N_PORTFOLIOS_TO_ANALYZE=100 for testing, then scale up.

## Common Issues

### Issue: "Seeds don't match step 02"
**Solution**: Make sure RETURNS_SEED, HIT_RUN_SEED, and SCENARIO_SEED in `config.py` match those in `02_portfolio_simulator/main.py`

### Issue: "Import error from 02_portfolio_simulator"
**Solution**: Make sure you're running from the repo root or that Python can find the parent directory

### Issue: "High % of NaN values"
**Solution**: Some months might fail to generate portfolios (CVaR constraint too tight). This is normal for a small % of months.

---

**Next Steps**: 
- Review diversity metrics in Excel
- Compare across different curves
- Use insights to refine glidepath parameters in step 01
