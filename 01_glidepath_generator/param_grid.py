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
      - When A == B (flat glidepath), only generate one curve (with the first t_A)
        to avoid duplicates

    Returns list of tuples: (t_A_y, t_A_m, t_B_y, t_B_m, A, B)
    """
    combos = []
    t_B_m = int(t_B_year) * 12
    
    # Track which (A, B) pairs we've seen as flat glidepaths
    flat_pairs_seen = set()
    
    for t_A_y, A, B in product(t_A_years_values, A_values, B_values):
        if (A >= B) and (t_A_y < t_B_year):
            # If A == B, this is a flat glidepath
            if A == B:
                # Only add the first occurrence of this (A, B) pair
                if (A, B) not in flat_pairs_seen:
                    flat_pairs_seen.add((A, B))
                    t_A_m = int(t_A_y) * 12
                    combos.append((int(t_A_y), int(t_A_m), int(t_B_year), int(t_B_m), float(A), float(B)))
                # else: skip this duplicate flat glidepath
            else:
                # A > B: normal declining glidepath, always add
                t_A_m = int(t_A_y) * 12
                combos.append((int(t_A_y), int(t_A_m), int(t_B_year), int(t_B_m), float(A), float(B)))
    
    return combos
