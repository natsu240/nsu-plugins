# nsu-plugins

個人用Claude Code設定(plugin: hooks/skills + dotfiles: settings.json/statusline.py)を配布するrepo。詳細は README.md 参照。

## Gitワークフロー

- **直コミットでOK**。個人リポジトリなのでブランチ・PRは不要、`main`に直接コミットする。
- **コミットしたら必ずGitHub Tagリリースを切る。** コミットして終わりにしない。手順:
  1. 該当プラグインの `plugins/<plugin-name>/.claude-plugin/plugin.json` の `version` をsemverで更新する(機能追加・修正内容に応じてpatch/minorを判断。破壊的変更はmajor)
  2. コミットを作成する(version bumpも同じコミットに含めてよい)
  3. `claude plugin tag --push` を該当プラグインディレクトリ(`plugins/<plugin-name>/`)から実行してタグを作成・push([公式CLI](https://code.claude.com/docs/en/plugin-dependencies#tag-plugin-releases-for-version-resolution)。tag名は`plugin.json`の`name`と`version`から自動導出され、`{plugin-name}--v{version}`形式になる。plugin.jsonとmarketplace.jsonのversion不一致・作業ツリーの汚れ・タグ重複は自動でエラーになる)
  4. `gh release create <tag名> --generate-notes`(tag名は手順3の出力に表示される。例: `nsu-claude-toolkit--v1.0.0`)

複数プラグインをこのrepoに追加した場合、プラグインごとに独立してバージョン管理・タグ付けする(`plugins/<name>/`ディレクトリ単位で`claude plugin tag`を実行)。

`git tag`を手で打たないこと。バージョン解決の対象になるタグ命名規則(`{plugin-name}--v{version}`)を守るため必ず`claude plugin tag`を使う。

## 構成メモ

- `.claude-plugin/marketplace.json` — マーケットプレイス定義(name: `nsu-plugins`、リポジトリ名と一致させている)。`owner`は`name`のみ、各pluginエントリは`name`/`description`/`source`のみの最小構成。
- `plugins/<plugin-name>/` — 各プラグイン本体。直下に`.claude-plugin/plugin.json`を置き、`agents/` `hooks/` `skills/` 等はそのプラグインディレクトリの中に置く(新しいプラグインを追加するときも同じ形にする)
- `dotfiles/` はプラグインの仕組みでは配布できない`settings.json`/`statusline.py`。`install.sh`で`~/.claude/`へ反映する。
