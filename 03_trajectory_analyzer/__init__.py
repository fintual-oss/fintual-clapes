# ===============================================================
#   Trajectory Analyzer
#   
#   Analyzes portfolio trajectories from step 02 (Hit-and-Run).
#   
#   For each CVaR glidepath curve:
#     - Calculates cumulative annualized returns
#     - Calculates percentage above target return (default: 6%)
#     - Computes comprehensive statistics and percentiles
#     - Calculates cumulative risk from CVaR limits (step 01)
#     - Combines with curve parameters from step 01
#     - Exports single-sheet Excel report
#   
#   How to run:
#   $ python -m 03_trajectory_analyzer.main
#   
#   Configuration:
#   - Edit TARGET_RETURN_THRESHOLD in main.py (default: 6%)
#   - Edit PERCENTILES in main.py
#   - Choose PROCESS_ALL_CURVES or specific curves
# ===============================================================
