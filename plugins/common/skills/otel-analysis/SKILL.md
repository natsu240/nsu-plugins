---
name: otel-analysis
description: "~/.claude/otel/配下に溜まったClaude CodeのOTelテレメトリログ(JSONL)をDuckDBで分析する。query_source別・モデル別・日別・セッション別のコスト/トークン内訳集計や、無駄パターン検知(出力小なのにキャッシュ読込だけ膨大、想定外のサブエージェント自動起動)を行う。「レートの消費内訳見せて」「今月何にトークン使った」「コストの内訳」「何が高くついてるか調べて」等、Claude Code自身の利用量・コストログを分析したいときに使う。"
allowed-tools: Bash
context: fork
---

# OTelログ分析

`~/.claude/otel/`配下に溜まったClaude CodeのOTelログ(JSONL)を、DuckDBでその場でクエリして分析する。DuckDBは常駐コンテナではないので、集計したいときにだけコマンドとして叩けばいい。

生のクエリ結果を全部そのまま返さず、要約・insight込みで報告すること。

## 前提確認(毎回軽くでOK)

```bash
bash ~/.claude/skills/otel-analysis/scripts/check_env.sh
```

duckdbが無ければインストールし、`~/.duckdbrc`に`otel_raw`viewが無ければ(見つかったログパスに合わせて)作成する。ログパスは環境によって`~/.claude/otel/output/logs.jsonl`か`~/.claude/otel/logs.jsonl`のどちらか(compose.yamlのvolumeマウント先次第)。

## スキーマ知識(クエリを組み立てる時の参考)

全イベント共通の属性(`attrs['...']`で取れる): `user.id`, `session.id`, `organization.id`, `user.email`, `terminal.type`, `event.timestamp`(UTC ISO8601), `prompt.id`(ターンごとのID)

### 主なイベント種別 (`event_name`)

| イベント名 | 内容 |
|---|---|
| `claude_code.api_request` | APIコール1回ごとのメタデータ。`model`, `input_tokens`, `output_tokens`, `cache_read_tokens`, `cost_usd`, `query_source` |
| `claude_code.assistant_response` | アシスタント応答の本文(詳細ログ有効時のみ) |
| `claude_code.api_request_body` / `claude_code.api_response_body` | APIリクエスト/レスポンスの生ボディ(詳細ログ有効時のみ) |
| `claude_code.tool_result` | ツール実行結果の種類とサイズ(バイト数) |
| `claude_code.hook_execution_start` / `claude_code.hook_execution_complete` | hookの実行状況 |
| `claude_code.subagent_completed` | サブエージェント(Agentツール経由)の完了 |

### `query_source`(どこから呼ばれたか)の実際の値

| 実際の値 | 分類 | 意味 |
|---|---|---|
| `repl_main_thread` | main | メインの会話そのもの |
| `agent:custom` | subagent | プラグインやスキルが起動したサブエージェント |
| `agent:builtin:<名前>` | subagent | 組み込みの汎用サブエージェント |
| `compact` / `generate_session_title` / `prompt_suggestion` / `web_fetch_apply` / `web_search_tool` / `sdk` | auxiliary | 会話本体を補助する裏方の処理 |

### Traces(`traces.jsonl`、`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`有効時のみ)

`otel_raw`と同じ要領で`traces*.jsonl`をUNNESTすれば読める。span種別:

- `claude_code.interaction`: プロンプト1回分の最上位span
- `claude_code.llm_request`: Claudeへの問い合わせ1回。`model`, 入出力トークン数, `duration_ms`, `ttft_ms`(最初の応答までの時間), `agent_id`/`parent_agent_id`
- `claude_code.tool`: ツール呼び出し1回。同じく`agent_id`/`parent_agent_id`
- `claude_code.tool.blocked_on_user`: ユーザー許可待ち時間のみ
- `claude_code.tool.execution`: 実行時間のみ
- `claude_code.hook`: hookの実行

## 集計クエリ(リクエスト内容に応じて選ぶ)

各スクリプトは `duckdb < ~/.claude/skills/otel-analysis/scripts/<ファイル名>` でそのまま実行できる。

| リクエスト例 | 実行するスクリプト |
|---|---|
| 「レートの消費内訳/コスト内訳見せて」(デフォルト) | `scripts/cost_by_query_source.sql` |
| モデル別に見たい | `scripts/cost_by_model.sql` |
| 日別の推移が見たい | `scripts/cost_by_day.sql` |
| セッション別に見たい | `scripts/cost_by_session.sql` |
| プロジェクト別に見たい(`session.id`を`~/.claude/projects/`のディレクトリと突き合わせる) | `scripts/cost_by_project.sql` |
| 無駄検知①: 出力小・キャッシュ読込大のイベントを探す(記事の実例: 出力10〜30トークンなのにcache_read_tokensが8万〜10万) | `scripts/waste_cache_heavy.sql` → 該当が多ければ `scripts/waste_cache_heavy_ratio.sql` で全体に占める割合も出す |
| 無駄検知②: 特定のquery_source(プラグイン等)が想定外に多く呼ばれていないか | `scripts/cost_by_query_source.sql` の回数列を見て、`agent:custom`等が想定より多い/コストが高いプラグインが会話ターンのたびに裏で追加API呼び出しをしていないか疑う(記事の「セキュリティプラグインが原因だったケース」と同じパターン) |
| `agent:custom`/`agent:builtin:*`の中身(具体的にどのプラグイン・スキル・組み込みエージェントが起動したか)を特定したい | `scripts/cost_by_agent_type.sql`(`prompt.id`で`claude_code.subagent_completed`と突き合わせ、`agent_type`列で実体を特定する) |
| 作業内容を振り返りたい(いつ何を頼んだか) | `scripts/work_timeline.sql`(`claude_code.user_prompt`の本文を時系列表示。指示文がそのまま出るので機密情報の混入に注意) |
| 作業パターンを振り返りたい(どのツールをどれだけ/どのくらいの時間/どのくらいの失敗率で使っているか) | `scripts/tool_usage_pattern.sql` |

上記でカバーできないリクエストは、スキーマ知識セクションを参考にその場でSQLを組み立てて`duckdb -c "..."`で実行する。

## 結果の見せ方

- 表はそのままターミナル出力(duckdbのデフォルト整形)で十分。件数が多い場合はLIMITを使う。
- 数値だけでなく、「このパターンは無駄っぽい」と気づいたら記事の2例のように具体的な原因(キャッシュ再読込・特定プラグインの自動起動など)まで踏み込んで指摘する。
