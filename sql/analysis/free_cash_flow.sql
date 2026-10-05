-- Cash Flow
WITH facts AS (
    SELECT
        ticker,
        fiscal_year,
        SUM(CASE WHEN metric_name = 'operating_cash_flow' THEN value_usd ELSE 0 END) AS operating_cash_flow,
        SUM(CASE WHEN metric_name = 'capital_expenditures' THEN value_usd ELSE 0 END) AS capex,
        SUM(CASE WHEN metric_name = 'revenue' THEN value_usd ELSE 0 END) AS revenue
    FROM financial_facts
    GROUP BY ticker, fiscal_year
),
flow AS (
    SELECT
        ticker,
        fiscal_year,
        operating_cash_flow,
        capex,
        revenue,
        -- Cash Flow dollar amount
        (operating_cash_flow - capex) AS free_cash_flow_usd
    FROM facts
)
SELECT
    ticker,
    fiscal_year,
    operating_cash_flow,
    capex,
    free_cash_flow_usd,
    revenue,
    -- Cash Flow Margin Percentage
    ROUND(
        (free_cash_flow_usd /
        NULLIF(revenue, 0))
        * 100, 2
    ) AS free_cash_flow_margin_percentage
FROM flow
WHERE fiscal_year BETWEEN 2021 AND 2025
ORDER BY ticker, fiscal_year;
