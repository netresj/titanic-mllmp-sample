# 共通プロンプト

このファイルは Claude Code、Codex、GitHub Copilot が共有する作業手順です。必須事項はルートの [AGENTS.md](../AGENTS.md) に従ってください。

## 共有スキルの利用

- [共有スキル一覧](README.md#共有スキル一覧) を確認し、依頼に関連するスキルがある場合は、その `SKILL.md` を読んで手順を適用する。

## トークン使用量の削減

- Dev Container 内では `rtk`（Rust Token Killer）、`rg`（ripgrep）、`jq` を利用できる。コンテナ外では利用可能か確認する。
- 対応するコマンドの出力を確認する際は、`rtk git status`、`rtk git diff`、`rtk git log -5` など、`rtk` 経由の実行を優先する。対応状況は `rtk --help` や各サブコマンドのヘルプで確認する。
- 圧縮で必要な情報が省略された場合や正確な原文が必要な場合は、元のコマンドで対象を絞って確認する。未対応のコマンドは通常どおり実行する。
- ファイル検索には `rg --files`、本文検索には対象パスを指定した `rg -n` を使い、必要な範囲だけを読む。JSON は `jq` で必要な項目を取り出す。
- 削減量を確認する場合は `rtk gain` を利用する。表示される値は RTK の推定値であり、サービスの請求額とは区別する。

## プロジェクト固有の情報

雛形を利用する際に、以下をプロジェクトに合わせて書き換えてください。現在の内容はこのテンプレートリポジトリ自体のものです。

- 目的・対象範囲: Claude Code、Codex、GitHub Copilot で共通の指示とスキルを共有するためのテンプレート。アプリケーションのコードは含まない。
- 使用言語・フレームワーク: Python 3。標準ライブラリと PyYAML のみを使う。
- セットアップコマンド: `python3 -m venv .venv` の後に `.venv/bin/python -m pip install -r .llm-agents/requirements.txt`。Dev Container には導入済みのため不要。
- ビルド・テスト・静的解析コマンド: スキルまたは `.llm-agents/scripts/` を変更した場合は、リポジトリのルートで下記を実行する。ビルドと静的解析は未設定。

  ```sh
  python3 -m unittest discover -s .llm-agents/tests
  python3 .llm-agents/scripts/register-skills.py --check
  ```

- コーディング規約: ドキュメントとコメントは日本語とし、句点は `。`、読点は `、` を使う。Python は標準ライブラリを優先し、依存を追加する場合は `.llm-agents/requirements.txt` に明記する。
