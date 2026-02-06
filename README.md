# Quarto MCP Server

Quarto Markdown（.qmd形式）を文字列として受け取り、PowerPoint（.pptx）形式を中心としたQuarto CLIがサポートする多様な出力形式に変換する MCP（Model Context Protocol）対応サーバー。

## 主要機能

- **PowerPoint形式を主軸**: 企業プレゼンテーション作成を最優先ユースケースとして設計
- **カスタムテンプレート対応**: PowerPointの企業テンプレート（.pptx）を指定可能
  - 設定ファイルで複数テンプレートを事前登録
  - ツール引数でテンプレートIDまたはURLを指定
  - **URL指定時は自動ダウンロードして使用**（HTTP/HTTPS対応）
- **文字列ベースの入力**: LLM/MCPクライアントから純粋な文字列として Quarto Markdown を受理
- **多形式出力対応**: PowerPoint以外にもQuarto CLIがサポートする全形式に対応
- **ファイルパス出力**: 指定されたパスに直接出力ファイルを生成
- **静的変換のみ**: セキュリティ確保のため、コードセル実行は行わない（`--no-execute`固定）

## 必須環境

- Python 3.10以上
- Quarto CLI 1.3以上

## インストール

### uvxを使用した実行（推奨）

```bash
# ローカルディレクトリから実行
uvx --from . quarto-mcp

# Gitリポジトリから直接実行
uvx --from git+https://github.com/notfolder/quarto_mcp quarto-mcp
```

### pipを使用したインストール

```bash
# ローカルから
pip install .

# Gitから
pip install git+https://github.com/notfolder/quarto_mcp
```

## 使用方法

MCPクライアントの設定ファイル（例: `~/.config/mcp/settings.json`）に以下を追加:

```json
{
  "mcpServers": {
    "quarto": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/notfolder/quarto_mcp", "quarto-mcp"]
    }
  }
}
```

## 提供ツール

### quarto_render

Quarto Markdownを指定形式に変換します。

**パラメータ:**
- `content` (必須): Quarto Markdown形式の文字列
- `format` (必須): 出力形式ID（pptx, html, pdf, docx等）
- `output_path` (必須): 出力ファイルの絶対パス
- `template` (任意): PowerPointテンプレート指定
  - テンプレートID（templates.yamlで定義）
  - HTTP/HTTPS URL（.pptxファイル）- 自動ダウンロード対応
- `format_options` (任意): 出力形式固有のオプション

**使用例:**

```python
# テンプレートIDを使用
{
  "content": "# スライドタイトル\n\n内容",
  "format": "pptx",
  "output_path": "/path/to/output.pptx",
  "template": "corporate_standard"
}

# HTTP URLからテンプレートをダウンロード
{
  "content": "# スライドタイトル\n\n内容",
  "format": "pptx",
  "output_path": "/path/to/output.pptx",
  "template": "https://example.com/templates/custom.pptx"
}
```

### quarto_list_formats

サポートされている出力形式の一覧を取得します。

## テンプレート機能

### テンプレートID

`config/templates.yaml`でテンプレートを事前登録できます:

```yaml
templates:
  corporate_standard:
    path: /path/to/corporate_standard.pptx
    description: "企業標準テンプレート"
```

### HTTP/HTTPSダウンロード

URLを直接指定することで、テンプレートを自動ダウンロードできます:

- **対応プロトコル**: HTTP, HTTPS（HTTPSを推奨）
- **ファイル形式**: .pptx形式のみ
- **ダウンロードタイムアウト**: 30秒
- **最大ファイルサイズ**: 50MB

## サポート形式

### プレゼンテーション形式
- `pptx`: Microsoft PowerPoint（テンプレート対応）
- `revealjs`: Reveal.js HTMLプレゼンテーション
- `beamer`: LaTeX Beamer

### ドキュメント形式
- `html`: HTML5
- `pdf`: PDF
- `docx`: Microsoft Word
- `odt`: OpenDocument Text
- `epub`: EPUB電子書籍

### Markdown形式
- `gfm`: GitHub Flavored Markdown
- `commonmark`: CommonMark
- `hugo`: Hugo
- `docusaurus`: Docusaurus

その他、多数の形式に対応。詳細は`quarto_list_formats`ツールで確認できます。

## ライセンス

CC-BY-4.0

## 詳細仕様

詳細な設計仕様については、[docs/SPEC.md](docs/SPEC.md)を参照してください。
