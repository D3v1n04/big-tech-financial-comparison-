-- Compute performance metrics for each company across multiple years
CREATE OR REPLACE VIEW vw_company_performance_metrics AS
WITH prior_year AS (
    SELECT
        ticker,
        fiscal_year,
        revenue,
        net_income,
        operating_cash_flow,
        capital_expenditures,
        total_assets,
        stockholders_equity,
        LAG(revenue) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_year_revenue,
        LAG(capital_expenditures) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_year_capex,
        LAG(total_assets) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_year_assets,
        LAG(stockholders_equity) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_year_equity
    FROM vw_company_year_financials
),
company_metrics AS (
    SELECT
        ticker,
        fiscal_year,
        revenue,
        net_income,
        operating_cash_flow,
        capital_expenditures,
        total_assets,
        stockholders_equity,

        -- CapEx YoY Growth %
        ((capital_expenditures - prior_year_capex) / NULLIF(prior_year_capex, 0)) * 100 AS capex_yoy_growth_pct,

        -- Revenue YoY Growth %
        ((revenue - prior_year_revenue) / NULLIF(prior_year_revenue, 0)) * 100 AS revenue_yoy_growth_pct,

        -- Capital Intensity %
        (capital_expenditures / NULLIF(revenue, 0)) * 100 AS capital_intensity_pct,

        -- Free Cash Flow in Dollars
        (operating_cash_flow - capital_expenditures) AS free_cash_flow_usd,

        -- FCF Margin %
        ((operating_cash_flow - capital_expenditures) / NULLIF(revenue, 0)) * 100 AS free_cash_flow_margin_pct,

        -- Direct ROE %
        (net_income / NULLIF(((stockholders_equity + prior_year_equity) / 2.0), 0)) * 100 AS direct_roe_pct
    FROM prior_year
)
SELECT
    ticker,
    fiscal_year,
    revenue,
    net_income,
    operating_cash_flow,
    capital_expenditures,
    total_assets,
    stockholders_equity,
    capex_yoy_growth_pct,
    revenue_yoy_growth_pct,
    capital_intensity_pct,
    free_cash_flow_usd,
    free_cash_flow_margin_pct,
    direct_roe_pct
FROM company_metrics
WHERE fiscal_year BETWEEN 2021 AND 2025;


SELECT *
FROM vw_company_performance_metrics
ORDER BY ticker, fiscal_year;
