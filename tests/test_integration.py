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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
