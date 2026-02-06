# Contributing to Quarto MCP Server

## 開発環境のセットアップ

### 1. 必須ソフトウェアのインストール

- Python 3.10以上
- Quarto CLI 1.3以上
- uv（推奨）またはpip

### 2. 依存関係のインストール

```bash
# uvを使用する場合（推奨）
uv pip install -e .

# pipを使用する場合
pip install -r requirements.txt
```

### 3. Quarto CLIの確認

```bash
quarto check
```

## テストの実行

### コンポーネントテスト（Quarto不要）

```bash
python tests/test_components.py
```

このテストでは以下を検証します：
- 一時ファイル管理
- テンプレート解決
- 形式定義
- データモデル
- サーバー初期化

### 統合テスト（Quarto必要）

```bash
python tests/test_basic.py
```

このテストでは実際にQuarto CLIを使用して変換を実行します。

## コード構成

```
src/
├── server.py              # MCPサーバーエントリポイント
├── core/
│   ├── renderer.py        # Quarto CLI実行ロジック
│   ├── file_manager.py    # 一時ファイル管理
│   └── template_manager.py # テンプレート管理
├── models/
│   ├── formats.py         # 形式定義
│   └── schemas.py         # 入出力スキーマ
└── tools/
    └── render.py          # quarto_renderツール実装
```

## 新機能の追加

### 新しい出力形式のサポート

1. `src/models/formats.py`に形式を追加：
   - `FORMAT_MIME_TYPES`辞書
   - `FORMAT_EXTENSIONS`辞書

2. テストを追加して動作確認

### 新しいMCPツールの追加

1. `src/tools/`に新しいモジュールを作成
2. ツール関数とTOOL_DEFINITIONを定義
3. `src/server.py`でツールを登録

## コーディング規約

- PEP 8に準拠
- 型ヒントを使用
- docstring形式のコメントを必ずつける
- 日本語でコメントを記述

## Pull Requestの作成

1. フォークしてブランチを作成
2. 変更を実装
3. テストを追加・実行
4. Pull Requestを作成

## 質問・バグ報告

GitHubのIssuesで報告してください。
