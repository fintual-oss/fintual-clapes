"""
Pension Model Parameters
All monetary values are expressed in UF (Unidad de Fomento - Chilean inflation-indexed unit)
"""


class PensionParameters:
    """
    Class to store all parameters for the pension simulation model.
    
    Monetary values in UF:
    - Salaries are in UF to avoid inflation effects
    - Contribution ceiling is in UF (official Chilean system value)
    - Results will also be in UF
    """
    
    def __init__(self):
        # ========================================
        # DEMOGRAPHIC PARAMETERS
        # ========================================
        self.age_start_work_male = 25     # Age when men start working
        self.age_start_work_female = 25   # Age when women start working
        self.age_retire_male = 60         # Legal retirement age for men
        self.age_retire_female = 60       # Legal retirement age for women
        self.life_expectancy_male = 90    # Life expectancy for men
        self.life_expectancy_female = 90  # Life expectancy for women
        
        # ========================================
        # ECONOMIC PARAMETERS (IN UF)
        # ========================================
        self.salary_initial_male = 20.0    # Initial salary for men in UF
        self.salary_initial_female = 20.0  # Initial salary for women in UF
        self.contribution_rate = 0.16      # Mandatory contribution rate (16%)
        self.contribution_ceiling = 87.8   # Contribution ceiling in UF (official value)
        self.salary_growth_real = 0.0125   # Real annual salary growth (1.25% per OECD)
        
        # ========================================
        # RETURN PARAMETERS
        # ========================================
        # Return during accumulation phase: this parameter will be found via binary search
        # Return after retirement (real, above UF inflation)
        self.return_post_retirement = 0.032  # 2.5% real (equivalent to UF+2.5%)
        
        # ========================================
        # TARGET PARAMETERS
        # ========================================
        self.replacement_rate_target = 0.63  # Target replacement rate (63%)
        
        # Number of months to average for replacement rate calculation
        # Options: 12 (last year) or 120 (last 10 years)
        self.months_for_replacement_rate = 120  # 12 or 120 months
        
        # ========================================
        # CONTRIBUTION DENSITY
        # ========================================
        # Contribution density: percentage of months with contributions
        # 1.0 = contributes every month (100%)
        # 0.583 = contributes 58.3% of the time (simulates gaps)
        
        # Contribution density for men
        self.contribution_density_male_no_gaps = 1.0    # 100% - no gaps
        self.contribution_density_male_with_gaps = 0.98  # 58.3% - with gaps
        
        # Contribution density for women
        self.contribution_density_female_no_gaps = 1.0   # 100% - no gaps
        self.contribution_density_female_with_gaps = 0.99 # 49.6% - with gaps
        
        # ========================================
        # BINARY SEARCH PARAMETERS
        # ========================================
        self.return_min = 0.0      # Minimum return for search (0%)
        self.return_max = 0.20     # Maximum return for search (20%)
        self.tolerance = 0.0001    # Tolerance for convergence
        self.max_iterations = 100  # Maximum iterations in binary search
    
    def __repr__(self):
        """String representation of parameters"""
        return (
            f"PensionParameters(\n"
            f"  Age start work M/F: {self.age_start_work_male}/{self.age_start_work_female}\n"
            f"  Age retire M/F: {self.age_retire_male}/{self.age_retire_female}\n"
            f"  Life expectancy M/F: {self.life_expectancy_male}/{self.life_expectancy_female}\n"
            f"  Initial salary M/F: {self.salary_initial_male}/{self.salary_initial_female} UF\n"
            f"  Contribution rate: {self.contribution_rate*100}%\n"
            f"  Contribution ceiling: {self.contribution_ceiling} UF\n"
            f"  Real salary growth: {self.salary_growth_real*100}%\n"
            f"  Target replacement rate: {self.replacement_rate_target*100}%\n"
            f"  Months for replacement rate: {self.months_for_replacement_rate}\n"
            f"  Contribution density M (no gaps/gaps): {self.contribution_density_male_no_gaps}/{self.contribution_density_male_with_gaps}\n"
            f"  Contribution density F (no gaps/gaps): {self.contribution_density_female_no_gaps}/{self.contribution_density_female_with_gaps}\n"
            f")"
        )
