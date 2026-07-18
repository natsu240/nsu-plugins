# nsu-plugins

個人用Claude Code設定(plugin: hooks/skills + dotfiles: settings.json/statusline.py)を配布するrepo。詳細は README.md 参照。

## Gitワークフロー

- **直コミットでOK**。個人リポジトリなのでブランチ・PRは不要、`main`に直接コミットする。
- **コミット→push→タグ→リリースは常に1セット。都度ユーザーに確認を取らず自動でやる。** `plugins/<name>/`配下に変更が入るコミットなら、表記修正のような軽微な変更でも必ずversion bump・タグ・リリースまで実行する。「これもバージョン上げますか?」のように聞き返さないこと。手順:
  1. 該当プラグインの `plugins/<plugin-name>/.claude-plugin/plugin.json` の `version` をsemverで更新する(機能追加・修正内容に応じてpatch/minorを判断。破壊的変更はmajor)
  2. コミットを作成する(version bumpも同じコミットに含めてよい)
  3. `git push origin main` でmainブランチ自体をpushする(`claude plugin tag --push`はタグしかpushしないので、これを飛ばすとタグ・Releaseだけ進んでmainが取り残される)
  4. `claude plugin tag --push` を該当プラグインディレクトリ(`plugins/<plugin-name>/`)から実行してタグを作成・push
  5. `gh release create <tag名> --generate-notes`(tag名は手順4の出力に表示される。例: `common--v1.1.0`)

複数プラグインをこのrepoに追加した場合、プラグインごとに独立してバージョン管理・タグ付けする(`plugins/<name>/`ディレクトリ単位で`claude plugin tag`を実行)。

`git tag`を手で打たないこと。バージョン解決の対象になるタグ命名規則(`{plugin-name}--v{version}`)を守るため必ず`claude plugin tag`を使う。

## 構成メモ

- `.claude-plugin/marketplace.json` — マーケットプレイス定義(name: `nsu-plugins`、リポジトリ名と一致させている)。`owner`は`name`のみ、各pluginエントリは`name`/`description`/`source`のみの最小構成。
- `plugins/<plugin-name>/` — 各プラグイン本体。直下に`.claude-plugin/plugin.json`を置き、`agents/` `hooks/` `skills/` 等はそのプラグインディレクトリの中に置く(新しいプラグインを追加するときも同じ形にする)
- `dotfiles/` はプラグインの仕組みでは配布できない`settings.json`/`statusline.py`。`install.sh`で`~/.claude/`へ反映する。

## `claude plugin` コマンドのノウハウ

このrepoのプラグインを操作するときは基本`claude plugin <サブコマンド>`を使う。`marketplace`だけさらに1段サブコマンドを持つ(`claude plugin marketplace <サブコマンド>`)。

**開発中の検証**

```bash
claude plugin validate . [--strict]   # plugin.json/marketplace.jsonの構文・スキーマ検証。--strictで警告もエラー扱い
claude plugin eval [target]           # evals/**/case.yaml等でプラグインの挙動をテスト(未整備なら使わない)
```

**マーケットプレイス管理**

```bash
claude plugin marketplace add ~/code/nsu-plugins     # ローカルパスから追加
claude plugin marketplace add natsu240/nsu-plugins   # GitHub owner/repo形式でも可(--sparseでモノレポの一部だけcheckout可)
claude plugin marketplace list
claude plugin marketplace update [name]               # 省略で全マーケットプレイス更新
claude plugin marketplace remove <name>
```

**インストール・有効化**

```bash
claude plugin install common@nsu-plugins [--scope user|project|local] [--config key=value]
claude plugin update common@nsu-plugins    # 再インストール後、反映にはセッション再起動が必要
claude plugin enable / disable common@nsu-plugins
claude plugin uninstall common@nsu-plugins [--prune] [--keep-data]
```

**確認**

```bash
claude plugin list [--json] [--available]
claude plugin details common@nsu-plugins   # コンポーネント一覧+トークンコスト概算
```

**リリース**(上のGitワークフロー参照)

```bash
cd plugins/<plugin-name>
claude plugin tag [--dry-run] [--push] [-f|--force] [-m "メッセージ(%sがversionに置換される)"] [--remote origin]
```

**注意点**

- ローカルの`plugin-dev`スキル付属リファレンスなど二次資料は古い/簡略化されている場合があるので、迷ったら`claude plugin validate`と`claude --help`系で実機確認する(公式ドキュメントは https://code.claude.com/docs/en/plugins-reference )
- `install`/`uninstall`のような、ユーザーの実環境(`~/.claude/`)に副作用が出る操作は、実行前に必ず確認を取る。検証目的で入れたら検証後にちゃんと`uninstall`すること
- `claude plugin update`は完了メッセージが出ても即座には反映されない。次のセッション再起動が要る
