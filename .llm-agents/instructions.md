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

- 目的: Kaggle Titanic の仮説検証。Notebook を使わず Python スクリプトで分析する。フロントアプリは後続開発で技術未選定。
- 技術: Python 3.12.13、uv 0.12.16、pandas、scikit-learn。アプリ依存は `pyproject.toml` と uv が生成する `uv.lock` に記録し、共有スキル用 `.llm-agents/requirements.txt` と分ける。
- 構成: `scripts/` は実行コード、`configs/` は全パラメータ、`data/` は入力・派生データ、`runs/` は実行記録、`docs/` は検証結果と知見。データと runs の内容は Git 管理外。
- セットアップ: ルートで `uv sync --locked`。
- 動作確認: `uv run --locked python scripts/run_experiment.py --config configs/smoke.json --allow-dirty`。人工データの確認であり Titanic の分析ではない。
- 検証: `uv run --locked python -m unittest discover -s tests -v`、`uv run --locked ruff check scripts tests`、`uv run --locked ruff format --check scripts tests`。
- スクリプトは必ず実行基盤経由で動かし、全パラメータ・seed・全入力ファイルを設定に明示する。ログ、環境、Git、入力ハッシュ、分割、指標を記録する。正式な検証はコミット済みコードで行い、正の `--issue` 番号を必須とする。入力はリポジトリ内を指す相対パスに限定する。
- 仮説は Issue に登録し、1検証サイクルを `experiment/<issue番号>-<短い説明>` ブランチで扱う。複数 run は同じサイクルに含めてよい。
- 結果を `docs/experiments/` に、得られた知見へのリンクを `docs/insights.md` に残す。否定・判定不能も記録する。評価データのリークを防ぎ、比較する実験では同じ分割を使う。
- PR・push 時は `.github/workflows/checks.yml` で Ruff・テスト・Notebook の混入を確認する。Notebook を `.gitignore` で隠さない。
- 日本語のドキュメント・コメントでは句点「。」と読点「、」を使う。秘密情報を設定・ログ・Git に含めない。
- 詳細な記録仕様・再現手順は `docs/README.md` を参照する。
- スキルや `.llm-agents/scripts/` 変更時は、PyYAML のあるシステム Python（Dev Container は導入済み）で次も実行する。ホストでは共有スキル用に別の仮想環境を用意する。

  ```sh
  python3 -m unittest discover -s .llm-agents/tests
  python3 .llm-agents/scripts/register-skills.py --check
  ```
