"""基本的なテストケース."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from src.core.file_manager import TempFileManager
from src.models.formats import FORMAT_DEFINITIONS


def test_format_definitions():
    """出力形式定義のテスト."""
    # pptx形式が存在することを確認
    assert "pptx" in FORMAT_DEFINITIONS
    
    # pptx形式の情報を確認
    pptx_format = FORMAT_DEFINITIONS["pptx"]
    assert pptx_format.format_id == "pptx"
    assert pptx_format.extension == ".pptx"
    assert pptx_format.supports_template is True
    assert pptx_format.category == "presentation"


def test_temp_file_manager():
    """TempFileManagerのテスト."""
    manager = TempFileManager()
    
    # コンテキストマネージャーとして使用
    with manager.create_workspace() as temp_dir:
        # ディレクトリが作成されることを確認
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # 一時ディレクトリ内にファイルを作成
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
    
    # コンテキスト終了後、ディレクトリが削除されることを確認
    assert not temp_dir.exists()


@pytest.mark.asyncio
async def test_list_formats():
    """list_formatsツールのテスト."""
    from src.tools.formats import list_formats
    
    formats = await list_formats()
    
    # フォーマットリストが空でないことを確認
    assert len(formats) > 0
    
    # pptx形式が含まれることを確認
    pptx_found = False
    for fmt in formats:
        if fmt["format_id"] == "pptx":
            pptx_found = True
            assert fmt["supports_template"] is True
            break
    
    assert pptx_found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
