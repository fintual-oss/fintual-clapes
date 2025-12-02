# ===============================================================
#   Portfolio Trajectory Generator - Hit and Run
#   
#   Generates portfolio trajectories using the Hit-and-Run algorithm
#   to ensure CVaR compliance with glidepath limits.
#   
#   For each CVaR glidepath curve from step 01:
#     - For each month t, generate N portfolios where CVaR < limit(t)
#     - Build trajectories by connecting portfolios across months
#     - Export CVaR and returns matrices to Excel
#   
#   How to run:
#   $ python -m 02_portfolio_simulator.main
#   
#   Configuration:
#   - Edit parameters in main.py (ALPHA_CVAR, N_PORTFOLIOS_PER_MONTH, etc.)
# ===============================================================
