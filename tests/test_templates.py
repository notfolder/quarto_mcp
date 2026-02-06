"""テンプレート機能のテストケース."""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.core.template_manager import (
    TemplateManager,
    TemplateNotFoundError,
    InvalidTemplateUrlError,
)


@pytest.mark.asyncio
async def test_template_manager_no_template():
    """テンプレート指定なしのテスト."""
    manager = TemplateManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # テンプレート未指定の場合、Noneが返ることを確認
        result = await manager.resolve_template(None, "pptx", temp_path)
        assert result is None
        
        # pptx以外の形式では常にNone
        result = await manager.resolve_template("some_id", "html", temp_path)
        assert result is None


@pytest.mark.asyncio
async def test_template_manager_invalid_url():
    """不正なURLのテスト."""
    manager = TemplateManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 不正なスキーム
        with pytest.raises(InvalidTemplateUrlError):
            await manager.resolve_template("ftp://example.com/template.pptx", "pptx", temp_path)
        
        # .pptx以外の拡張子
        with pytest.raises(InvalidTemplateUrlError):
            await manager.resolve_template("https://example.com/template.docx", "pptx", temp_path)


def test_template_manager_load_config():
    """設定ファイルからのテンプレート読み込みテスト."""
    # 一時的な設定ファイルを作成
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_file = temp_path / "templates.yaml"
        
        # テンプレートファイルを作成
        template_file = temp_path / "test_template.pptx"
        template_file.write_text("dummy pptx content")
        
        # 設定ファイルを作成
        config = {
            "templates": {
                "test_template": {
                    "path": str(template_file),
                    "description": "Test template"
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # TemplateManagerを初期化
        manager = TemplateManager(config_path=config_file)
        
        # テンプレートが読み込まれていることを確認
        assert "test_template" in manager.templates
        assert manager.templates["test_template"] == str(template_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
