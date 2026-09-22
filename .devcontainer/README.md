# 開発環境について

Windows、macOS、Linux（Ubuntu）から共通の Ubuntu 24.04 環境を利用するための Dev Container 設定です。Titanic 分析用に Python 3.12.13 と uv 0.12.16 を使用します。

## 前提

- Visual Studio Code
- Docker コンテナを実行できる環境（Windows・macOS では Docker Desktop など）
- Docker Compose v2 以降（`docker compose` が利用可能なこと）
- VS Code の Dev Containers 拡張機能
- コンテナイメージと拡張機能を取得できるネットワーク接続

Windows では Linux コンテナを利用してください。

## 起動方法

1. Docker を起動します。
2. VS Code でリポジトリのルートを開きます。
3. 拡張機能画面で `@recommended` を検索し、Microsoft の **Dev Containers**（`ms-vscode-remote.remote-containers`）をホスト側にインストールします。
4. 左下のリモート接続ボタンから **Reopen in Container** を選ぶか、コマンドパレットから `Dev Containers: Reopen in Container` を実行します。既存環境を更新する場合は `Dev Containers: Rebuild Container` を実行します。
5. 左下に `Dev Container: Titanic Analysis` と表示されたら、拡張機能画面のコンテナ側で Claude Code・Codex・GitHub Copilot の導入を確認し、それぞれサインインします。

Compose を手動で起動する必要はありません。拡張機能が `devcontainer.json` を読み、開発用コンテナとプロキシをまとめて起動します。起動に失敗した場合は `Dev Containers: Show Container Log` で確認してください。

`customizations.vscode.settings` にコンテナ内の VS Code 用プロキシ設定を指定しています。ホスト側の VS Code や認証用ブラウザはホストのネットワーク設定を使います。`proxy:3128` は Compose 内の名前なので、ホストのユーザ設定には指定しないでください。企業ネットワークではホストからの拡張機能取得やブラウザ認証にも通信許可が必要です。

コンテナ内のユーザは `vscode` です。エージェント拡張機能は `devcontainer.json` の `customizations.vscode.extensions` に記載しています。各サービスの契約・認証は別途必要です。この雛形にはエージェントの CLI を追加する処理は含めていません。

