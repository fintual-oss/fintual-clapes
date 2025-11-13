# ===============================================================
#   Glidepaths vs. Portfolios Comparison (as a Python package)
#   - Reads CVaR by portfolio (Loop_drunken_portfolio_results.xlsx)
#   - Reads CVaR glidepaths (glidepaths_results.xlsx)
#   - Checks, for each glidepath, how many portfolios comply
#     month-by-month: CVaR_portfolio[t] <= CVaR_limit[t]
#   - Exports a summary Excel with % of compliant portfolios
#
#   How to run:
#   $ python -m glidecompare.main
#
#   Paths and filenames are set in config.py
# ===============================================================