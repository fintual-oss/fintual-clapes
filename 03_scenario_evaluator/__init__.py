# ===============================================================
#   03_scenario_evaluator — Portfolio Trajectory Scenario Evaluator
#
#   Evaluates portfolio trajectory performance across multiple
#   scenario seeds, using the weight matrices from Module 02.
#
#   Pipeline (per curve):
#     1. Load weight tensor from HDF5: (HORIZON_MONTHS × N_PORTFOLIOS × N_ASSETS)
#     2. Shuffle portfolios within each month (breaks Markov
#        chain autocorrelation from Hit-and-Run)
#     3. Regenerate asset return scenarios with RETURNS_SEED=111
#        (same deterministic matrix used in Module 02)
#     4. For each scenario seed in SCENARIO_SEEDS:
#          a. Sample one scenario index per month → (HORIZON_MONTHS,)
#          b. Compute portfolio return per trajectory per month
#             → matrix (HORIZON_MONTHS × N_PORTFOLIOS)
#          c. Calculate annualized cumulative return per trajectory
#             → vector (N_PORTFOLIOS,)
#     5. Save results to HDF5: dataset (N_SEEDS × N_PORTFOLIOS)
#
#   Output:
#     outputs/scenario_results/<curve_name>.h5
#       └── Dataset 'annualized_returns': shape (N_SEEDS, N_PORTFOLIOS)
#
#   How to run:
#   $ python -m 03_scenario_evaluator.main
#
#   Configuration:
#   - Edit SCENARIO_SEEDS list in main.py
#   - Edit SHUFFLE_SEED for reproducibility of the within-month shuffle
#   - RETURNS_SEED and SIMULATION_METHOD must match Module 02 exactly
#
# ===============================================================
