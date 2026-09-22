# LLM エージェントについて

Claude Code、Codex、GitHub Copilot の3種類の拡張機能で共通の指示を利用するための構成です。共通プロンプト、スキル、エージェント定義の本体を `.llm-agents/` に集約します。

## 指示の参照関係

| 対象 | 入口 | 参照先 |
| --- | --- | --- |
| Codex | `AGENTS.md` | `.llm-agents/instructions.md` |
| Claude Code | `CLAUDE.md` | `AGENTS.md` → `.llm-agents/instructions.md` |
| GitHub Copilot | `.github/copilot-instructions.md` | `AGENTS.md` → `.llm-agents/instructions.md` |

[AGENTS.md](../AGENTS.md) を共通ルールの正本とし、[instructions.md](instructions.md) に作業手順とプロジェクト固有の情報を記載します。矛盾がある場合は `AGENTS.md` を優先します。

共通指示の入口には参照とツール固有の追加指示だけを記載します。スキルのコマンド登録には、下記のシンボリックリンクを利用します。

## 配置と更新方法

- `instructions.md`: 共通プロンプトの唯一の本体です。プロジェクトの目的や検証コマンドをここに記入してください。
- `skills/`: 再利用するスキルの本体を配置します（例: `skills/review/SKILL.md`）。
- `agents/`: 役割別のエージェント定義を配置します（例: `agents/reviewer.md`）。
- `tmp/`: 同じ作業環境のエージェント間で参照する作業記録やレビュー結果などの一時ファイルを、必要時に作成します。Git 管理対象外のため、クローン先や他の環境には共有されません。継続して共有・保存する内容は、適切な Git 管理対象のドキュメントへ転記してください。

`skills/` には共有スキル作成用の `create-shared-skill` を用意しています。`agents/` は空の配置先です。共通プロンプトがこのページの一覧から必要なスキルを選び、その本体を読む構成です。各エージェントの探索場所に本体へのリンクを置き、コマンドからも呼び出せるようにしています。

共通の変更は `AGENTS.md` または `instructions.md` に、ツール固有の変更は対応する入口に追記してください。Copilot の入口は `.github/copilot-instructions.md` とし、`.vscode/` に同じ指示を複製しません。

## 共有スキル一覧

| 名前 | 利用する場面 | 本体 |
| --- | --- | --- |
| `create-shared-skill` | 3エージェントで共有するスキルの作成・更新 | [SKILL.md](skills/create-shared-skill/SKILL.md) |
| `setup-project` | 目的や技術スタックを対話で整理し、開発環境とドキュメントを設定 | [SKILL.md](skills/setup-project/SKILL.md) |

## スキルを作成・利用する

Claude Code、Codex、GitHub Copilot のいずれでも、例えば次のように依頼します。

```text
このリポジトリの create-shared-skill スキルを使って、差分レビュー用の review-changes スキルを作成してください。
```

作成した本体は `.llm-agents/skills/review-changes/SKILL.md` に配置され、このページの一覧に登録されます。別のエージェントでも同じリポジトリを開き、次のように依頼できます。

```text
このリポジトリの review-changes スキルを使って、現在の差分をレビューしてください。
```

`review-changes` は作成例であり、初期状態では含まれていません。名前で読み込まれない場合は `.llm-agents/skills/<名前>/SKILL.md を読み、その手順を実行してください` と本体を指定してください。新しいスキルを作成した後も、入口ファイルの複製やエージェント別の本文の同期は不要です。

この方式は各エージェントがリポジトリ内の指示ファイルを読めることを前提とします。スキルが追加の実行環境や外部ツールを必要とする場合は、その依存を別途用意してください。


## コマンドで呼び出す

リポジトリを開き、各エージェントのチャット入力欄で実行します。ターミナルのシェルコマンドではありません。

