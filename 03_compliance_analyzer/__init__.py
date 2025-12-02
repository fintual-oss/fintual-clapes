# ===============================================================
#   Trajectory Analyzer
#   
#   Analyzes portfolio trajectories from step 02 (Hit-and-Run).
#   
#   For each CVaR glidepath curve:
#     - Calculates cumulative annualized returns
#     - Calculates percentage above target return (4%)
#     - Computes comprehensive statistics and percentiles
#     - Combines with curve parameters from step 01
#     - Exports comprehensive Excel report
#   
#   How to run:
#   $ python -m 03_trajectory_analyzer.main
#   
#   Configuration:
#   - Edit TARGET_RETURN_THRESHOLD in main.py (default: 4%)
#   - Edit PERCENTILES in main.py
#   - Choose PROCESS_ALL_CURVES or specific curves
# ===============================================================