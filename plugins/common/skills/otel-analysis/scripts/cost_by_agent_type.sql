-- query_source='agent:custom'/'agent:builtin:*'の実体を、同じprompt.idを持つ
-- claude_code.subagent_completedイベントのagent_type(プラグイン/スキル/組み込みエージェント名)と突き合わせて特定する
SELECT
  s.attrs['agent_type'] AS agent_type,
  s.attrs['is_built_in'] AS is_built_in,
  count(*) AS 回数,
  round(sum(CAST(a.attrs['cost_usd'] AS DOUBLE)), 4) AS 合計コストUSD
FROM otel_raw a
JOIN otel_raw s
  ON a.attrs['prompt.id'] = s.attrs['prompt.id']
  AND s.event_name = 'claude_code.subagent_completed'
WHERE a.event_name = 'claude_code.api_request'
  AND a.attrs['query_source'] LIKE 'agent:%'
GROUP BY 1, 2
ORDER BY 4 DESC;
