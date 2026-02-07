"""Mermaidバリデーション機能のテスト."""

import pytest
from src.validators.mermaid_extractor import MermaidExtractor
from src.validators.regex_validator import RegexValidator


class TestMermaidExtractor:
    """MermaidExtractorのテストクラス."""
    
    def setup_method(self):
        """各テストメソッドの前に実行される."""
        self.extractor = MermaidExtractor()
    
    def test_extract_quarto_extended_syntax(self):
        """Quarto拡張記法のMermaidブロックを正しく抽出できること."""
        content = """# テストスライド

```{mermaid}
graph TD
    A --> B
```

通常のテキスト
"""
        blocks = self.extractor.extract_mermaid_blocks(content)
        
        assert len(blocks) == 1
        assert blocks[0]['block_index'] == 0
        assert blocks[0]['start_line'] == 3
        assert blocks[0]['end_line'] == 6
        assert 'graph TD' in blocks[0]['code']
        assert 'A --> B' in blocks[0]['code']
    
    def test_extract_standard_markdown_syntax(self):
        """標準Markdown記法のMermaidブロックを正しく抽出できること."""
        content = """# テストスライド

```mermaid
flowchart LR
    Start --> End
```
"""
        blocks = self.extractor.extract_mermaid_blocks(content)
        
        assert len(blocks) == 1
        assert blocks[0]['start_line'] == 3
        assert blocks[0]['end_line'] == 6
        assert 'flowchart LR' in blocks[0]['code']
    
    def test_extract_multiple_blocks(self):
        """複数のMermaidブロックを抽出できること."""
        content = """# テスト

```{mermaid}
graph TD
    A --> B
```

## セクション2

```mermaid
sequenceDiagram
    Alice->>Bob: Hello
```
"""
        blocks = self.extractor.extract_mermaid_blocks(content)
        
        assert len(blocks) == 2
        assert blocks[0]['block_index'] == 0
        assert blocks[1]['block_index'] == 1
        assert 'graph TD' in blocks[0]['code']
        assert 'sequenceDiagram' in blocks[1]['code']
    
    def test_detect_typo_patterns(self):
        """スペルミスパターンを検出できること."""
        content = """# テスト

```mermiad
graph TD
    A --> B
```
"""
        issues = self.extractor.detect_malformed_blocks(content)
        
        # スペルミスが検出されること
        typo_issues = [i for i in issues if i['issue_type'] == 'typo']
        assert len(typo_issues) > 0
        assert typo_issues[0]['severity'] == 'error'
        assert typo_issues[0]['line'] == 3
    
    def test_detect_unclosed_block(self):
        """未閉鎖のコードブロックを検出できること."""
        content = """# テスト

```{mermaid}
graph TD
    A --> B
"""
        issues = self.extractor.detect_malformed_blocks(content)
        
        # 未閉鎖エラーが検出されること
        unclosed_issues = [i for i in issues if i['issue_type'] == 'unclosed']
        assert len(unclosed_issues) > 0
        assert unclosed_issues[0]['severity'] == 'error'
    
    def test_detect_unblocked_keyword(self):
        """コードブロック外のMermaidキーワードを検出できること."""
        content = """# テスト

graph TD
    A --> B

```{mermaid}
flowchart LR
    A --> B
```
"""
        issues = self.extractor.detect_malformed_blocks(content)
        
        # コードブロック外のキーワードが警告として検出されること
        unblocked_issues = [i for i in issues if i['issue_type'] == 'unblocked']
        assert len(unblocked_issues) > 0
        assert unblocked_issues[0]['severity'] == 'warning'
        assert 'graph' in unblocked_issues[0]['keyword']
    
    def test_no_false_positive_for_inline_code(self):
        """インラインコード内のキーワードは検出しないこと."""
        content = """# テスト

本文に`graph TD`というインラインコードがある

```{mermaid}
flowchart LR
    A --> B
```
"""
        issues = self.extractor.detect_malformed_blocks(content)
        
        # インラインコード内のキーワードは除外されるため、
        # unblockedタイプの問題は検出されないはず
        unblocked_issues = [i for i in issues if i['issue_type'] == 'unblocked']
        # インラインコード内のキーワードは除外処理により検出されない
        assert len(unblocked_issues) == 0


class TestRegexValidator:
    """RegexValidatorのテストクラス."""
    
    def setup_method(self):
        """各テストメソッドの前に実行される."""
        self.validator = RegexValidator()
    
    def test_valid_graph_diagram(self):
        """有効なgraphダイアグラムを検証できること."""
        code = """graph TD
    A --> B
    B --> C"""
        
        result = self.validator.validate(code)
        
        assert result['is_valid'] is True
        assert result['diagram_type'] == 'graph'
    
    def test_valid_flowchart_diagram(self):
        """有効なflowchartダイアグラムを検証できること."""
        code = """flowchart LR
    Start --> Process --> End"""
        
        result = self.validator.validate(code)
        
        assert result['is_valid'] is True
        assert result['diagram_type'] == 'flowchart'
    
    def test_empty_code(self):
        """空のコードはエラーとして検出されること."""
        code = ""
        
        result = self.validator.validate(code)
        
        assert result['is_valid'] is False
        assert result['error_message'] is not None
    
    def test_no_diagram_type(self):
        """ダイアグラムタイプがない場合はエラーとして検出されること."""
        code = "A --> B"
        
        result = self.validator.validate(code)
        
        assert result['is_valid'] is False
        assert 'ダイアグラムタイプ' in result['error_message']
    
    def test_unmatched_quotes(self):
        """引用符が対応していない場合はエラーとして検出されること."""
        code = """graph TD
    A["Unclosed quote]"""
        
        result = self.validator.validate(code)
        
        assert result['is_valid'] is False
        assert '引用符' in result['error_message']
    
    def test_unmatched_brackets(self):
        """括弧が対応していない場合はエラーとして検出されること."""
        code = """graph TD
    A[Open bracket"""
        
        result = self.validator.validate(code)
        
        assert result['is_valid'] is False
        assert '括弧' in result['error_message']


class TestMermaidExtractorEdgeCases:
    """MermaidExtractorのエッジケーステスト."""
    
    def setup_method(self):
        """各テストメソッドの前に実行される."""
        self.extractor = MermaidExtractor()
    
    def test_empty_content(self):
        """空のコンテンツを処理できること."""
        content = ""
        blocks = self.extractor.extract_mermaid_blocks(content)
        
        assert len(blocks) == 0
    
    def test_no_mermaid_blocks(self):
        """Mermaidブロックがない場合は空リストを返すこと."""
        content = """# テスト

通常のテキストのみ

```python
print("Hello")
```
"""
        blocks = self.extractor.extract_mermaid_blocks(content)
        
        assert len(blocks) == 0
    
    def test_nested_code_block_in_string(self):
        """文字列内のコードブロックは除外されること."""
        content = """# テスト

```{mermaid}
graph TD
    A["コードブロック```を含む文字列"]
```
"""
        blocks = self.extractor.extract_mermaid_blocks(content)
        
        # 正しくブロックが1つ抽出されること
        assert len(blocks) == 1
