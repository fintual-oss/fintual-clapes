import os.path as op

# Repo root = one level above this package folder
BASE_DIR = op.dirname(op.dirname(op.abspath(__file__)))

# Input files (produced by your other pipelines)
# - LOOP_FILE: Excel with sheet 'cvar_by_portfolio'
#   columns: Portfolio, m001..m360 (wide format)
# - GLIDES_FILE: Excel from cvar_glidepaths (sheet like a big table)
LOOP_FILE   = op.join(BASE_DIR, "outputs", "portfolio_cvar_series.xlsx")
GLIDES_FILE = op.join(BASE_DIR, "outputs", "glidepaths_universe.xlsx")

# Output file
OUT_DIR  = op.join(BASE_DIR, "outputs")
OUT_FILE = op.join(OUT_DIR, "glidepaths_vs_portfolios.xlsx")

# Names/labels used in the workflow
LOOP_SHEET_NAME   = "cvar_by_portfolio"
SUMMARY_SHEETNAME = "summary"
