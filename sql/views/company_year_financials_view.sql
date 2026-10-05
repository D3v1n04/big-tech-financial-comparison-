-- View for Company Year Financial Data
CREATE OR REPLACE VIEW vw_company_year_financials AS
SELECT
    ticker,
    fiscal_year,
    -- Financial Metrics
    SUM(CASE WHEN metric_name = 'revenue' THEN value_usd ELSE 0 END) AS revenue,
    SUM(CASE WHEN metric_name = 'net_income' THEN value_usd ELSE 0 END) AS net_income,
    SUM(CASE WHEN metric_name = 'operating_cash_flow' THEN value_usd ELSE 0 END) AS operating_cash_flow,
    SUM(CASE WHEN metric_name = 'capital_expenditures' THEN value_usd ELSE 0 END) AS capital_expenditures,
    SUM(CASE WHEN metric_name = 'total_assets' THEN value_usd ELSE 0 END) AS total_assets,
    SUM(CASE WHEN metric_name = 'stockholders_equity' THEN value_usd ELSE 0 END) AS stockholders_equity
FROM financial_facts
-- Filter for specific metrics
WHERE metric_name IN (
    'revenue',
    'net_income',
    'operating_cash_flow',
    'capital_expenditures',
    'total_assets',
    'stockholders_equity'
)
AND fiscal_year BETWEEN 2020 AND 2025
GROUP BY ticker, fiscal_year;


SELECT *
FROM vw_company_year_financials
ORDER BY ticker, fiscal_year;