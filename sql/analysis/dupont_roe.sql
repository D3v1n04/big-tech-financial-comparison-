-- DuPont ROE
WITH facts AS (
    SELECT
        ticker,
        fiscal_year,
        SUM(CASE WHEN metric_name = 'revenue' THEN value_usd ELSE 0 END) AS revenue,
        SUM(CASE WHEN metric_name = 'net_income' THEN value_usd ELSE 0 END) AS net_income,
        SUM(CASE WHEN metric_name = 'total_assets' THEN value_usd ELSE 0 END) AS ending_assets,
        SUM(CASE WHEN metric_name = 'stockholders_equity' THEN value_usd ELSE 0 END) AS ending_equity
    FROM financial_facts
    GROUP BY ticker, fiscal_year
),
-- Last year's values
previous_yr AS (
    SELECT
        ticker,
        fiscal_year,
        revenue,
        net_income,
        ending_assets,
        ending_equity,
        -- Last year's assets and equity for the averages
        LAG(ending_assets) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_assets,
        LAG(ending_equity) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_equity
    FROM facts
)
SELECT
    ticker,
    fiscal_year,
    -- Net Profit Margin
    ROUND((net_income / NULLIF(revenue, 0)) * 100, 2) AS net_profit_margin,
    -- Asset Turnover
    ROUND(revenue / NULLIF(((ending_assets + prior_assets) / 2.0), 0), 2) AS asset_turnover,
    -- Equity Multiplier
    ROUND(((ending_assets + prior_assets) / 2.0) / NULLIF(((ending_equity + prior_equity) / 2.0), 0), 2) AS equity_multiplier,
    -- DuPont ROE
    ROUND(
        ((net_income / NULLIF(revenue, 0)) * 100) *
        (revenue / NULLIF(((ending_assets + prior_assets) / 2.0), 0)) *
        (((ending_assets + prior_assets) / 2.0) / NULLIF(((ending_equity + prior_equity) /
        2.0), 0)), 2
    ) AS dupont_roe_percentage,
    -- Direct ROE Check
    ROUND((net_income / NULLIF(((ending_equity + prior_equity) / 2.0), 0)) * 100, 2) AS direct_roe_percentage
FROM previous_yr
WHERE fiscal_year BETWEEN 2021 AND 2025
ORDER BY ticker, fiscal_year;
