# ===============================================================
#   Monte Carlo simulation for MULTIPLE portfolios over 360 months
#   - Each month has its own random weight vector (drunken manager)
#   - Asset returns are simulated from a multivariate normal (MVN)
#   - Returns simulation can be FIXED with an optional seed (reproducible)
#   - For each portfolio:
#       (i) Average annualized cumulative return (annualized return)
#       (ii) Monthly CVaR at confidence level ALPHA
#   - Output (Excel):
#       * Sheet "cvar_by_portfolio": CVaR_t for each month t and portfolio p
#
#   Note:
#   - All main parameters (ALPHA, DELTA, N_TRAJ, etc.) are configured in main.py
# ===============================================================
