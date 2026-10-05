-- Asset Turnover
WITH facts AS (
    SELECT
        ticker,
        fiscal_year,
        SUM(CASE WHEN metric_name = 'revenue' THEN value_usd ELSE 0 END) AS revenue,
        SUM(CASE WHEN metric_name = 'total_assets' THEN value_usd ELSE 0 END) AS ending_assets
    FROM financial_facts
    GROUP BY ticker, fiscal_year
),
previous_yr AS (
    SELECT
        ticker,
        fiscal_year,
        revenue,
        ending_assets,
        LAG(ending_assets) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_assets
    FROM facts
)
SELECT
    ticker,
    fiscal_year,
    revenue,
    ending_assets,
    prior_assets,

    -- Average assets
    ((ending_assets + prior_assets) / 2.0) AS average_assets,

    -- Turnover
    ROUND(
        revenue / NULLIF(((ending_assets + prior_assets) / 2.0), 0),
        2
    ) AS asset_turnover
FROM previous_yr
WHERE fiscal_year BETWEEN 2021 AND 2025
ORDER BY ticker, fiscal_year;
