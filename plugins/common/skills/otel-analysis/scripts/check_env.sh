#!/bin/bash
set -euo pipefail

if ! command -v duckdb >/dev/null 2>&1; then
  curl -fsSL https://install.duckdb.org | sh
fi

if ls ~/.claude/otel/output/logs*.jsonl >/dev/null 2>&1; then
  LOG_GLOB="~/.claude/otel/output/logs*.jsonl"
elif ls ~/.claude/otel/logs*.jsonl >/dev/null 2>&1; then
  LOG_GLOB="~/.claude/otel/logs*.jsonl"
else
  echo "ERROR: OTelログファイルが見つからない (~/.claude/otel/output/ 、 ~/.claude/otel/ のどちらにも logs*.jsonl が無い)" >&2
  exit 1
fi

if ! grep -q "CREATE OR REPLACE VIEW otel_raw" ~/.duckdbrc 2>/dev/null; then
  cat > ~/.duckdbrc <<EOF
CREATE OR REPLACE VIEW otel_raw AS
WITH records AS (
  SELECT UNNEST(resourceLogs).scopeLogs AS scopeLogs
  FROM read_ndjson('$LOG_GLOB', ignore_errors=true)
),
scoped AS (
  SELECT UNNEST(scopeLogs).logRecords AS logRecords FROM records
),
flat AS (
  SELECT UNNEST(logRecords) AS rec FROM scoped
)
SELECT
  rec.body.stringvalue AS event_name,
  map_from_entries(
    list_transform(rec.attributes, x -> {
      'key': x.key,
      'value': COALESCE(x.value.stringvalue, CAST(x.value.intvalue AS VARCHAR), CAST(x.value.doublevalue AS VARCHAR), CAST(x.value.boolvalue AS VARCHAR))
    })
  ) AS attrs
FROM flat;
EOF
  echo "~/.duckdbrc に otel_raw view を作成しました (log path: $LOG_GLOB)"
else
  echo "OK: duckdb / otel_raw view は準備済み"
fi
