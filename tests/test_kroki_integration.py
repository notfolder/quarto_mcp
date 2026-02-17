"""Kroki統合機能のユニットテスト."""

import os
import pytest
from src.converters.kroki_converter import KrokiConverter
from src.managers.yaml_frontmatter_manager import YAMLFrontmatterManager


class TestKrokiConverter:
    """KrokiConverterクラスのテストクラス."""
    
    def test_convert_quarto_syntax_with_png(self):
        """Quarto拡張記法がPNG形式でKroki記法に変換されることをテスト."""
        converter = KrokiConverter(format_id="pptx", image_format="png")
        
        content = """```{mermaid}
graph LR
    A --> B
```"""
        
        result = converter.convert(content)
        
        assert "```{kroki-mermaid-png}" in result
        assert "graph LR" in result
        assert "A --> B" in result
    
    def test_convert_quarto_syntax_with_svg(self):
        """Quarto拡張記法がSVG形式でKroki記法に変換されることをテスト."""
        converter = KrokiConverter(format_id="html", image_format="svg")
        
        content = """```{mermaid #fig-example}
graph TD
    Start --> End
```"""
        
        result = converter.convert(content)
        
        assert "```{kroki-mermaid-svg #fig-example}" in result
    
    def test_convert_markdown_syntax(self):
        """標準Markdown記法がKroki記法に変換されることをテスト."""
        # image_format=Noneでも、format_idがpptxなので自動的にpngが選択される
        converter = KrokiConverter(format_id="pptx", image_format=None)
        
        content = """```mermaid
sequenceDiagram
    Alice->>Bob: Hello
```"""
        
        result = converter.convert(content)
        
        # pptxの場合、自動選択でpngになる
        assert "```{kroki-mermaid-png}" in result
        assert "sequenceDiagram" in result
    
    def test_auto_format_selection_pptx(self):
        """PowerPoint出力時にPNG形式が自動選択されることをテスト."""
        converter = KrokiConverter(format_id="pptx", image_format="auto")
        
        content = "```mermaid\ngraph LR\n```"
        result = converter.convert(content)
        
        assert "```{kroki-mermaid-png}" in result
    
    def test_auto_format_selection_html(self):
        """HTML出力時にSVG形式が自動選択されることをテスト."""
        converter = KrokiConverter(format_id="html", image_format="auto")
        
        content = "```mermaid\ngraph LR\n```"
        result = converter.convert(content)
        
        assert "```{kroki-mermaid-svg}" in result
    
    def test_env_var_override(self, monkeypatch):
        """環境変数が画像形式の指定を上書きすることをテスト."""
        monkeypatch.setenv("QUARTO_MCP_KROKI_IMAGE_FORMAT", "svg")
        
        # pptxは通常pngだが、環境変数でsvgに上書きされる
        converter = KrokiConverter(format_id="pptx", image_format="auto")
        
        content = "```mermaid\ngraph LR\n```"
        result = converter.convert(content)
        
        assert "```{kroki-mermaid-svg}" in result
    
    def test_preserve_cell_options(self):
        """セルオプションが保持されることをテスト."""
        converter = KrokiConverter(format_id="pptx", image_format="png")
        
        content = """```{mermaid #fig-id .class width="80%"}
graph LR
```"""
        
        result = converter.convert(content)
        
        assert "```{kroki-mermaid-png #fig-id .class width=\"80%\"}" in result


class TestYAMLFrontmatterManager:
    """YAMLFrontmatterManagerクラスのテストクラス."""
    
    def test_add_kroki_config_to_empty_yaml(self):
        """空のYAMLにKroki設定が追加されることをテスト."""
        manager = YAMLFrontmatterManager(kroki_service_url="http://kroki:8000")
        
        content = "# Hello\n\nSome content"
        result = manager.add_kroki_config(content)
        
        assert "---" in result
        assert "filters:" in result
        assert "- kroki" in result
        assert "kroki:" in result
        assert "serviceUrl: http://kroki:8000" in result
    
    def test_add_kroki_config_to_string_yaml(self):
        """文字列型のYAML（不正なYAML）を処理できることをテスト."""
        manager = YAMLFrontmatterManager(kroki_service_url="http://kroki:8000")
        
        # YAMLとして文字列が返される場合のテスト
        content = """---
just a string
---

# Content"""
        
        result = manager.add_kroki_config(content)
        
        # エラーにならず、新しいYAMLが生成されること
        assert "filters:" in result
        assert "- kroki" in result
        assert "serviceUrl: http://kroki:8000" in result
    
    def test_add_kroki_config_to_existing_yaml(self):
        """既存のYAMLにKroki設定が追加されることをテスト."""
        manager = YAMLFrontmatterManager(kroki_service_url="http://kroki:8000")
        
        content = """---
title: Test Document
format: pptx
---

# Content"""
        
        result = manager.add_kroki_config(content)
        
        assert "title: Test Document" in result
        assert "format: pptx" in result
        assert "filters:" in result
        assert "- kroki" in result
        assert "serviceUrl: http://kroki:8000" in result
    
    def test_no_duplicate_kroki_filter(self):
        """krokiフィルターが重複して追加されないことをテスト."""
        manager = YAMLFrontmatterManager(kroki_service_url="http://kroki:8000")
        
        content = """---
filters:
  - kroki
---

# Content"""
        
        result = manager.add_kroki_config(content)
        
        # krokiが1回だけ出現することを確認
        assert result.count("- kroki") == 1
    
    def test_preserve_existing_filters(self):
        """既存のフィルターが保持されることをテスト."""
        manager = YAMLFrontmatterManager(kroki_service_url="http://kroki:8000")
        
        content = """---
filters:
  - other-filter
---

# Content"""
        
        result = manager.add_kroki_config(content)
        
        assert "- other-filter" in result
        assert "- kroki" in result
    
    def test_override_service_url(self):
        """serviceUrlが常に上書きされることをテスト."""
        manager = YAMLFrontmatterManager(kroki_service_url="http://new-kroki:9000")
        
        content = """---
kroki:
  serviceUrl: http://old-kroki:8000
---

# Content"""
        
        result = manager.add_kroki_config(content)
        
        assert "serviceUrl: http://new-kroki:9000" in result
        assert "http://old-kroki:8000" not in result


class TestKrokiIntegration:
    """Kroki統合機能の統合テスト."""
    
    def test_full_conversion_flow(self):
        """完全な変換フローのテスト."""
        # 1. Mermaid記法の変換
        converter = KrokiConverter(format_id="pptx", image_format="png")
        content = """---
title: Test
---

```mermaid
graph LR
    A --> B
```"""
        
        content = converter.convert(content)
        
        # 2. YAML設定の追加
        manager = YAMLFrontmatterManager(kroki_service_url="http://kroki:8000")
        result = manager.add_kroki_config(content)
        
        # 検証
        assert "title: Test" in result
        assert "```{kroki-mermaid-png}" in result
        assert "filters:" in result
        assert "- kroki" in result
        assert "serviceUrl: http://kroki:8000" in result
