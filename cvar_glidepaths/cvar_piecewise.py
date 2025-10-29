def cvar_piecewise_months(age_m: int, t_A_m: int, t_B_m: int, A: float, B: float) -> float:
    """
    Piecewise definition of the max CVaR path at a given age in months:
    - If age_m <= t_A_m: CVaR = A
    - If t_A_m < age_m <= t_B_m: linear transition A -> B
    - If age_m  > t_B_m: CVaR = B
    """
    if age_m <= t_A_m:
        return A
    elif age_m <= t_B_m:
        slope = (B - A) / (t_B_m - t_A_m)
        return A + slope * (age_m - t_A_m)
    else:
        return B
