-- waste_cache_heavy.sql に該当するイベントが全体コストに占める割合
SELECT
  sum(CASE WHEN CAST(attrs['output_tokens'] AS INT) < 50 AND CAST(attrs['cache_read_tokens'] AS INT) > 50000
      THEN CAST(attrs['cost_usd'] AS DOUBLE) ELSE 0 END) / sum(CAST(attrs['cost_usd'] AS DOUBLE)) AS 割合
FROM otel_raw
WHERE event_name = 'claude_code.api_request';
