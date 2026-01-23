"""
Pension Model Formulas and Simulation Logic
Contains all mathematical functions and life cycle pension simulation
"""

import numpy as np


class PensionSimulator:
    """
    Main class to simulate the pension life cycle.
    Handles fund accumulation, pension calculation, and target return search.
    """
    
    def __init__(self, parameters):
        """
        Initialize the simulator with model parameters.
        
        Args:
            parameters: Instance of PensionParameters with model configuration
        """
        self.params = parameters
    
    def simulate_accumulation(self, is_male, with_gaps, annual_return):
        """
        Simulate the accumulation phase from start of work until retirement.
        
        Process:
        1. Simulate month by month the work cycle
        2. Apply contributions (respecting contribution ceiling)
        3. Apply contribution density (percentage of actual contributions)
        4. Apply returns to accumulated fund
        5. Adjust salary annually according to real growth
        
        Args:
            is_male (bool): True if male, False if female
            with_gaps (bool): True if reduced contribution density (gaps)
            annual_return (float): Annual real return during accumulation
        
        Returns:
            tuple: (final_balance, list_salaries_last_12_months, monthly_detail)
                - final_balance (float): Accumulated balance in UF at retirement
                - salaries_last_12_months (list): List of monthly salaries of last 12 months in UF
                - monthly_detail (list): List of dictionaries with month-by-month information
        """
        # Determine parameters by gender
        age_start = (self.params.age_start_work_male if is_male 
                    else self.params.age_start_work_female)
        age_retirement = (self.params.age_retire_male if is_male 
                         else self.params.age_retire_female)
        salary_initial = (self.params.salary_initial_male if is_male
                         else self.params.salary_initial_female)
        
        # Determine contribution density
        if with_gaps:
            contribution_density = (self.params.contribution_density_male_with_gaps if is_male 
                                   else self.params.contribution_density_female_with_gaps)
        else:
            contribution_density = (self.params.contribution_density_male_no_gaps if is_male 
                                   else self.params.contribution_density_female_no_gaps)
        
        # Calculate total months to simulate
        total_months = (age_retirement - age_start) * 12
        
        # Simulation variables
        balance = 0.0
        salary_current = salary_initial
        monthly_return = (1 + annual_return) ** (1/12) - 1
        
        # Lists to store information
        detail = []
        salaries_last_12_months = []
        
        # Month-by-month simulation
        for month in range(total_months):
            age_current = age_start + (month / 12)
            
            # Salary growth: at the start of each year
            if month > 0 and month % 12 == 0:
                salary_current *= (1 + self.params.salary_growth_real)
            
            # Calculate contribution for the month
            salary_taxable = min(salary_current, self.params.contribution_ceiling)
            contribution_base = salary_taxable * self.params.contribution_rate
            contribution = contribution_base * contribution_density  # Apply density
            balance += contribution
            
            # Apply return to accumulated balance
            balance *= (1 + monthly_return)
            
            # Save salaries from last 12 months (last year before retirement)
            months_to_retirement = total_months - month
            if months_to_retirement <= 12:
                salaries_last_12_months.append(salary_current)
            
            # Save monthly detail
            detail.append({
                'month': month + 1,
                'age': round(age_current, 2),
                'salary_uf': round(salary_current, 4),
                'contribution_base_uf': round(contribution_base, 4),
                'contribution_density': contribution_density,
                'contribution_effective_uf': round(contribution, 4),
                'balance_uf': round(balance, 2)
            })
        
        return balance, salaries_last_12_months, detail
    
    def calculate_monthly_pension(self, accumulated_balance, is_male):
        """
        Calculate monthly pension using annuity formula.
        
        The fund is depleted exactly at the end of life expectancy (Option A).
        Uses the present value of annuity formula:
        
        Pension = Balance * [r(1+r)^n] / [(1+r)^n - 1]
        
        Where:
        - r = monthly return
        - n = number of retirement months
        
        Args:
            accumulated_balance (float): Accumulated balance in UF at retirement
            is_male (bool): True if male, False if female
        
        Returns:
            float: Monthly pension in UF
        """
        # Determine parameters by gender
        age_retirement = (self.params.age_retire_male if is_male 
                         else self.params.age_retire_female)
        life_expectancy = (self.params.life_expectancy_male if is_male 
                          else self.params.life_expectancy_female)
        
        # Calculate retirement months
        retirement_months = (life_expectancy - age_retirement) * 12
        
        # Convert annual return to monthly
        monthly_return = (1 + self.params.return_post_retirement) ** (1/12) - 1
        
        # Apply annuity formula
        if monthly_return > 0:
            numerator_factor = monthly_return * (1 + monthly_return) ** retirement_months
            denominator_factor = (1 + monthly_return) ** retirement_months - 1
            pension = accumulated_balance * (numerator_factor / denominator_factor)
        else:
            # If return is 0, simply divide the balance
            pension = accumulated_balance / retirement_months
        
        return pension
    
    def calculate_replacement_rate(self, pension, salaries_last_12_months):
        """
        Calculate the replacement rate as the ratio between pension and the average
        of salaries from the last 12 months.
        
        Replacement Rate = Pension / Average(Salaries last 12 months)
        
        Args:
            pension (float): Monthly pension in UF
            salaries_last_12_months (list): List of monthly salaries from last 12 months in UF
        
        Returns:
            tuple: (replacement_rate, average_salary)
                - replacement_rate (float): Pension/salary ratio
                - average_salary (float): Average of salaries from last 12 months in UF
        """
        average_salary = np.mean(salaries_last_12_months)
        replacement_rate = pension / average_salary
        return replacement_rate, average_salary
    
    def search_target_return(self, is_male, with_gaps):
        """
        Use binary search to find the return that achieves the target replacement rate.
        
        Algorithm:
        1. Start with interval [return_min, return_max]
        2. Calculate replacement rate with median return
        3. Adjust interval depending on whether we are above or below target
        4. Repeat until convergence or maximum iterations reached
        
        Args:
            is_male (bool): True if male, False if female
            with_gaps (bool): True if has contribution gaps
        
        Returns:
            tuple: (required_return, achieved_replacement_rate, final_balance, monthly_pension)
                - required_return (float): Required annual return
                - achieved_replacement_rate (float): Replacement rate achieved
                - final_balance (float): Accumulated balance in UF
                - monthly_pension (float): Monthly pension in UF
        """
        return_min = self.params.return_min
        return_max = self.params.return_max
        
        iteration = 0
        while iteration < self.params.max_iterations:
            # Calculate median return of interval
            return_median = (return_min + return_max) / 2
            
            # Simulate with median return
            balance, salaries_12_months, _ = self.simulate_accumulation(
                is_male, with_gaps, return_median
            )
            pension = self.calculate_monthly_pension(balance, is_male)
            replacement_rate, _ = self.calculate_replacement_rate(pension, salaries_12_months)
            
            # Check convergence
            difference = abs(replacement_rate - self.params.replacement_rate_target)
            if difference < self.params.tolerance:
                return return_median, replacement_rate, balance, pension
            
            # Adjust interval according to result
            if replacement_rate < self.params.replacement_rate_target:
                # We need higher return
                return_min = return_median
            else:
                # We need lower return
                return_max = return_median
            
            iteration += 1
        
        # If it doesn't converge, return best approximation
        return return_median, replacement_rate, balance, pension


def calculate_years_contributed(monthly_detail):
    """
    Calculate the number of effective contribution years from monthly detail.
    
    With the new model using contribution density, this is simply:
    total_months * contribution_density / 12
    
    Args:
        monthly_detail (list): List of dictionaries with month-by-month information
    
    Returns:
        float: Years of effective contributions
    """
    if not monthly_detail:
        return 0.0
    
    # Get contribution density (should be the same for all months)
    contribution_density = monthly_detail[0]['contribution_density']
    total_months = len(monthly_detail)
    
    years_contributed = (total_months * contribution_density) / 12
    return years_contributed
