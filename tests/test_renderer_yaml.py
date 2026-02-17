"""QuartoRendererのYAML処理のテスト."""

import pytest
from src.core.renderer import QuartoRenderer


class TestQuartoRendererYAMLHandling:
    """QuartoRendererのYAML処理テストクラス."""
    
    def test_extract_yaml_header_no_yaml(self):
        """YAMLヘッダーがない場合のテスト."""
        renderer = QuartoRenderer()
        
        content = "# Title\n\nSome content here."
        yaml_dict, body = renderer._extract_yaml_header(content)
        
        # YAMLヘッダーがない場合はNoneと元のコンテンツが返る
        assert yaml_dict is None
        assert body == content
    
    def test_extract_yaml_header_with_valid_yaml(self):
        """有効なYAMLヘッダーがある場合のテスト."""
        renderer = QuartoRenderer()
        
        content = """---
title: Test Document
format: pptx
---

# Content"""
        
        yaml_dict, body = renderer._extract_yaml_header(content)
        
        assert yaml_dict is not None
        assert isinstance(yaml_dict, dict)
        assert yaml_dict["title"] == "Test Document"
        assert yaml_dict["format"] == "pptx"
        assert body.strip() == "# Content"
    
    def test_extract_yaml_header_with_empty_yaml(self):
        """空のYAMLヘッダーがある場合のテスト."""
        renderer = QuartoRenderer()
        
        # 空のYAMLヘッダーは---の間に空行がある形式
        content = """---

---

# Content"""
        
        yaml_dict, body = renderer._extract_yaml_header(content)
        
        # 空のYAMLは空辞書として返る
        assert yaml_dict == {}
        assert body.strip() == "# Content"
    
    def test_extract_yaml_header_with_string_yaml(self):
        """文字列型のYAML（不正）がある場合のテスト."""
        renderer = QuartoRenderer()
        
        content = """---
just a string
---

# Content"""
        
        yaml_dict, body = renderer._extract_yaml_header(content)
        
        # 文字列型YAMLは空辞書として返る
        assert yaml_dict == {}
        assert body.strip() == "# Content"
    
    def test_merge_yaml_headers_with_none(self):
        """existing_yamlがNoneの場合のテスト."""
        renderer = QuartoRenderer()
        
        result = renderer._merge_yaml_headers(
            existing_yaml=None,
            format_id="pptx",
            format_options={},
            template_path=None
        )
        
        # Noneの場合も正しく空辞書から生成される
        assert isinstance(result, dict)
        assert "pptx" in result
    
    def test_merge_yaml_headers_with_empty_dict(self):
        """existing_yamlが空辞書の場合のテスト."""
        renderer = QuartoRenderer()
        
        result = renderer._merge_yaml_headers(
            existing_yaml={},
            format_id="pptx",
            format_options={},
            template_path=None
        )
        
        assert isinstance(result, dict)
        assert "pptx" in result
    
    def test_merge_yaml_headers_with_valid_dict(self):
        """existing_yamlが有効な辞書の場合のテスト."""
        renderer = QuartoRenderer()
        
        result = renderer._merge_yaml_headers(
            existing_yaml={"title": "Test", "author": "Someone"},
            format_id="pptx",
            format_options={"slide-level": 2},
            template_path="/path/to/template.pptx"
        )
        
        # 既存のキーが保持される
        assert result["title"] == "Test"
        assert result["author"] == "Someone"
        
        # 新しいフォーマット設定が追加される
        assert "pptx" in result
        assert result["pptx"]["slide-level"] == 2
        assert result["pptx"]["reference-doc"] == "/path/to/template.pptx"
