-- session.idと~/.claude/projects/配下のディレクトリ(session_id.jsonlの置き場所)を突き合わせてプロジェクト別に集計する
-- project列はディレクトリ名をそのまま出す(元のパスの"/"を"-"に置換したエンコード形式。逆変換はパス自体に"-"を含む場合に曖昧になるため行わない)
WITH session_project AS (
  SELECT
    regexp_extract(file, '/projects/([^/]+)/', 1) AS project,
    regexp_extract(file, '([^/]+)\.jsonl$', 1) AS session_id
  FROM glob('~/.claude/projects/*/*.jsonl') AS t(file)
)
SELECT
  sp.project AS project,
  count(*) AS 回数,
  round(sum(CAST(a.attrs['cost_usd'] AS DOUBLE)), 4) AS 合計コストUSD
FROM otel_raw a
JOIN session_project sp ON a.attrs['session.id'] = sp.session_id
WHERE a.event_name = 'claude_code.api_request'
GROUP BY 1
ORDER BY 3 DESC;
