# ===============================================================
#   Chilean Pension System Required Return Calculator
#   
#   Calculates the investment return needed to achieve adequate
#   retirement income in the Chilean AFP pension system.
#   
#   For each demographic profile (male/female, with/without gaps):
#     - Simulates complete pension lifecycle (accumulation + retirement)
#     - Uses binary search to find required return for 60% replacement rate
#     - Accounts for contribution density (labor market gaps)
#     - Calculates pension using annuity formula
#     - Exports comprehensive Excel report
#   
#   How to run:
#   $ python -m 00_target_return.main
#   
#   Configuration:
#   - Edit parameters.py to modify demographic and economic assumptions
#   - Default target: 60% replacement rate
#   - Results in UF (Chilean inflation-indexed units)
#   
# ===============================================================
