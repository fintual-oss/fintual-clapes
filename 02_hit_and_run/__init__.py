# ===============================================================
#   02_hit_and_run — CVaR-Constrained Portfolio Weight Sampler
#
#   Generates portfolio weight tensors using the Hit-and-Run
#   algorithm, constrained by CVaR glidepath limits from step 01.
#
#   For each CVaR glidepath curve:
#     - For each month t (1..HORIZON_MONTHS), sample N portfolios
#       where CVaR(w) < cvar_limit(t) using the Hit-and-Run algorithm
#     - Save weight tensor (HORIZON_MONTHS × N_portfolios × N_assets)
#       to a compressed HDF5 file
#
#   Output:
#     outputs/hit_and_run_matrices/<curve_name>.h5
#       └── Dataset 'weights': shape (HORIZON_MONTHS, N_PORTFOLIOS, N_ASSETS)
#
#   How to run:
#   $ python -m 02_hit_and_run.main
#
#   Configuration:
#   - Edit the CONFIGURATION block at the top of main.py
#   - Key parameters: SIMULATION_METHOD, ALPHA_CVAR, N_PORTFOLIOS_PER_MONTH,
#     HORIZON_MONTHS, RETURNS_SEED, HIT_RUN_SEED, N_PROCESSES
#   - RETURNS_SEED must match the value used in module 03
#
# ===============================================================
