# ===============================================================
#   04_full_pool_analyzer — Full Pool Scenario Analyzer
#
#   Final module of the pipeline. Reads the annualized return
#   results from module 03 and aggregates them into a single
#   Excel file with one row per glidepath curve.
#
#   Instead of averaging across seeds or portfolios first, this
#   module treats the entire (N_SEEDS x N_PORTFOLIOS) matrix as
#   a single pool and computes all statistics directly on the
#   full matrix, without any intermediate averaging step.
#
#   Pipeline (per curve):
#     1. Load annualized returns matrix: (N_SEEDS x N_PORTFOLIOS)
#     2. Compute statistics directly on the full matrix
#        (numpy operates over all elements without flattening,
#        which is equivalent but more memory efficient)
#     3. Compute pct_above for each TARGET_RETURN_THRESHOLD
#        over the full matrix
#
#   Output:
#     outputs/analysis_full_pool/analysis_full_pool.xlsx
#       Single sheet, one row per curve.
#       Columns: curve params + statistics + pct_above_X% thresholds
#
#   How to run:
#   $ python -m 04_full_pool_analyzer.main
#
#   Configuration:
#   - Edit TARGET_RETURN_THRESHOLDS in main.py (use values from module 00)
#   - Edit PERCENTILES, SORT_BY, OUTPUT_LABEL as needed
#
# ===============================================================
