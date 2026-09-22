# 実験と知見の管理

`experiments/` にサイクルごとの結果を保存し、`insights.md` から参照します。否定された仮説や判定不能の結果も残します。

## 記録形式（schema_version: 1）

各実行は `runs/<UTC時刻>-<ランダムID>/` に保存されます。将来の画面は `run.json` を入口にし、`schema_version` と `status` を確認して読む想定です。

| ファイル | 内容 |
| --- | --- |
| `run.json` | ID、Issue、開始・終了日時、状態、終了コード、Git コミット・ブランチ・変更状態、コマンド、成果物一覧 |
| `config.original.json` / `config.json` | 元の設定と解析済みの設定 |
| `environment.json` | uv、Python、OS、CPU アーキテクチャ、導入パッケージ、スレッド数 |
| `inputs.json` | 入力のパス・サイズ・SHA-256 |
| `source/` / `source.json` | scripts/**/*.py（サブディレクトリを含む）、依存定義・ロック・Python バージョンのコピーとハッシュ |
| `run.log` | 標準出力・標準エラーと実行基盤のエラー |
| `metrics.json` | 評価指標（JSON オブジェクト） |
| その他 | 分割情報、予測など実験固有の成果物 |

状態は `running`、`completed`、`failed`、`interrupted` です。準備中の失敗では一部ファイルがありません。強制終了・電源断では `running` が残る可能性があるため完了扱いにしません。強制終了直前のバッファやディスク障害まで保存を保証しません。

## 分析スクリプトの契約

- `scripts/` に置き、`--config <JSON>` と `--output-dir <ディレクトリ>` を受け取ります。
- 設定には `script`、`seed`（0以上2**32未満）、`inputs`（リポジトリ内を指すルート基準の相対パス一覧。絶対パス・リポジトリ外への参照は拒否）、`parameters` を必ず含めます。使う全パラメータを明示し、暗黙の既定値を避けます。
- ライブラリ・モデル・データ分割に seed を渡します。基盤側では `PYTHONHASHSEED` と主要な数値計算のスレッド数を固定します。
- 使う入力を `inputs` に全件列挙します。基盤が開始前のハッシュを保存します。実行中に入力やコードを変更しないでください。
- 進捗・処理内容・警告を標準出力／標準エラーへ出し、`metrics.json` と成果物を保存します。秘密情報をログや設定に含めません。
- 評価データを学習や前処理の fit に使わず、分割行 ID と評価手順を残します。比較実験は同じ分割で行います。

## 再現手順

1. `run.json` のコミットを別の作業コピーにチェックアウトします。
2. 入力データを復元し、`inputs.json` の SHA-256 と照合します。データ本体は自動コピーしません。
3. `uv sync --locked` で環境を用意し、保存した uv・Python・OS・パッケージの環境情報と比較します。
4. 保存した `config.json` で再実行し、新しい run の指標・分割・予測を比較します。

正式実行では正の `--issue` 番号が必須です。`--allow-dirty` は動作確認専用で、この場合のみ Issue 番号を省略できます。スナップショットの対象は上表に限定され、未コミットの全ファイルを保全しません。正式な検証にはコミット済みの実行を採用します。OS・CPU・ライブラリの違いによるビット単位一致は保証しません。

共有スキル変更時は、PyYAML を導入済みの Dev Container のシステム Python で次も実行します。ホストでは `.llm-agents/requirements.txt` を別の仮想環境に導入し、分析用の依存と分けます。

```sh
python3 -m unittest discover -s .llm-agents/tests
python3 .llm-agents/scripts/register-skills.py --check
```
