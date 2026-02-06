# Quarto MCP Server - Dockerfile
# Python 3.11ベースのイメージでQuarto CLIとMCPサーバーを実行

FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新と必要なツールのインストール
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Quarto CLIのインストール
# 最新版のURLは https://github.com/quarto-dev/quarto-cli/releases から確認
ARG QUARTO_VERSION=1.4.549
RUN wget -q https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.deb && \
    dpkg -i quarto-${QUARTO_VERSION}-linux-amd64.deb && \
    rm quarto-${QUARTO_VERSION}-linux-amd64.deb

# TinyTeXのインストール（PDF出力対応）
# 必要に応じてコメント解除
# RUN quarto install tinytex --no-prompt

# Pythonパッケージのインストール
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# アプリケーションファイルをコピー
COPY src/ ./src/
COPY config/ ./config/
COPY templates/ ./templates/

# 設定ファイルのパスを環境変数で指定可能にする
ENV QUARTO_MCP_CONFIG=/app/config/templates.yaml

# MCPサーバーを起動
CMD ["python", "-m", "src.server"]
