"""
基本的な機能テスト
注意: Quarto CLIがインストールされている環境で実行してください
"""
import asyncio
import os
import tempfile
from pathlib import Path

from src.core.renderer import QuartoRenderer


async def test_basic_render():
    """基本的なレンダリングテスト"""
    print("Testing basic Quarto rendering...")
    
    # サンプルコンテンツ
    content = """---
title: "Test Presentation"
---

# Introduction

This is a test slide.

## Features

- Feature 1
- Feature 2
- Feature 3
"""
    
    # 一時ファイルを作成
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        output_path = f.name
    
    try:
        renderer = QuartoRenderer()
        
        # HTMLに変換（最も基本的な形式）
        result = await renderer.render(
            content=content,
            format="html",
            output_path=output_path
        )
        
        print(f"✓ Render successful!")
        print(f"  Format: {result.format}")
        print(f"  Output: {result.output.path}")
        print(f"  Size: {result.output.size_bytes} bytes")
        print(f"  Quarto version: {result.metadata.quarto_version}")
        print(f"  Render time: {result.metadata.render_time_ms} ms")
        
        # ファイルが存在することを確認
        assert Path(output_path).exists(), "Output file not created"
        print(f"✓ Output file exists")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
        
    finally:
        # クリーンアップ
        if os.path.exists(output_path):
            os.remove(output_path)


async def test_multiple_formats():
    """複数形式のテスト"""
    print("\nTesting multiple output formats...")
    
    content = """# Test Document

This is a simple test document.
"""
    
    formats = ["html", "gfm", "commonmark"]
    
    for fmt in formats:
        print(f"\n  Testing format: {fmt}")
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_path = f.name
        
        try:
            renderer = QuartoRenderer()
            result = await renderer.render(
                content=content,
                format=fmt,
                output_path=output_path
            )
            
            if Path(output_path).exists():
                print(f"    ✓ {fmt} conversion successful")
            else:
                print(f"    ✗ {fmt} conversion failed - no output file")
                
        except Exception as e:
            print(f"    ✗ {fmt} conversion failed: {e}")
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)


async def main():
    """メインテスト実行"""
    print("="*60)
    print("Quarto MCP Server - Basic Tests")
    print("="*60)
    
    # Quartoがインストールされているか確認
    try:
        import subprocess
        result = subprocess.run(
            ["quarto", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"\nQuarto CLI version: {result.stdout.strip()}\n")
    except Exception as e:
        print(f"\n⚠ Warning: Quarto CLI not found or not accessible")
        print(f"   Please install Quarto CLI to run these tests")
        print(f"   Error: {e}\n")
        return
    
    # テスト実行
    success = await test_basic_render()
    
    if success:
        await test_multiple_formats()
    
    print("\n" + "="*60)
    print("Tests completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
