-- event.timestampはUTC ISO8601なので、JSTに変換してから日付に丸める(UTCのまま丸めると日本時間の「今日」とズレる)
SELECT
  date_trunc('day', CAST(attrs['event.timestamp'] AS TIMESTAMPTZ) AT TIME ZONE 'Asia/Tokyo') AS 日付,
  count(*) AS 回数,
  round(sum(CAST(attrs['cost_usd'] AS DOUBLE)), 4) AS 合計コストUSD
FROM otel_raw
WHERE event_name = 'claude_code.api_request'
GROUP BY 1
ORDER BY 1 DESC;
