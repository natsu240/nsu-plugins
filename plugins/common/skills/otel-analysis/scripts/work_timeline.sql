-- 作業内容の振り返り: user_promptの本文を時系列(JST)で一覧する
-- 注意: promptカラムには入力した指示文がそのまま入るため、機密情報を含む可能性がある。表示前に内容を確認すること
SELECT
  CAST(attrs['event.timestamp'] AS TIMESTAMPTZ) AT TIME ZONE 'Asia/Tokyo' AS 時刻JST,
  attrs['session.id'] AS session_id,
  left(attrs['prompt'], 80) AS prompt_head
FROM otel_raw
WHERE event_name = 'claude_code.user_prompt'
ORDER BY 1 DESC
LIMIT 50;
