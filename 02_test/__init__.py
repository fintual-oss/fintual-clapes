# ===============================================================
#   Portfolio Diversity Analyzer
#   
#   Analyzes the diversity of portfolios generated in step 02.
#   
#   For each CVaR glidepath curve:
#     - Re-generates portfolios using the SAME seeds as step 02
#     - Extracts portfolio weights (not saved in step 02)
#     - Calculates diversity metrics:
#       * Mean weights per asset (month by month)
#       * Standard deviation, range, percentiles
#       * Concentration metrics (HHI, Entropy, N_effective)
#     - Exports to Excel (one file per curve)
#   
#   How to run:
#   $ python -m 00_test.main
#   
#   Configuration:
#   - Edit config.py to select curves and number of portfolios
#   - IMPORTANT: Seeds must match those used in step 02
# ===============================================================
