# nsu-plugins

個人用のClaude Code設定一式。プラグインとして配布できる部分(hooks/skills)と、settings.json由来でプラグインの仕組みでは配れない個人設定(dotfiles)を1つのrepoにまとめている。

## 構成

```
.
├── .claude-plugin/
│   └── marketplace.json           # マーケットプレイス定義(name/owner/plugins一覧)
├── plugins/
│   └── nsu-claude-toolkit/        # プラグイン本体(複数プラグインを置く場合はここに追加していく)
│       ├── .claude-plugin/
│       │   └── plugin.json        # プラグインのマニフェスト
│       ├── hooks/
│       │   ├── hooks.json         # general-purposeサブエージェントをブロックするhook設定
│       │   └── scripts/
│       │       └── block-general-purpose.py
│       └── skills/
│           └── otel-analysis/     # Claude Code自身のOTelログ(コスト/トークン)をDuckDBで分析するスキル
├── dotfiles/                       # プラグインでは配布できない個人設定
│   ├── settings.json               # ~/.claude/settings.json にマージする内容
│   └── statusline.py               # ~/.claude/statusline.py
└── install.sh                       # dotfiles/ を ~/.claude/ に反映するスクリプト
```

**なぜ分かれているか**: Claude Codeのプラグインはskills/agents/hooks/MCP/LSP/output-styles/themes/monitors/binに加えて、プラグイン直下に`settings.json`を置いて既定値を配ることもできる。ただし現状そこで指定できるのは`agent`(デフォルトサブエージェント)と`subagentStatusLine`の2キーのみで、env変数・`permissions`・メインの`statusLine`・テーマなどは対象外([公式リファレンス](https://code.claude.com/docs/en/plugins-reference#file-locations-reference)参照)。そのため今回のenv変数・`permissions.defaultMode`・メインの`statusLine`・テーマ等は`dotfiles/` + `install.sh` で別途`~/.claude/settings.json`に反映する。

## 入れ方

### 1. プラグイン部分(hooks / skills)

Claude Code内で:

```
/plugin marketplace add natsu240/nsu-plugins
/plugin install nsu-claude-toolkit@nsu-plugins
```

ローカルで試す場合はパスを直接指定してもよい: `/plugin marketplace add /path/to/nsu-plugins`

### 2. dotfiles部分(settings.json / statusline.py)

```bash
./install.sh
```

- `~/.claude/statusline.py` を上書き
- `~/.claude/settings.json` に `dotfiles/settings.json` の内容をディープマージ(既存ファイルは自動でバックアップ)

**注意**: `dotfiles/settings.json` には `permissions.defaultMode: "bypassPermissions"` と `skipDangerousModePermissionPrompt: true` が含まれる。権限確認プロンプトを全て自動許可する設定なので、意図しない環境に適用する場合は該当2項目を削除してから使うこと。

**hookの二重登録に注意**: プラグイン(hooks.json)とマージ後の既存`settings.json`の両方に`block-general-purpose.py`を叩く設定が残っていると、同じhookが2回実行される(実害はないが冗長)。プラグインを`/plugin install`した後は、`~/.claude/settings.json`の`hooks`エントリを手動で削除してよい。

## otel-analysisスキルについて

`~/.claude/otel/` 配下にOTel Collector(docker-compose)経由でログが出力されている前提で動く。Collector自体のセットアップ(collector-config.yaml・docker-compose.yml)はこのrepoには含めていない。参考: [Claude CodeにOTelログを導入して、トークン消費・コストを可視化する](https://zenn.dev/nakashimaharuto/articles/claude-code-otel-logging-guide)

## ライセンス

MIT
