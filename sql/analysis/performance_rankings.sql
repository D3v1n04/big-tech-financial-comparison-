-- Scorecard
WITH company_year AS (
    SELECT
        ticker,
        fiscal_year,
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
    GROUP BY ticker, fiscal_year
),
prior_year AS (
    SELECT
        ticker,
        fiscal_year,
        revenue,
        net_income,
        operating_cash_flow,
        capital_expenditures,
        total_assets,
        stockholders_equity,
        -- Last year's values
        LAG(revenue) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_year_revenue,
        LAG(capital_expenditures) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_year_capex,
        LAG(total_assets) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_year_assets,
        LAG(stockholders_equity) OVER(PARTITION BY ticker ORDER BY fiscal_year) AS prior_year_equity
    FROM company_year
),
company_metrics AS (
    SELECT
        ticker,
        fiscal_year,
        -- CapEx Year Over Year Growth %
        ((capital_expenditures - prior_year_capex) / NULLIF(prior_year_capex, 0)) * 100 AS capex_yoy_growth_pct,
        -- Revenue Year Over Year Growth %
        ((revenue - prior_year_revenue) / NULLIF(prior_year_revenue, 0)) * 100 AS revenue_yoy_growth_pct,
        -- Capital Intensity %
        (capital_expenditures / NULLIF(revenue, 0)) * 100 AS capital_intensity_pct,
        -- Cash Flow
        (operating_cash_flow - capital_expenditures) AS free_cash_flow_usd,
        -- Cash Flow Margin %
        ((operating_cash_flow - capital_expenditures) / NULLIF(revenue, 0)) * 100 AS free_cash_flow_margin_pct,
        -- Direct ROE %
        (net_income / NULLIF(((stockholders_equity + prior_year_equity) / 2.0), 0)) * 100 AS direct_roe_pct
    FROM prior_year
),
latest_year AS (
    SELECT *
    FROM company_metrics
    WHERE fiscal_year = 2025
),
ranked_companies AS (
    SELECT
        *,
        -- Rankings
        RANK() OVER (ORDER BY direct_roe_pct DESC) AS direct_roe_rank,
        RANK() OVER (ORDER BY free_cash_flow_margin_pct DESC) AS free_cash_flow_margin_rank,
        RANK() OVER (ORDER BY revenue_yoy_growth_pct DESC) AS revenue_growth_rank,
        RANK() OVER (ORDER BY capital_intensity_pct ASC) AS capital_intensity_rank
    FROM latest_year
),
scored_companies AS (
    SELECT
        *,
        -- Combined Overall Score (Lower is better)
        (
            direct_roe_rank
            + free_cash_flow_margin_rank
            + revenue_growth_rank
            + capital_intensity_rank
        ) AS overall_score
    FROM ranked_companies
)
SELECT
    ticker,
    fiscal_year,
    -- Metrics
    ROUND(capex_yoy_growth_pct, 2) AS capex_yoy_growth_pct,
    ROUND(revenue_yoy_growth_pct, 2) AS revenue_yoy_growth_pct,
    ROUND(capital_intensity_pct, 2) AS capital_intensity_pct,
    free_cash_flow_usd,
    ROUND(free_cash_flow_margin_pct, 2) AS free_cash_flow_margin_pct,
    ROUND(direct_roe_pct, 2) AS direct_roe_pct,
    -- Rankings
    direct_roe_rank,
    free_cash_flow_margin_rank,
    revenue_growth_rank,
    capital_intensity_rank,
    -- Score Summary
    overall_score,
    -- Leaderboard Rank
    RANK() OVER (ORDER BY overall_score ASC) AS overall_rank
FROM scored_companies
ORDER BY overall_rank ASC;
