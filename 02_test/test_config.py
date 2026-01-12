# ========================================
# CONFIGURATION FOR PORTFOLIO DIVERSITY ANALYZER
# ========================================

# ----------------------------------------
# Curve Selection
# ----------------------------------------
PROCESS_ALL_CURVES = False  # True = analyze all curves, False = only selected
CURVES_TO_ANALYZE = [
    "curve_0001",
    "curve_0002"
]

# ----------------------------------------
# Portfolio Generation Parameters
# ----------------------------------------
# Number of portfolios to generate per month
# NOTE: Use smaller values (e.g., 100) for testing, larger (e.g., 1000) for final analysis
N_PORTFOLIOS_TO_ANALYZE = 1_000  # Options: 100, 500, 1000

# ----------------------------------------
# Random Seeds (MUST MATCH step 02 for reproducibility)
# ----------------------------------------
# CRITICAL: These seeds MUST be the same as in 02_portfolio_simulator/main.py
# to ensure we're analyzing the exact same portfolios
RETURNS_SEED = 42       # Seed for asset return simulation
HIT_RUN_SEED = 123      # Seed for Hit-and-Run algorithm
SCENARIO_SEED = 999     # Seed for scenario selection per month

# ----------------------------------------
# Simulation Parameters (MUST MATCH step 02)
# ----------------------------------------
SIMULATION_METHOD = "copula"  # "mvn" or "copula" - must match step 02
ALPHA_CVAR = 0.90            # CVaR confidence level - must match step 02
N_TRAJ = 10_000              # Number of Monte Carlo scenarios - must match step 02
HORIZON_MONTHS = 480         # Investment horizon - must match step 02

# ----------------------------------------
# Diversity Metrics
# ----------------------------------------
# Percentiles to calculate for weight distributions
PERCENTILES = [10, 25, 50, 75, 90]

# ----------------------------------------
# Output
# ----------------------------------------
OUTPUT_SUBDIR = "portfolio_diversity"  # Subdirectory within outputs/
