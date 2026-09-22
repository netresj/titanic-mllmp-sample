# 厳密なベースイメージ固定が必要な場合は、ビルド引数に digest 付き参照を指定する。
ARG BASE_IMAGE=mcr.microsoft.com/devcontainers/base:ubuntu-24.04
FROM ghcr.io/astral-sh/uv:0.12.16 AS uv
FROM ${BASE_IMAGE}

COPY --from=uv /uv /uvx /usr/local/bin/

# インストーラとバイナリのバージョンを揃えて固定する。
ARG RTK_VERSION=v0.49.0

USER root

# 検索範囲と JSON の出力項目を絞る補助ツールも用意する。
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl ripgrep jq python3 python3-yaml python3-venv \
    && rm -rf /var/lib/apt/lists/*

# 公式インストーラが CPU を判定し、配布バイナリの SHA-256 を検証する。
RUN curl -fsSL --retry 3 \
      "https://raw.githubusercontent.com/rtk-ai/rtk/${RTK_VERSION}/install.sh" \
      -o /tmp/install-rtk.sh \
    && RTK_VERSION="${RTK_VERSION}" RTK_INSTALL_DIR=/usr/local/bin \
       RTK_SKIP_CHECKSUM=0 sh /tmp/install-rtk.sh \
    && rm /tmp/install-rtk.sh \
    && rtk --version

USER vscode

# 実際の利用ユーザで実行と統計データの書き込みを確認する。
RUN rtk gain && rg --version && jq --version \
    && python3 --version && python3 -c 'import yaml'
