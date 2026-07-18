-- 作業パターンの振り返り: ツール別の利用頻度・平均所要時間・失敗率
SELECT
  attrs['tool_name'] AS tool,
  count(*) AS 回数,
  round(avg(CAST(attrs['duration_ms'] AS DOUBLE)), 1) AS 平均ms,
  sum(CASE WHEN attrs['success'] = 'false' THEN 1 ELSE 0 END) AS 失敗数
FROM otel_raw
WHERE event_name = 'claude_code.tool_result'
GROUP BY 1
ORDER BY 2 DESC;
