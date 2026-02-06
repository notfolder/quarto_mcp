"""
統合テスト（Quarto CLIが必要）

注: これらのテストはQuarto CLIがインストールされている環境でのみ実行可能です。
"""

import pytest
import os
import tempfile
from pathlib import Path

from src.core.renderer import QuartoRenderer, QuartoRenderError


# Quarto CLIが利用可能かチェック
def is_quarto_available():
    """Quarto CLIが利用可能かチェックする."""
    try:
        import subprocess
        result = subprocess.run(
            ["quarto", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# Quarto CLIが利用可能な場合のみテストを実行
pytestmark = pytest.mark.skipif(
    not is_quarto_available(),
    reason="Quarto CLI is not available"
)


@pytest.mark.asyncio
async def test_render_to_html():
    """HTML出力の統合テスト."""
    renderer = QuartoRenderer()
    
    # シンプルなQuarto Markdown
    content = """# テストドキュメント

これはテストです。

## セクション1

内容1

## セクション2

内容2
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "output.html"
        
        # レンダリング実行
        result = await renderer.render(
            content=content,
            format_id="html",
            output_path=str(output_path),
        )
        
        # 結果の検証
        assert result.success is True
        assert result.format == "html"
        assert result.output.path == str(output_path)
        assert output_path.exists()
        assert result.output.size_bytes > 0
        assert result.metadata.quarto_version
        assert result.metadata.render_time_ms > 0


@pytest.mark.asyncio
async def test_render_with_yaml_header():
    """YAMLヘッダー付きコンテンツの統合テスト."""
    renderer = QuartoRenderer()
    
    # YAMLヘッダー付きQuarto Markdown
    content = """---
title: "テストドキュメント"
author: "テスト作成者"
---

# はじめに

これはYAMLヘッダー付きのテストです。
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "output.html"
        
        # レンダリング実行
        result = await renderer.render(
            content=content,
            format_id="html",
            output_path=str(output_path),
        )
        
        # 結果の検証
        assert result.success is True
        assert output_path.exists()


@pytest.mark.asyncio
async def test_render_invalid_format():
    """不正な形式IDのエラーテスト."""
    renderer = QuartoRenderer()
    
    content = "# テスト"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "output.txt"
        
        # 不正な形式ID
        with pytest.raises(QuartoRenderError) as exc_info:
            await renderer.render(
                content=content,
                format_id="invalid_format",
                output_path=str(output_path),
            )
        
        assert exc_info.value.code == "UNSUPPORTED_FORMAT"


@pytest.mark.asyncio
async def test_render_pptx_for_manual_inspection():
    """PowerPoint出力テスト（手動確認用）.
    
    このテストは実際のPowerPointファイルを生成し、
    test_output/ディレクトリに保存します。
    テスト後にファイルを開いて内容を確認できます。
    """
    renderer = QuartoRenderer()
    
    # プレゼンテーション用のQuarto Markdown
    content = """---
title: "Quarto MCP Server デモ"
subtitle: "PowerPoint出力テスト"
author: "Quarto MCP Team"
date: "2026-02-07"
format:
  pptx:
    slide-level: 2
---

# イントロダクション

## Quarto MCP Serverとは

Quarto MCPサーバーは、Quarto Markdownを様々な形式に変換するツールです。

主な特徴：

- **PowerPoint形式を主軸**: 企業プレゼンテーション作成を最優先
- **カスタムテンプレート対応**: 企業テンプレートの利用可能
- **文字列ベースの入力**: LLMから直接Markdownを受理

## 技術スタック

使用技術：

1. Python 3.10+
2. Quarto CLI 1.3+
3. MCP (Model Context Protocol)
4. httpx（非同期HTTP通信）

# デモコンテンツ

## リスト表示

箇条書きの例：

- 項目1
- 項目2
  - サブ項目A
  - サブ項目B
- 項目3

## 番号付きリスト

1. 最初のステップ
2. 次のステップ
3. 最後のステップ

## コードブロック

```python
def hello_quarto():
    print("Hello, Quarto MCP!")
    return "Success"
```

# まとめ

## 今後の展望

- アイコン検索機能の実装
- テンプレート管理の強化
- パフォーマンス最適化

## お問い合わせ

ご質問やフィードバックをお待ちしております！
"""
    
    # test_outputディレクトリを作成
    output_dir = Path(__file__).parent.parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "demo_presentation.pptx"
    
    # レンダリング実行
    result = await renderer.render(
        content=content,
        format_id="pptx",
        output_path=str(output_path),
    )
    
    # 結果の検証
    assert result.success is True
    assert result.format == "pptx"
    assert output_path.exists()
    assert result.output.size_bytes > 0
    
    # テスト成功時にファイルパスを表示
    print(f"\n✅ PowerPointファイルが生成されました: {output_path.absolute()}")
    print(f"   ファイルサイズ: {result.output.size_bytes:,} bytes")
    print(f"   変換時間: {result.metadata.render_time_ms} ms")
    print(f"\n   以下のコマンドでファイルを開けます:")
    print(f"   open {output_path.absolute()}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
