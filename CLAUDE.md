# nsu-plugins

個人用Claude Code設定(plugin: hooks/skills + dotfiles: settings.json/statusline.py)を配布するrepo。詳細は README.md 参照。

## Gitワークフロー

- **直コミットでOK**。個人リポジトリなのでブランチ・PRは不要、`main`に直接コミットする。
- **コミットしたら必ずGitHub Tagリリースを切る。** コミットして終わりにしない。手順:
  1. `.claude-plugin/plugin.json` の `version` をsemverで更新する(機能追加・修正内容に応じてpatch/minorを判断。破壊的変更はmajor)
  2. コミットを作成する
  3. `git tag vX.Y.Z`(plugin.jsonのversionと一致させる)
  4. `git push origin main --tags`
  5. `gh release create vX.Y.Z --generate-notes`

version bumpとtagは同じコミットに含めてよい(plugin.jsonの変更もそのコミットに含める)。

## 構成メモ

- `.claude-plugin/plugin.json` — plugin本体のマニフェスト(name: `nsu-claude-toolkit`)
- `.claude-plugin/marketplace.json` — マーケットプレイス定義(name: `nsu-plugins`、リポジトリ名と一致させている)
- `dotfiles/` はプラグインの仕組みでは配布できない`settings.json`/`statusline.py`。`install.sh`で`~/.claude/`へ反映する。
