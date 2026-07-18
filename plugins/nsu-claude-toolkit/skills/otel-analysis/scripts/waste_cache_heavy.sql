-- 出力トークンが小さいのにキャッシュ読込だけ膨らんでいるイベントを検出
SELECT
  attrs['model'] AS model,
  CAST(attrs['output_tokens'] AS INT) AS out_tok,
  CAST(attrs['cache_read_tokens'] AS INT) AS cache_read_tok,
  CAST(attrs['cost_usd'] AS DOUBLE) AS cost_usd,
  attrs['query_source'] AS query_source
FROM otel_raw
WHERE event_name = 'claude_code.api_request'
  AND CAST(attrs['output_tokens'] AS INT) < 50
  AND CAST(attrs['cache_read_tokens'] AS INT) > 50000
ORDER BY cache_read_tok DESC
LIMIT 30;
