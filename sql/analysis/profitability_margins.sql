-- Profitability Margins
SELECT
    ticker,
    fiscal_year,
    SUM(CASE WHEN metric_name = 'revenue' THEN value_usd ELSE 0 END) AS revenue_usd,
    SUM(CASE WHEN metric_name = 'operating_income' THEN value_usd ELSE 0 END) AS operating_income_usd,
    SUM(CASE WHEN metric_name = 'net_income' THEN value_usd ELSE 0 END) AS net_income_usd,

    -- Operating Margin
    ROUND(
        (
            SUM(CASE WHEN metric_name = 'operating_income' THEN value_usd ELSE 0 END) /
            NULLIF(SUM(CASE WHEN metric_name = 'revenue' THEN value_usd ELSE 0 END), 0)
        ) * 100, 2
    ) AS operating_margin_percentage,

    -- Net Profit Margin
    ROUND(
        (
            SUM(CASE WHEN metric_name = 'net_income' THEN value_usd ELSE 0 END) /
            NULLIF(SUM(CASE WHEN metric_name = 'revenue' THEN value_usd ELSE 0 END), 0)
        ) * 100,
        2
    ) AS net_profit_margin_percentage

FROM financial_facts
GROUP BY ticker, fiscal_year
ORDER BY ticker, fiscal_year;
