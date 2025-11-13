from itertools import product
import numpy as np
from config import (
    T_A_YEARS_VALUES, T_B_YEAR,)

from utils import grid_vals
from config import A_MIN, A_MAX, A_STEP, B_MIN, B_MAX, B_STEP

# Precompute A and B grids
A_VALUES = grid_vals(A_MIN, A_MAX, A_STEP)
B_VALUES = grid_vals(B_MIN, B_MAX, B_STEP)

def generate_param_grid(
    t_A_years_values = T_A_YEARS_VALUES,
    A_values = A_VALUES,
    B_values = B_VALUES,
    t_B_year: int = T_B_YEAR
):
    """
    Generate all admissible combinations (t_A, A, B, t_B) subject to:
      - A >= B
      - t_A < t_B

    Returns list of tuples: (t_A_y, t_A_m, t_B_y, t_B_m, A, B)
    """
    combos = []
    t_B_m = int(t_B_year) * 12
    for t_A_y, A, B in product(t_A_years_values, A_values, B_values):
        if (A >= B) and (t_A_y < t_B_year):
            t_A_m = int(t_A_y) * 12
            combos.append((int(t_A_y), int(t_A_m), int(t_B_year), int(t_B_m), float(A), float(B)))
    return combos
