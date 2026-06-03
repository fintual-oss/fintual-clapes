# ===============================================================
#   01_glidepath_generator — CVaR Glidepath Universe Generator
#
#   Generates all possible CVaR glidepath curves and exports
#   them to a single Excel file for use in step 02.
#
#   A CVaR glidepath defines the maximum allowed risk (CVaR)
#   at each month of the investment horizon. It has three phases:
#     1. Constant high-risk phase (before t_A)
#     2. Linear transition from A to B (between t_A and t_B)
#     3. Constant low-risk phase (after t_B)
#
#   Configuration:
#   - Edit config.py to set ages, CVaR ranges, and output filename
#   - Key parameters to adjust per gender profile:
#       T_END_YEARS / T_B_YEAR = 65 for men, 60 for women
#
#   How to run:
#   $ python -m 01_glidepath_generator.main
#
#   Output:
#   - outputs/glidepaths_universe.xlsx
#     One column per glidepath curve, rows = parameters + monthly CVaR values
#
# ===============================================================
