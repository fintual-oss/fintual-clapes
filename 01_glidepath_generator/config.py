# Central place for main configuration values

# Ages (years)
T_START_YEARS = 25          # starting age
T_END_YEARS   = 60          # retirement age
# Transition end age t_B (years). If t_B == 65, the path is flat at retirement.
T_B_YEAR = 60

# Derived (months)
T_START_MONTHS = T_START_YEARS * 12
T_END_MONTHS   = T_END_YEARS * 12

# Total months in the horizon
MONTHS = T_END_MONTHS - T_START_MONTHS  

# Transition start age t_A (years). — full range 40..50
T_A_YEARS_VALUES = list(range(35, 51))

# Independent ranges for A and B (CVaR caps)
A_MIN, A_MAX, A_STEP = 0.05, 0.10, 0.01
B_MIN, B_MAX, B_STEP = 0.03, 0.03, 0.01

# Output filename (Excel)
OUTPUT_XLSX = "glidepaths_universe.xlsx"
