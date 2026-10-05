-- Revenue Growth
WITH facts AS (
    SELECT
        ticker,
        fiscal_year,
        SUM(CASE WHEN metric_name = 'revenue' THEN value_usd ELSE 0 END) AS revenue_usd
    FROM financial_facts
    GROUP BY ticker, fiscal_year
),
previous_yr AS (
    SELECT
        ticker,
        fiscal_year,
        revenue_usd,
        -- Last year's revenue
        LAG(revenue_usd) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_year_revenue
    FROM facts
)
SELECT
    ticker,
    fiscal_year,
    revenue_usd,
    prior_year_revenue,
    -- Revenue Growth Percentage
    ROUND(
        ((revenue_usd - prior_year_revenue) /
        NULLIF(prior_year_revenue, 0)) *
        100, 2
    ) AS revenue_growth_percentage
FROM previous_yr
WHERE fiscal_year BETWEEN 2021 AND 2025
ORDER BY ticker, fiscal_year;
