# Quarto MCP Server

Quarto Markdown（.qmd形式）を文字列として受け取り、PowerPoint（.pptx）形式を中心としたQuarto CLIがサポートする多様な出力形式に変換する MCP（Model Context Protocol）対応サーバー。

## 主要機能

- **PowerPoint形式を主軸**: 企業プレゼンテーション作成を最優先ユースケースとして設計
- **カスタムテンプレート対応**: PowerPointの企業テンプレート（.pptx）を指定可能
- **文字列ベースの入力**: LLM/MCPクライアントから純粋な文字列として Quarto Markdown を受理
- **多形式出力対応**: PowerPoint以外にもQuarto CLIがサポートする全形式に対応
- **静的変換のみ**: セキュリティ確保のため、コードセル実行は行わない（`--no-execute`固定）

## サポート形式

- **プレゼンテーション**: pptx（PowerPoint）、revealjs、beamer
- **ドキュメント**: html、pdf、docx、odt、epub、typst
- **Markdown**: gfm、commonmark、hugo、docusaurus、markua
- **Wiki**: mediawiki、dokuwiki、zimwiki、jira、xwiki
- **その他**: jats、ipynb、rtf、rst、asciidoc、org、context、texinfo、man

## 必須要件

- Python 3.10以上
- Quarto CLI 1.3以上
- uv（Pythonパッケージマネージャー）推奨

### 追加要件（形式別）

- PDF出力: TeX Live または TinyTeX（`quarto install tinytex`）
- Typst出力: Typst CLI

## インストール

### uvxを使用した実行（推奨）

システムにインストールせずに直接実行できます：

```bash
# ローカルディレクトリから実行
uvx --from . quarto-mcp

# Gitリポジトリから直接実行
uvx --from git+https://github.com/notfolder/quarto_mcp quarto-mcp
```

### pip/uvでインストール

```bash
# ローカルから
pip install .
# または
uv pip install .

# インストール後
quarto-mcp
```

## 使用方法

### MCPクライアントから使用

MCP設定ファイル（例: `~/.config/mcp/settings.json`）に以下を追加：

```json
{
  "mcpServers": {
    "quarto": {
      "command": "uvx",
      "args": ["--from", "/path/to/quarto_mcp", "quarto-mcp"]
    }
  }
}
```

### quarto_render ツール

```typescript
// MCPクライアントから呼び出し
{
  "content": "# My Presentation\n\n## Slide 1\n\nContent here...",
  "format": "pptx",
  "output_path": "/path/to/output.pptx",
  "template": "corporate_standard",  // オプション
  "format_options": {                 // オプション
    "slide-level": 2
  }
}
```

#### パラメータ

- **content** (必須): Quarto Markdown文字列
- **format** (必須): 出力形式ID（例: `pptx`, `html`, `pdf`）
- **output_path** (必須): 出力ファイルの絶対パス
- **template** (任意): PowerPoint用テンプレートIDまたは絶対パス
- **format_options** (任意): 形式固有のオプション設定

## テンプレート設定

PowerPointテンプレートは `config/templates.yaml` で設定：

```yaml
templates:
  corporate_standard:
    path: /app/templates/corporate_standard.pptx
    description: "企業標準テンプレート"
```

## 開発

```bash
# 依存関係をインストール
uv pip install -e .

# Quarto CLIの確認
quarto check

# サーバー起動
python -m src.server
```

## ライセンス

CC-BY-4.0

## 詳細仕様

詳細な設計仕様については [docs/SPEC.md](docs/SPEC.md) を参照してください。
