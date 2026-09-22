# Multi-LLM-Project

## このリポジトリについて

このリポジトリは、複数の LLM を VS Code のコーディングエージェントで利用するためのテンプレートリポジトリです。
対象とする LLM サービスは Claude Code、Codex、GitHub Copilot です。
Windows、macOS、Linux（Ubuntu）での開発を対象とします。

## はじめ方

1. このリポジトリをテンプレートとして利用するか、クローンします。Windows で直接クローンする場合は、スキル登録用のシンボリックリンクを保持するため [Windows での利用](.llm-agents/README.md#windows-での利用) を先に確認してください。
2. VS Code でリポジトリのルートを開き、必要な推奨拡張機能をインストールします。
3. 利用する Claude Code、Codex、GitHub Copilot のアカウントでサインインします。
4. [共通ルール](AGENTS.md) を確認し、[共通プロンプト](.llm-agents/instructions.md) のプロジェクト固有の情報を更新します。対話で設定する場合は、下記の `setup-project` を利用できます。
5. 共通のコンテナ環境を使う場合は、[Dev Container の手順](.devcontainer/README.md) に従います。

## 対話でプロジェクトを設定する

[setup-project](.llm-agents/skills/setup-project/SKILL.md) に開発したいものの目的や技術スタックを伝えると、不足する要件を対話で整理し、Dev Container、共通プロンプト、README などを更新します。

例えば「このリポジトリの setup-project スキルを使って、本の貸出管理アプリの開発環境を設定してください」と依頼できます。

エージェント別の記法や候補に出ない場合の対処は、[コマンドで呼び出す](.llm-agents/README.md#コマンドで呼び出す) を参照してください。

## ディレクトリ構成

```text
.
├── AGENTS.md                       # 共通ルールの正本・Codex の入口
├── CLAUDE.md                       # Claude Code の入口
├── LICENSE
├── .github/
│   └── copilot-instructions.md     # GitHub Copilot の入口
├── .llm-agents/
│   ├── README.md                   # エージェント構成の説明
│   ├── instructions.md             # 共通プロンプトの本体
│   ├── requirements.txt            # 登録スクリプトの依存（PyYAML）
│   ├── skills/                     # スキルの本体の配置先
│   ├── agents/                     # エージェント定義の本体の配置先
│   ├── tmp/                        # 必要時に作成するローカルの一時記録（Git 管理対象外）
│   ├── scripts/
│   │   └── register-skills.py      # 探索場所へのリンクの登録・検証
│   └── tests/
│       └── test_register_skills.py # 登録スクリプトの回帰テスト
├── .claude/skills/                 # Claude Code・Copilot の探索場所（本体へのリンク）
├── .agents/skills/                 # Codex の探索場所（本体へのリンク）
├── .devcontainer/
│   ├── README.md                   # 開発環境の説明
│   ├── devcontainer.json           # Ubuntu ベースの共通環境
│   ├── compose.yaml                # 開発用コンテナとプロキシの起動定義
│   ├── Dockerfile                  # RTK・検索補助ツールの導入
│   └── proxy/                      # Squid によるドメインの許可・拒否
│       ├── Dockerfile
│       ├── entrypoint.sh           # リストから ACL を生成
│       ├── squid.conf
│       └── lists/                  # whitelist.txt・blacklist.txt
└── .vscode/
    ├── extensions.json             # 推奨拡張機能
    └── settings.json               # ワークスペース設定
```

共通プロンプトは1ファイルに集約し、各エージェントの入口から参照します。アプリケーションの言語やディレクトリ構成は、利用するプロジェクトに合わせて追加してください。

共有スキルを追加する場合は、いずれのエージェントでも「このリポジトリの `create-shared-skill` スキルを使って、○○用のスキルを作成してください」と依頼できます。作成したスキルは共通ディレクトリに配置され、他のエージェントでも同じ本体を読み込んで利用できます。

エージェントについての詳細は [.llm-agents/README.md](.llm-agents/README.md) を参照してください。
開発環境についての詳細は [.devcontainer/README.md](.devcontainer/README.md) を参照してください。

共有スキル作成コマンドは Claude Code・Copilot では `/create-shared-skill`、Codex では `$create-shared-skill` です。[登録と呼び出しの手順](.llm-agents/README.md#コマンドで呼び出す) を参照してください。
