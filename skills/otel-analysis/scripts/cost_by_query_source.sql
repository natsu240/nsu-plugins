SELECT
  attrs['query_source'] AS query_source,
  count(*) AS 回数,
  round(sum(CAST(attrs['cost_usd'] AS DOUBLE)), 4) AS 合計コストUSD
FROM otel_raw
WHERE event_name = 'claude_code.api_request'
GROUP BY query_source
ORDER BY 合計コストUSD DESC;