| エージェント | 呼び出し例 | 探索場所 |
| --- | --- | --- |
| Claude Code | `/create-shared-skill レビュー用のスキルを作成してください` | `.claude/skills/create-shared-skill/` |
| GitHub Copilot（VS Code） | `/create-shared-skill レビュー用のスキルを作成してください` | `.claude/skills/create-shared-skill/` |
| Codex（CLI・IDE） | `$create-shared-skill レビュー用のスキルを作成してください` | `.agents/skills/create-shared-skill/` |
| Claude Code | `/setup-project React と FastAPI を使ったアプリを開発したいです` | `.claude/skills/setup-project/` |
| GitHub Copilot（VS Code） | `/setup-project React と FastAPI を使ったアプリを開発したいです` | `.claude/skills/setup-project/` |
| Codex（CLI・IDE） | `$setup-project 本の貸出管理アプリを開発したいです` | `.agents/skills/setup-project/` |

Claude Code と Copilot では `/`、Codex では `$` から候補を選びます。Codex の `/skills` からもスキルを選択できます。候補に出ない場合は、下記の登録確認後にエージェントを再起動するか、VS Code の `Developer: Reload Window` を実行してください。

### 登録の仕組み

各探索場所の `<名前>` は `../../.llm-agents/skills/<名前>` を指す相対シンボリックリンクです。`SKILL.md` と補助ファイルの本体は共有ディレクトリのみに置きます。`.github/skills/` への追加コピーは不要です。

Dev Container には Python 3 と PyYAML を導入済みです。コンテナ外では初回にルートで依存を導入してください。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r .llm-agents/requirements.txt
```

以降の `python3` は `.venv/bin/python` に置き換えます。Windows では環境作成に `py -3 -m venv .venv`、実行には `.venv\Scripts\python.exe` を使います。

新しいスキルの作成後は、ルートで次を実行します。`create-shared-skill` の手順にも含まれています。

```sh
python3 .llm-agents/scripts/register-skills.py
python3 .llm-agents/scripts/register-skills.py --check
```

登録スクリプトは名前（64文字未満の小文字英数字とハイフン）、frontmatter の `name` とディレクトリ名の一致、空でない文字列の `description` を検証し、不足するリンクだけを追加します。同じリンクがあれば変更せず、別のファイルやリンクがあればエラーにします。共有ディレクトリを参照するリンクの本体・`SKILL.md` 欠落も、通常実行と `--check` の両方でエラーにします。削除・改名したスキルの古いリンクは自動削除しないため、対象を確認して手動で整理してください。共有ディレクトリ以外を参照する独自スキルのリンクは変更しません。Dev Container の作成時にも登録を実行します。

### 回帰テスト

依存の導入後、ルートで実行します。テストは一時ディレクトリを使用します。

```sh
python3 -m unittest discover -s .llm-agents/tests -v
python3 .llm-agents/scripts/register-skills.py --check
```

テストは必要に応じてローカルで実行してください。Windows のテストにはシンボリックリンク作成権限が必要です。このチェックはファイルの整合性を検証するもので、各エージェントの画面上での認識は別途確認してください。

### Windows での利用

Windows 上で直接利用する場合は Python 3 とシンボリックリンク作成権限（開発者モードなど）が必要です。コマンドの `python3` は `py -3` に置き換えられます。Git でリンクを保持するには、リンクを利用できる環境で `git -c core.symlinks=true clone <リポジトリURL>` を使ってください。

リンクが通常のテキストファイルとしてチェックアウトされている場合、登録スクリプトは上書きせず停止します。リンクを保持できる環境でクローンし直すか、WSL の Linux ファイルシステム上でクローンして Dev Container を利用してください。

### 公式仕様

- [Claude Code: スキルの配置と呼び出し](https://code.claude.com/docs/en/skills)
- [VS Code: Agent Skills とスラッシュコマンド](https://code.visualstudio.com/docs/agent-customization/agent-skills)
- [Codex: ローカルスキルと明示的な呼び出し](https://learn.chatgpt.com/docs/build-skills)
