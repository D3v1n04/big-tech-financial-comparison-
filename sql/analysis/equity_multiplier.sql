-- Equity Multiplier
WITH facts AS (
    SELECT
        ticker,
        fiscal_year,
        SUM(CASE WHEN metric_name = 'total_assets' THEN value_usd ELSE 0 END) AS ending_assets,
        SUM(CASE WHEN metric_name = 'stockholders_equity' THEN value_usd ELSE 0 END) AS ending_equity
    FROM financial_facts
    GROUP BY ticker, fiscal_year
),
previous_yr AS (
    SELECT
        ticker,
        fiscal_year,
        ending_assets,
        ending_equity,
        -- Last year's assets and equity
        LAG(ending_assets) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_assets,
        LAG(ending_equity) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_equity
    FROM facts
)
SELECT
    ticker,
    fiscal_year,
    -- Average assets
    ((ending_assets + prior_assets) / 2.0) AS average_total_assets,
    -- Average equity
    ((ending_equity + prior_equity) / 2.0) AS average_stockholders_equity,
    -- Equity Multiplier
    ROUND(
        ((ending_assets + prior_assets) / 2.0) /
        NULLIF(((ending_equity + prior_equity) /
        2.0), 0),2
    ) AS equity_multiplier
FROM previous_yr
WHERE fiscal_year BETWEEN 2021 AND 2025
ORDER BY ticker, fiscal_year;
