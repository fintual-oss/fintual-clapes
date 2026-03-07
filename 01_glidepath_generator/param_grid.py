from itertools import product
import numpy as np
from config import (
    T_A_YEARS_VALUES, T_B_YEAR, FLAT_LEVELS)

from utils import grid_vals
from config import A_MIN, A_MAX, A_STEP, B_MIN, B_MAX, B_STEP

# Precompute A and B grids for declining glidepaths
A_VALUES = grid_vals(A_MIN, A_MAX, A_STEP)
B_VALUES = grid_vals(B_MIN, B_MAX, B_STEP)

def generate_param_grid(
    t_A_years_values = T_A_YEARS_VALUES,
    A_values = A_VALUES,
    B_values = B_VALUES,
    flat_levels = FLAT_LEVELS,
    t_B_year: int = T_B_YEAR
):
    """
    Generate all admissible combinations (t_A, A, B, t_B) for:
    1. Declining glidepaths: A > B (all combinations of t_A x A x B where A > B)
    2. Flat glidepaths: A = B (one curve per level in flat_levels)

    Returns list of tuples: (t_A_y, t_A_m, t_B_y, t_B_m, A, B)
    """
    combos = []
    t_B_m = int(t_B_year) * 12
    
    # ============================================================
    # Part 1: Generate DECLINING glidepaths (A > B)
    # ============================================================
    for t_A_y, A, B in product(t_A_years_values, A_values, B_values):
        if (A > B) and (t_A_y < t_B_year):
            t_A_m = int(t_A_y) * 12
            combos.append((int(t_A_y), int(t_A_m), int(t_B_year), int(t_B_m), float(A), float(B)))
    
    # ============================================================
    # Part 2: Generate FLAT glidepaths (A = B)
    # ============================================================
    # For flat glidepaths, t_A doesn't matter (no transition), so we use the first t_A value
    if flat_levels and len(t_A_years_values) > 0:
        t_A_first = t_A_years_values[0]
        t_A_first_m = int(t_A_first) * 12
        
        for level in flat_levels:
            if t_A_first < t_B_year:
                combos.append((int(t_A_first), int(t_A_first_m), int(t_B_year), int(t_B_m), float(level), float(level)))
    
    return combos
