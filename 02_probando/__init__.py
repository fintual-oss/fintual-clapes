# ===============================================================
#   Portfolio Trajectory Generator - Backward Hit-and-Run
#   
#   Generates portfolio trajectories using the Hit-and-Run algorithm
#   with BACKWARD generation (from last month to first month) to ensure
#   CVaR compliance and temporal continuity.
#   
#   For each CVaR glidepath curve from step 01:
#     - Generate N independent trajectories using backward algorithm
#     - Each trajectory: one portfolio per month, generated from T→1
#     - Start at most restrictive CVaR (last month)
#     - Use previous portfolio as initial point when moving backward
#     - Apply adaptive burn-in based on CVaR limit expansion
#     - Project to feasible space when needed
#     - Export returns matrices to Excel
#   
#   How to run:
#   $ python -m 02_portfolio_simulator_backward.main
#   
#   Configuration:
#   - Edit parameters in main.py:
#     * N_TRAJECTORIES: number of independent trajectories
#     * INITIAL_BURN_IN: burn-in for final month (25)
#     * ADAPTIVE_BURN_IN: FIXED burn-in when CVaR expands (5)
#     * PROJECTION_BURN_IN: burn-in when projection needed (10)
# ===============================================================
