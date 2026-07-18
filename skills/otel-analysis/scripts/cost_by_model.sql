SELECT
  attrs['model'] AS model,
  count(*) AS 回数,
  round(sum(CAST(attrs['cost_usd'] AS DOUBLE)), 4) AS 合計コストUSD
FROM otel_raw
WHERE event_name = 'claude_code.api_request'
GROUP BY 1
ORDER BY 3 DESC;
