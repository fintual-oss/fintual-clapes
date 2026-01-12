"""
Main - Entry point for the pension model
Runs the complete model and generates results in Excel
"""

from parameters import PensionParameters
from formulas import PensionSimulator
from exporters import ResultsExporter


def main():
    """
    Main function to execute the pension simulation model.
    
    Process:
    1. Load model parameters
    2. Create pension simulator
    3. Calculate required returns for each profile
    4. Generate Excel file with results
    """
    
    print("=" * 70)
    print("CHILEAN PENSION SYSTEM SIMULATION MODEL")
    print("Fintual-Clapes Team")
    print("=" * 70)
    print()
    
    # 1. Initialize parameters
    print("Loading model parameters...")
    parameters = PensionParameters()
    print(f"  Parameters loaded")
    print(f"  - Initial salary M/F: {parameters.salary_initial_male}/{parameters.salary_initial_female} UF")
    print(f"  - Contribution ceiling: {parameters.contribution_ceiling} UF")
    print(f"  - Target replacement rate: {parameters.replacement_rate_target*100}%")
    print()
    
    # 2. Create simulator
    print("Initializing simulator...")
    simulator = PensionSimulator(parameters)
    print("  Simulator initialized")
    print()
    
    # 3. Create exporter
    print("Preparing results exporter...")
    exporter = ResultsExporter(parameters, simulator)
    print("  Exporter ready")
    print()
    
    # 4. Run simulation and export results
    print("Running simulations and generating results...")
    print("-" * 70)
    generated_file = exporter.export_results()
    print("-" * 70)
    print()
    
    print("=" * 70)
    print("PROCESS COMPLETED SUCCESSFULLY")
    print(f"Results saved in: {generated_file}")
    print("=" * 70)
    print()
    print("NEXT STEP:")
    print("Use the 'Required Return (%)' values from the Summary sheet")
    print("to calibrate TARGET_RETURN_THRESHOLD in step 03_trajectory_analyzer")
    print()


if __name__ == "__main__":
    main()
