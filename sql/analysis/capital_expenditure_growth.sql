-- Capital expenditure growth percentage
WITH capex AS (
    SELECT
        ticker,
        fiscal_year,
        value_usd AS capex_usd,
        LAG(value_usd) OVER (PARTITION BY ticker ORDER BY fiscal_year) AS prev_year_capex
    FROM financial_facts
    WHERE metric_name = 'capital_expenditures'
)
SELECT
    ticker,
    fiscal_year,
    capex_usd,
    prev_year_capex,
    ROUND((capex_usd - prev_year_capex) / prev_year_capex * 100, 2) AS capex_growth_percentage
FROM capex
WHERE fiscal_year BETWEEN 2021 AND 2025
ORDER BY ticker, fiscal_year;


-- Capital intensity
SELECT
    ticker,
    fiscal_year,
    SUM(CASE WHEN metric_name = 'capital_expenditures' THEN value_usd ELSE 0 END) AS capex_usd,
    SUM(CASE WHEN metric_name = 'revenue' THEN value_usd ELSE 0 END) AS revenue_usd,
    ROUND(
        (
        SUM(CASE WHEN metric_name = 'capital_expenditures' THEN value_usd ELSE 0 END) /
        NULLIF(SUM(CASE WHEN metric_name = 'revenue' THEN value_usd ELSE 0 END), 0)
        ) * 100,2
    ) AS capital_intensity_percentage
FROM financial_facts
GROUP BY ticker, fiscal_year
ORDER BY ticker, fiscal_year;
