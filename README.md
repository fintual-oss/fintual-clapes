# CVaR Glidepaths for Chilean Pension Reform

This repo stores code experiments related to a research collaboration between **Fintual** and **Clapes UC** investigating optimal portfolio glidepaths for target date funds under Chile's new pension investment regime.

The objective of our research is to develop a decaying maximum CVaR curve restriction framework that achieves minimum replacement rate requirements for Chilean pension funds.

---

## Repository Structure

The repo has four main parts, and each main folder includes a Word document with a more detailed explanation of the methodology used.

### 1. `portfolios/` — Portfolio Simulation
This module simulates random portfolios over a long horizon and computes their Conditional Value at Risk (CVaR).  
It uses historical returns, generates random weights each month (a "drunken manager" process), simulates asset returns with a multivariate normal distribution, and then calculates monthly CVaR values.  

- `main.py`: runs the full simulation and exports results to Excel (`Loop_drunken_portfolio_results.xlsx`).  
- Other scripts handle CVaR calculation, portfolio returns, random weights, covariance matrix adjustments, and file I/O.  
- **Methodology**: the folder includes a Word document that explains the portfolio simulation methodology in detail.

**Output:** CVaR by portfolio, month by month.

---

### 2. `cvar_glidepaths/` — Glidepath Generation
This module generates a full universe of CVaR glidepaths, which are piecewise linear curves describing the maximum risk (CVaR ceiling) allowed through the investor’s life cycle.  

- `main.py`: builds all glidepaths and saves them to Excel (`glidepaths_results.xlsx`).  
- `config.py`: defines ages (start at 35, retirement at 65), transition ages, and CVaR ranges (A and B).  
- Other scripts create the parameter grid, build the DataFrame of curves, and implement the piecewise function.  
- **Methodology**: the folder includes `Methodology_CVaR_Glidepaths.docx` with the theoretical explanation.

**Output:** a universe of admissible CVaR glidepaths.

---

### 3. `comparation/` — Glidepaths vs. Portfolios Comparison
This module compares the simulated portfolios with the glidepaths to check compliance.  
A portfolio is considered compliant if, in every month, its CVaR never exceeds the glidepath ceiling.  

- `main.py`: loads portfolio results and glidepaths, runs the comparison, and exports a summary (`glidepaths_vs_portfolios.xlsx`).  
- `loaders.py`: loads and reshapes data.  
- `logic.py`: implements the month-by-month comparison.  
- **Methodology**: the folder includes `Methodology.docx` describing the compliance rule.

**Output:** summary table with number and percentage of compliant portfolios for each glidepath.

---

### 4. `outputs/` — Results
This folder stores all output files created by the workflows:

- `Loop_drunken_portfolio_results.xlsx`: simulated portfolios and their monthly CVaR values.  
- `glidepaths_results.xlsx`: the full set of glidepaths generated.  
- `glidepaths_vs_portfolios.xlsx`: compliance results between portfolios and glidepaths.  

---

## How to run 

1. Simulate portfolios 
- python -m portfolios.main

2. Generate glidepaths
- python -m cvar_glidepaths.main

3. Compare glidepaths vs portfolios
- python -m comparation.main

