SELECT
    ticker,
    metric_name
FROM financial_facts
GROUP BY ticker, metric_name
HAVING COUNT(DISTINCT fiscal_year) != 6;