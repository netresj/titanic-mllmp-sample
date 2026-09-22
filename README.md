# Titanic Analysis

Kaggle Titanic の仮説を Python スクリプトで検証するプロジェクトです。Notebook は使用しません。実験の設定・ログ・環境・結果を保存し、Issue、検証ブランチ、知見を結び付けます。

## 現在の範囲

実験の記録基盤、人工データでの動作確認、仮説・結果のテンプレートを用意しています。Titanic の前処理・学習・提出ファイル生成と、可視化するフロントアプリは後続開発です。フロントの技術は未選定です。

## 技術と構成

Python 3.12.13、uv 0.12.16、pandas、scikit-learn を使用し、依存を `uv.lock` に固定します。記録は JSON とログファイルで保存します。

```text
configs/                 # Git 管理する実験設定
scripts/                 # 実行基盤・分析用 Python スクリプト
tests/                   # 実験基盤の検証
data/raw/                # 手動配置する原本（Git 管理外）
data/processed/          # 派生データ（Git 管理外）
runs/<run-id>/           # 実験ログ・環境・結果（Git 管理外）
docs/experiments/        # 仮説検証ごとの結果
docs/insights.md         # 知見の索引
.github/ISSUE_TEMPLATE/  # 仮説の登録様式
.devcontainer/          # 開発環境・プロキシ
.llm-agents/             # 共通指示・共有スキル
```

## セットアップと実行

[開発環境の手順](.devcontainer/README.md) に従い `Dev Containers: Rebuild Container` を実行してください。作成時に共有スキル登録と `uv sync --locked` を実行します。

ホストの場合は uv 0.12.16 を用意し、以下をリポジトリルートで実行します。Python は `.python-version` に従って uv が用意します。

ホストとコンテナの `.venv` は共用できません。別環境で作った `.venv` が残っている場合は、Git 管理外の `.llm-agents/tmp/` などに退避してから同期してください。

```sh
uv sync --locked
uv run --locked python scripts/run_experiment.py --config configs/smoke.json --allow-dirty
uv run --locked python -m unittest discover -s tests -v
uv run --locked ruff check scripts tests
uv run --locked ruff format --check scripts tests
```

動作確認には Kaggle データも認証情報も不要です。表示された `runs/<run-id>/run.log` に実行中から標準出力・標準エラーを保存します。`tail -f runs/<run-id>/run.log` で確認できます。指標は人工データの結果であり、Titanic の性能ではありません。

データは Kaggle から自身で取得し、`data/raw/train.csv`、`data/raw/test.csv` に配置します。データ取得・提出は自動化していません。原本は上書きせず保管してください。

## 仮説検証の進め方

1. Issue の「仮説検証」で、仮説・根拠・評価方法・判定基準を登録します。
2. 1サイクルにつき `experiment/<issue番号>-<短い説明>` ブランチを作ります。同じサイクル内で複数回実験できます。
3. スクリプトと設定を作成し、入力一覧・seed・全パラメータを明示してコミットします。
4. `uv run --locked python scripts/run_experiment.py --config configs/<設定>.json --issue <番号>` で実行します。
5. [結果テンプレート](docs/experiments/_template.md) を `docs/experiments/<issue番号>-<短い説明>.md` にコピーし、結果・解釈・限界を記録します。[知見の索引](docs/insights.md) も更新します。
6. PR に Issue と結果文書を関連付け、レビュー後にマージします。次の仮説は新しい Issue・ブランチに分けます。

成果物は Git 管理外です。共有・長期保存する run ディレクトリと入力データは別途保管し、文書に保存先を記載します。

記録形式・再現方法は [実験基盤の説明](docs/README.md)、共通ルールは [AGENTS.md](AGENTS.md)、エージェント設定は [.llm-agents/README.md](.llm-agents/README.md) を参照してください。依存の同期方法は [uv 公式資料](https://docs.astral.sh/uv/concepts/projects/sync/) に基づきます。

## CI

PR と push 時に `.github/workflows/checks.yml` が依存の同期、Ruff、実験基盤のテスト、Git 管理された Notebook の混入確認を実行します。CI 設定は [uv の公式ガイド](https://docs.astral.sh/uv/guides/integration/github/) を参照しています。
