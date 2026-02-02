"""
Results Exporters
Defines paths and functions to export model results to Excel
"""

import os
import pandas as pd
import numpy as np
from formulas import calculate_years_contributed


class ResultsExporter:
    """
    Class to handle results export to Excel.
    Generates multiple sheets with different views of the data.
    """
    
    def __init__(self, parameters, simulator):
        """
        Initialize the exporter.
        
        Args:
            parameters: Instance of PensionParameters
            simulator: Instance of PensionSimulator
        """
        self.params = parameters
        self.sim = simulator
    
    def get_output_path(self, base_name="target_return"):
        """
        Build the output file path.
        
        Args:
            base_name (str): Base file name
        
        Returns:
            str: Full path of output file
        """
        # Relative path from 00_target_return to outputs
        output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Simple filename without timestamp
        filename = f"{base_name}.xlsx"
        
        return os.path.join(output_dir, filename)
    
    def calculate_profile_results(self):
        """
        Calculate results for the 4 analysis profiles.
        
        Returns:
            list: List of dictionaries with results by profile
        """
        # Define the 4 profiles
        profiles = [
            {'name': 'Male without gaps', 'is_male': True, 'with_gaps': False},
            {'name': 'Male with gaps', 'is_male': True, 'with_gaps': True},
            {'name': 'Female without gaps', 'is_male': False, 'with_gaps': False},
            {'name': 'Female with gaps', 'is_male': False, 'with_gaps': True},
        ]
        
        results = []
        
        print("Calculating required returns...")
        for profile in profiles:
            print(f"  Processing: {profile['name']}")
            
            # Search for required return
            req_return, achieved_rate, final_balance, pension = self.sim.search_target_return(
                profile['is_male'], profile['with_gaps']
            )
            
            # Get additional details with found return
            _, salaries_for_replacement, detail = self.sim.simulate_accumulation(
                profile['is_male'], profile['with_gaps'], req_return
            )
            average_salary = np.mean(salaries_for_replacement)
            
            # Calculate effective contribution years
            years_contributed = calculate_years_contributed(detail)
            
            # Get contribution density
            contribution_density = detail[0]['contribution_density'] if detail else 1.0
            
            # Determine label for average salary column
            months = self.params.months_for_replacement_rate
            if months == 12:
                salary_label = 'Average Salary Last 12 Months (UF)'
            elif months == 120:
                salary_label = 'Average Salary Last 10 Years (UF)'
            else:
                salary_label = f'Average Salary Last {months} Months (UF)'
            
            # Save results
            results.append({
                'Profile': profile['name'],
                'Contribution Density (%)': round(contribution_density * 100, 1),
                'Required Return (%)': round(req_return * 100, 2),
                'Achieved Replacement Rate (%)': round(achieved_rate * 100, 2),
                'Final Accumulated Balance (UF)': round(final_balance, 2),
                'Monthly Pension (UF)': round(pension, 2),
                salary_label: round(average_salary, 2),
                'Effective Contribution Years': round(years_contributed, 1),
                'profile_obj': profile  # For internal use
            })
        
        return results
    
    def generate_summary_sheet(self, results):
        """
        Generate DataFrame for summary sheet.
        
        Args:
            results (list): List of results by profile
        
        Returns:
            pd.DataFrame: DataFrame with results summary
        """
        # Remove internal use column
        df = pd.DataFrame(results)
        df = df.drop(columns=['profile_obj'])
        return df
    
    def generate_monthly_detail_sheets(self, results):
        """
        Generate DataFrames for monthly detail sheets of the 4 profiles.
        
        Args:
            results (list): List of results by profile
        
        Returns:
            list: List of tuples (profile_name, dataframe)
        """
        print("Generating monthly detail for the 4 profiles...")
        
        details = []
        
        for result in results:
            profile = result['profile_obj']
            
            # Get the profile's return
            req_return, _, _, _ = self.sim.search_target_return(
                profile['is_male'], profile['with_gaps']
            )
            
            # Simulate with that return
            _, _, detail = self.sim.simulate_accumulation(
                profile['is_male'], profile['with_gaps'], req_return
            )
            
            # Create DataFrame
            df = pd.DataFrame(detail)
            df['year'] = ((df['month'] - 1) // 12) + 1  # Adjusted so month 1 is in year 1
            df = df[['year', 'month', 'age', 'salary_uf', 'contribution_base_uf', 
                    'contribution_density', 'contribution_effective_uf', 'balance_uf']]
            
            # Save with profile name
            details.append((profile['name'], df))
        
        return details
    
    def generate_sensitivity_sheet(self, profiles):
        """
        Generate DataFrame for sensitivity analysis.
        
        Args:
            profiles (list): List of profiles to analyze
        
        Returns:
            pd.DataFrame: DataFrame with sensitivity analysis
        """
        print("Generating sensitivity analysis...")
        
        # Range of returns to test (0% to 15% in 1% increments)
        test_returns = np.arange(0, 0.16, 0.01)
        sensitivity_results = []
        
        for ret in test_returns:
            row = {'Return (%)': round(ret * 100, 2)}
            
            for profile in profiles:
                # Simulate with this return
                balance, salaries_for_replacement, _ = self.sim.simulate_accumulation(
                    profile['is_male'], profile['with_gaps'], ret
                )
                pension = self.sim.calculate_monthly_pension(balance, profile['is_male'])
                replacement_rate, _ = self.sim.calculate_replacement_rate(
                    pension, salaries_for_replacement
                )
                
                row[f"{profile['name']} - Replacement Rate (%)"] = round(replacement_rate * 100, 2)
            
            sensitivity_results.append(row)
        
        return pd.DataFrame(sensitivity_results)
    
    def generate_parameters_sheet(self):
        """
        Generate DataFrame with used parameters.
        
        Returns:
            pd.DataFrame: DataFrame with model parameters
        """
        params_dict = {
            'Parameter': [
                'Age start work male',
                'Age start work female',
                'Age retire male',
                'Age retire female',
                'Life expectancy male',
                'Life expectancy female',
                'Initial salary male (UF)',
                'Initial salary female (UF)',
                'Contribution rate',
                'Contribution ceiling (UF)',
                'Real annual salary growth',
                'Return post-retirement',
                'Target replacement rate',
                'Months for replacement rate calculation',
                'Contribution density male - no gaps',
                'Contribution density male - with gaps',
                'Contribution density female - no gaps',
                'Contribution density female - with gaps'
            ],
            'Value': [
                self.params.age_start_work_male,
                self.params.age_start_work_female,
                self.params.age_retire_male,
                self.params.age_retire_female,
                self.params.life_expectancy_male,
                self.params.life_expectancy_female,
                self.params.salary_initial_male,
                self.params.salary_initial_female,
                f"{self.params.contribution_rate * 100}%",
                self.params.contribution_ceiling,
                f"{self.params.salary_growth_real * 100}%",
                f"{self.params.return_post_retirement * 100}%",
                f"{self.params.replacement_rate_target * 100}%",
                self.params.months_for_replacement_rate,
                f"{self.params.contribution_density_male_no_gaps * 100}%",
                f"{self.params.contribution_density_male_with_gaps * 100}%",
                f"{self.params.contribution_density_female_no_gaps * 100}%",
                f"{self.params.contribution_density_female_with_gaps * 100}%"
            ]
        }
        
        return pd.DataFrame(params_dict)
    
    def export_results(self, filename=None):
        """
        Main function that generates Excel file with all results.
        
        Args:
            filename (str, optional): Filename. If None, uses default name
        
        Returns:
            str: Path of generated file
        """
        # Get output path
        if filename is None:
            output_path = self.get_output_path()
        else:
            output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
        
        # Calculate results for the 4 profiles
        results = self.calculate_profile_results()
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            
            # Sheet 1: Parameters
            df_parameters = self.generate_parameters_sheet()
            df_parameters.to_excel(writer, sheet_name='Parameters', index=False)
            
            # Sheet 2: Summary by profile
            df_summary = self.generate_summary_sheet(results)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Sheets 3-6: Monthly detail for each profile
            monthly_details = self.generate_monthly_detail_sheets(results)
            for profile_name, df_detail in monthly_details:
                # Use profile name directly (max 31 characters for Excel)
                sheet_name = profile_name.replace(' ', '_')[:31]
                df_detail.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Sheet 7: Sensitivity analysis
            profiles_for_sensitivity = [r['profile_obj'] for r in results]
            df_sensitivity = self.generate_sensitivity_sheet(profiles_for_sensitivity)
            df_sensitivity.to_excel(writer, sheet_name='Sensitivity Analysis', index=False)
        
        print(f"\nFile generated successfully: {output_path}")
        return output_path