作成時に `postCreateCommand` で共有スキルの登録スクリプトを実行します。コマンドの利用方法は [エージェント構成](../.llm-agents/README.md#コマンドで呼び出す) を参照してください。

## 外部アクセス用プロキシ

`compose.yaml` で開発用の `devcontainer` と Squid の `proxy` を一緒に起動します。Squid のヘルスチェックが成功すると開発用コンテナを起動し、VS Code から環境を閉じると両サービスを停止します。

開発用コンテナには `HTTP_PROXY` / `HTTPS_PROXY` と小文字の同名変数を `http://proxy:3128` に設定しています。これらを参照する curl、Git などの HTTP／HTTPS 通信が Squid を経由します。HTTPS は CONNECT で中継し、TLS の復号や独自 CA の配布は行いません。

`NO_PROXY` / `no_proxy` には `localhost,127.0.0.1,::1,proxy,devcontainer` を設定しています。別のサービスを追加して直接接続したい場合は、両方の変数にサービス名を追加してください。

プロキシのポートはホストに公開していません。同じ Compose ネットワーク内では認証なしで利用でき、接続先ポートは HTTP の 80 と HTTPS の 443 に限定しています。変更が必要な場合は `proxy/squid.conf` の ACL を編集して再ビルドしてください。キャッシュは無効で、アクセスログはコンテナの標準出力に記録します。

これは環境変数を利用する明示的なプロキシ設定です。直接通信をネットワークで禁止する構成ではありません。環境変数を参照しない拡張機能やツール、SSH などには個別の設定が必要です。また、イメージ取得・Dockerfile のビルド中の通信はこのプロキシを経由しません。それらにもプロキシが必要なネットワークでは、Docker 側のプロキシ設定を別途用意してください。

設定後は `Dev Containers: Rebuild Container` を実行します。開発用コンテナ内で次を実行すると、プロキシの利用と HTTPS CONNECT を確認できます。

```sh
curl -v --fail --head http://registry.npmjs.org
curl -v --fail --head https://pypi.org/simple/pip/
```

ホストのリポジトリルートから状態とアクセスログを確認できます。`compose.yaml` の `name` で Compose のプロジェクト名を `titanic-analysis_devcontainer` に固定しているため、Dev Containers 拡張が起動したコンテナも次のコマンドで操作できます。実際のプロジェクト名は `docker compose ls` で確認できます。

```sh
docker compose -f .devcontainer/compose.yaml ps
docker compose -f .devcontainer/compose.yaml logs --tail=50 proxy
```

構成の仕様は [VS Code の Dev Container 作成ガイド](https://code.visualstudio.com/docs/devcontainers/create-dev-container) と [Squid のアクセス制御](https://www.squid-cache.org/Doc/config/http_access/) を参照してください。

### ドメインのホワイトリスト・ブラックリスト

- `proxy/lists/whitelist.txt`: 許可するドメイン。有効な行がある場合、そのドメインだけを許可します。空の場合はブラックリスト以外を許可します。
- `proxy/lists/blacklist.txt`: 拒否するドメイン。両方に一致する場合は拒否を優先します。

初期状態では Python（uv / PyPI）、Node.js（npm）、Claude Code・Codex・GitHub Copilot・GitHub・VS Code のホストを許可しています。ブラックリストはコメントのみです。**許可リストにない宛先へのプロキシ通信は拒否されます。**

| 用途 | 許可する主なホスト |
| --- | --- |
| Python パッケージの取得 | `pypi.org`、`files.pythonhosted.org` |
| uv のインストーラと配布先 | `astral.sh`、`releases.astral.sh` |
| GitHub、uv・CPython 配布物、GitHub 依存、nvm | `.github.com`、`.githubusercontent.com`、`.githubassets.com`、`github-cloud.s3.amazonaws.com` |
| Node.js 本体・ヘッダ、npm パッケージ | `nodejs.org`、`registry.npmjs.org` |
| Claude Code | `api.anthropic.com`、`claude.ai`、`platform.claude.com`、`downloads.claude.ai` など |
| Codex | `.chatgpt.com`、`api.openai.com`、`.auth.openai.com`、配布・コンテンツ用 CDN など |
| GitHub Copilot | `.githubcopilot.com`、GitHub 共通ホスト、`default.exp-tas.com` |
| VS Code Server・拡張機能 | `marketplace.visualstudio.com`、`.gallery.vsassets.io`、`.gallerycdn.vsassets.io`、VS Code 配布用 CDN など |

配布元の根拠は [uv のインストール](https://docs.astral.sh/uv/getting-started/installation/)、[uv の Python 配布物](https://docs.astral.sh/uv/concepts/python-versions/)、[PyPI の Index API](https://docs.pypi.org/api/index-api/)、[npm のレジストリ](https://docs.npmjs.com/cli/v11/using-npm/registry/) を参照してください。uv は Docker ビルド時に公式イメージから導入します。Node.js は未導入です。

PyPy、Yarn、起動後の Ubuntu パッケージ取得用の候補は、許可リスト内にコメントで用意しています。社内レジストリや npm のインストールスクリプトが取得する追加バイナリ（Playwright、Cypress、Electron など）は、利用するものに応じて追加してください。GitHub Enterprise の独自ドメイン、企業 SSO の IdP、Bedrock・Vertex AI・Azure などの外部モデルプロバイダは別途追加してください。エージェントが Web 検索や外部サイト閲覧でアクセスする宛先も、利用先に応じた追加が必要です。接続が拒否された場合は `docker compose -f .devcontainer/compose.yaml logs --tail=100 proxy` の `TCP_DENIED/403` から宛先を確認できます。

接続先の確認には [Claude Code のネットワーク要件](https://code.claude.com/docs/en/network-config)、[Codex の認証](https://developers.openai.com/codex/auth/)、[Copilot の許可リスト](https://docs.github.com/en/copilot/reference/copilot-allowlist-reference)、[VS Code のネットワーク要件](https://code.visualstudio.com/docs/setup/network) を利用しています。Codex の一覧は通常の ChatGPT / API キー認証向けの基本構成で、全機能・外部連携を網羅するものではありません。サービス側の配布先変更時はログから追記してください。

GitHub の Git 操作をプロキシ経由にする場合は `https://github.com/OWNER/REPO.git` 形式を使ってください。SSH 形式の `git@github.com:OWNER/REPO.git` はこの HTTP プロキシを自動では利用しません。GitHub Packages の npm ホストは `.github.com` に含まれます。Copilot は全契約プラン向けのドメインを許可しています。Claude のプラグイン情報・旧インストーラ向けに `storage.googleapis.com` も許可するため、このホスト上の他のバケットにも通信できます。

GitHub の許可は特定のリポジトリだけに限定するものではありません。また、レジストリを許可しても個々のパッケージの安全性を判定するものではありません。

1行に1ドメインを記載します。`example.com` はそのホストだけ、`.example.com` はドメイン自身とサブドメインに一致します。URL、パス、ポート、`*.example.com` のようなワイルドカードは記載しません。空行、`#` 以降のコメント、Windows の改行に対応しています。

例えばホワイトリストに `.example.com`、ブラックリストに `blocked.example.com` を記載すると、`example.com` とそのサブドメインのうち `blocked.example.com` 以外を許可します。判定は HTTP の宛先ホスト名と HTTPS CONNECT の宛先ホスト名に適用します。IP アドレスからの逆引きは行いません。ヘルスチェックはリストの制限対象外です。ドメインの記法は [Squid の ACL 仕様](https://www.squid-cache.org/Doc/config/acl/) に従います。

リストのディレクトリは読み取り専用でマウントしています。初回は `Dev Containers: Rebuild Container` を実行してください。その後のリスト変更は、ホストのリポジトリルートから次を実行して反映します（イメージの再ビルドは不要）。再起動時には既存のプロキシ接続が切断されます。

```sh
docker compose -f .devcontainer/compose.yaml restart proxy
docker compose -f .devcontainer/compose.yaml ps
```

起動時にリストを読み込んで ACL を生成するため、`squid -k reconfigure` だけでは変更を反映できません。ファイルの削除や読み取り権限の不足がある場合は起動に失敗します。この制限が適用されるのは Squid を経由する通信です。

## トークン削減ツール

コンテナのビルド時に以下をインストールします。

| ツール | 用途 |
| --- | --- |
| RTK（Rust Token Killer） | 対応するコマンドの出力を圧縮し、LLM が読む量を削減 |
| ripgrep（`rg`） | 必要なファイルや行に検索を限定 |
| `jq` | JSON から必要な項目だけを抽出 |
| Python 3・PyYAML | 共有スキルの登録と YAML メタデータの検証 |

RTK は [公式リリース v0.49.0](https://github.com/rtk-ai/rtk/releases/tag/v0.49.0) に固定しています。[公式インストーラ](https://github.com/rtk-ai/rtk/blob/v0.49.0/install.sh) で Linux の x86_64 / ARM64 を判定し、SHA-256 の検証後に `/usr/local/bin/rtk` へ配置します。初回ビルドには Ubuntu のパッケージ配布元と GitHub への接続が必要です。

設定を反映するには `Dev Containers: Rebuild Container` を実行してください。コンテナ内のターミナルで確認できます。

```sh
rtk --version
rtk git status
rtk git diff
rtk git log -5
rtk gain
rg --version
jq --version
```

利用方針は [共通プロンプト](../.llm-agents/instructions.md) に集約しています。Claude Code、Codex、GitHub Copilot はその指示に従って `rtk` を明示的に呼び出します。通常のコマンドを自動変換するフックや `rtk init` による指示ファイルの生成は行っていません。エージェントが Dev Container 内のターミナルを使っていることを確認してください。

圧縮された出力だけで判断できない場合は、元のコマンドで必要な情報を確認してください。`rtk gain` は RTK 経由の実行による推定削減量を表示します。ファイル閲覧など別の経路で渡す情報には適用されず、実際の請求額の削減率を示すものではありません。

更新時は `Dockerfile` の `RTK_VERSION` を変更して再ビルドします。利用例と対応コマンドは [RTK 公式ドキュメント](https://www.rtk-ai.app/docs/getting-started/installation/) を参照してください。

Python 3 と PyYAML は Ubuntu のパッケージとして明示的に導入し、ビルド時に Python の起動と `yaml` のインポートを確認します。コンテナ外での依存導入と回帰テストは [エージェント構成](../.llm-agents/README.md#回帰テスト) を参照してください。

ベースイメージの既定値は更新可能な `ubuntu-24.04` タグです。厳密に固定する場合は、`compose.yaml` の `services.devcontainer.build.args.BASE_IMAGE` に確認済みの `mcr.microsoft.com/devcontainers/base:ubuntu-24.04@sha256:<digest>` を指定してください。Dockerfile の `BASE_IMAGE` ビルド引数で切り替えられます。プロキシのベースイメージは `proxy/Dockerfile` の `ubuntu:24.04` です。ベースイメージを固定しても、ビルド時に取得する Ubuntu パッケージまで同一になる保証はありません。

## カスタマイズ

- 使用言語が決まったら、`devcontainer.json` に Features を追加するか、既存の `Dockerfile` に必要なツールを追加してください。
- 開発サーバを利用する場合は、必要に応じて `forwardPorts` を追加してください。
- 設定変更後は `Dev Containers: Rebuild Container` を実行してください。
- API キーや認証情報をイメージ・設定ファイル・Git に保存しないでください。

Dev Container を使わず、各 OS 上で直接開発することもできます。その場合は必要な開発ツールを個別に用意してください。

## Titanic 分析環境

作成時に共有スキル登録の後で `uv sync --locked` を実行します。Python 3.12.13 は uv が取得し、分析用の `.venv` を作成します。システム Python と PyYAML は共有スキル用に維持します。分析依存に PyYAML を混ぜません。

uv は `ghcr.io/astral-sh/uv:0.12.16` からコピーします。このイメージの取得はビルド時の通信です。起動後の Python と依存の取得先は既存の GitHub・PyPI 許可リストで対応します。Kaggle データはホストで取得して `data/raw/` に配置してください。

ワークスペースは既存の `/workspaces/Multi-LLM-Project` を維持します。Compose 名は `titanic-analysis_devcontainer` に変更したため、旧環境とは別のコンテナになります。ホストのリポジトリは同じものをマウントします。旧環境のコンテナ内だけに保存したファイルがあれば先に取り出し、新環境へ移してください。旧コンテナは自動削除しません。

フロントアプリ・API は未実装のため、アプリの待受ポートや転送ポートはありません。

```sh
uv --version
uv sync --locked
uv run --locked python --version
uv run --locked python scripts/run_experiment.py --config configs/smoke.json --allow-dirty
uv run --locked python -m unittest discover -s tests -v
uv run --locked ruff check scripts tests
uv run --locked ruff format --check scripts tests
```

ホストで形式とビルドを確認する場合はルートで実行します。

```sh
docker compose -f .devcontainer/compose.yaml config --quiet
docker compose -f .devcontainer/compose.yaml build
```

ホストとコンテナでは `.venv` を共用できません。既存環境が別 OS 用の場合は退避してから `uv sync --locked` を実行してください。データと実験記録の説明は [README](../README.md) を参照してください。
