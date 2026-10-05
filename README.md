# Big Tech Financial Comparison

## Capital Aggression vs. Structural Efficiency

A corporate finance and competitive intelligence analysis of Microsoft, Amazon, and Alphabet. This project evaluates whether escalating infrastructure investment is translating into sustainable revenue growth, profitability, capital efficiency, and free cash flow.

## Business Question

Which company is funding the cloud and AI infrastructure race most aggressively while maintaining the strongest company wide profitability, capital efficiency, and cash sustainability?

## Companies and Time Period

- Microsoft
- Amazon
- Alphabet

The analysis will compare reported fiscal years 2020 through 2025. Each company uses a different fiscal calendar, so all findings will identify the reported fiscal year and avoid treating fiscal years as identical calendar periods.

## Objectives

1. Extract audited annual financial data from SEC filings.
2. Build a traceable dataset where each metric can be linked to its original source filing.
3. Analyze revenue growth, infrastructure investment, profitability, free cash flow, and returns using PostgreSQL.
4. Apply the DuPont framework to explain how each company generates return on equity.
5. Identify major shifts in investment intensity and financial performance over time.
6. Present a data supported recommendation and key risks through Tableau.

## Core Metrics

### Investment and Growth

- Revenue
- Revenue growth
- Capital expenditures
- Capital expenditure growth
- Capital expenditures as a percentage of revenue
- Capital expenditures as a percentage of operating cash flow

### Profitability and Returns

- Operating income and operating margin
- Net income and net profit margin
- Total assets
- Total equity
- Return on assets
- Return on equity
- Asset turnover
- DuPont framework: net profit margin × asset turnover × equity multiplier

### Cash Sustainability

- Operating cash flow
- Free cash flow
- Free cash flow margin
- Capital expenditure coverage from operating cash flow

## Data Sources and Auditability

The project will use audited annual filings from the United States Securities and Exchange Commission.

For each extracted financial value, the dataset will retain:

- Company name and ticker
- Fiscal year
- SEC filing type and filing date
- Source filing link or identifier
- Original reported metric name
- Standardized project metric name
- Original value, unit, and cleaned value

This makes the analysis reproducible and allows every reported result to be traced back to an original filing.

## Methodology and Limitations

This is a company wide financial comparison. The project will use capital expenditure and cash flow metrics as indicators of infrastructure investment.

Cloud and AI segment disclosures are not fully comparable across Microsoft, Amazon, and Alphabet. Where segment data is used, the project will identify the disclosure difference instead of treating non equivalent measures as directly comparable.

The analysis will identify financial trends and risks, but it will not claim that capital spending alone caused a financial result or predict future performance with certainty.

## Technology Stack

- Python for SEC data extraction, cleaning, validation, and loading
- PostgreSQL for analytical data modeling and SQL analysis
- DBeaver for database development and query execution
- Tableau for executive dashboards and storytelling
- Ubuntu Linux, VS Code, Git, and GitHub for development and documentation

## Planned Deliverables

1. Auditable financial dataset for Microsoft, Amazon, and Alphabet
2. Python extraction and cleaning scripts
3. PostgreSQL table definitions, validation queries, and analytical SQL
4. Tableau executive storyboard with five pages:
   - Executive verdict
   - Capital investment race
   - Profitability and DuPont return engine
   - Cash sustainability
   - Methodology and source appendix
5. Short investment committee style memo with findings, recommendation, risks, and limitations

## Project Status

Phase 0: Project setup and scope definition in progress.
