"""Mermaidコードブロック抽出と不正記法検出."""

import re
from typing import List, Dict, Any


class MermaidExtractor:
    """Quarto Markdown内のMermaidコードブロックを抽出し、不正記法を検出する."""
    
    # Mermaidダイアグラムタイプキーワード
    DIAGRAM_KEYWORDS = [
        "graph", "flowchart", "sequenceDiagram", "classDiagram", 
        "stateDiagram", "erDiagram", "gantt", "pie", "gitGraph", 
        "journey", "quadrantChart", "requirementDiagram", "C4Context"
    ]
    
    # スペルミスパターン
    TYPO_PATTERNS = {
        r"```\s*mermiad": "mermiad → mermaid",
        r"```\s*mermeid": "mermeid → mermaid",
        r"```\s*mermad": "mermad → mermaid",
        r"```\s*mermaaid": "mermaaid → mermaid",
        r"```\s*mremaid": "mremaid → mermaid",
        r"```\s*meramid": "meramid → mermaid",
        r"```\s*marmaid": "marmaid → mermaid",
        r"flowchrat": "flowchrat → flowchart",
        r"sequencDiagram": "sequencDiagram → sequenceDiagram",
        r"classDigram": "classDigram → classDiagram",
        r"stateDiagarm": "stateDiagarm → stateDiagram",
    }
    
    # 波括弧の不要なスペースパターン
    BRACE_SPACE_PATTERN = r"```\{\s+mermaid|\}\s+```|```mermaid\s+\}"
    
    def __init__(self):
        """初期化."""
        # キーワード検出用の正規表現パターンを事前コンパイル
        self._keyword_patterns = []
        for keyword in self.DIAGRAM_KEYWORDS:
            pattern = re.compile(rf'(^|\s){re.escape(keyword)}(\s|$)')
            self._keyword_patterns.append((keyword, pattern))
    
    def extract_mermaid_blocks(self, content: str) -> List[Dict[str, Any]]:
        """
        Quarto Markdownから全てのMermaidコードブロックを抽出する.
        
        Args:
            content: Quarto Markdown形式のコンテンツ
            
        Returns:
            抽出されたMermaidブロックのリスト
            各ブロックは以下のキーを持つ辞書:
            - block_index: ブロックのインデックス（0始まり）
            - start_line: 開始行番号（1始まり）
            - end_line: 終了行番号（1始まり）
            - code: Mermaidコード本体（マーカー除く）
        """
        blocks = []
        lines = content.split('\n')
        
        # Quarto拡張記法と標準Markdown記法の両方に対応（先頭の空白も許容）
        pattern = r'^\s*```\{mermaid\}|^\s*```mermaid'
        
        i = 0
        block_index = 0
        while i < len(lines):
            line = lines[i]
            
            # コードブロック開始を検出
            if re.match(pattern, line):
                start_line = i + 1  # 1始まり
                code_lines = []
                i += 1
                
                # コードブロックの終了を探す
                while i < len(lines):
                    if lines[i].strip() == '```':
                        end_line = i + 1  # 1始まり
                        
                        blocks.append({
                            'block_index': block_index,
                            'start_line': start_line,
                            'end_line': end_line,
                            'code': '\n'.join(code_lines)
                        })
                        block_index += 1
                        break
                    else:
                        code_lines.append(lines[i])
                    i += 1
            
            i += 1
        
        return blocks
    
    def detect_malformed_blocks(self, content: str) -> List[Dict[str, Any]]:
        """
        不正な記法を2段階ハイブリッドチェックで検出する.
        
        第1段階: 正規表現による不正パターン検出
        第2段階: コンテキスト検証によるキーワード検出
        
        Args:
            content: Quarto Markdown形式のコンテンツ
            
        Returns:
            検出された問題のリスト
            各問題は以下のキーを持つ辞書:
            - line: 行番号（1始まり）
            - issue_type: 問題タイプ
            - severity: 重大度
            - keyword/pattern: 検出されたキーワードまたはパターン
            - suggestion: 修正提案
            - context: 該当行のテキスト
        """
        issues = []
        lines = content.split('\n')
        
        # 第1段階: 正規表現による不正パターン検出
        issues.extend(self._detect_typos(lines))
        issues.extend(self._detect_brace_spacing(lines))
        issues.extend(self._detect_unclosed_blocks(lines))
        
        # 第2段階: コンテキスト検証によるキーワード検出
        issues.extend(self._detect_unblocked_keywords(lines))
        
        # 重複除去と優先順位付け
        issues = self._merge_duplicate_issues(issues)
        
        return issues
    
    def _detect_typos(self, lines: List[str]) -> List[Dict[str, Any]]:
        """スペルミスパターンを検出する（第1段階）."""
        issues = []
        
        for line_num, line in enumerate(lines, start=1):
            for pattern, suggestion in self.TYPO_PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'line': line_num,
                        'issue_type': 'typo',
                        'severity': 'error',
                        'pattern': pattern,
                        'suggestion': f'スペルミス: {suggestion}',
                        'context': self._trim_context(line)
                    })
        
        return issues
    
    def _detect_brace_spacing(self, lines: List[str]) -> List[Dict[str, Any]]:
        """波括弧の不要なスペースを検出する（第1段階）."""
        issues = []
        
        for line_num, line in enumerate(lines, start=1):
            if re.search(self.BRACE_SPACE_PATTERN, line):
                issues.append({
                    'line': line_num,
                    'issue_type': 'malformed',
                    'severity': 'error',
                    'pattern': 'brace_spacing',
                    'suggestion': '波括弧内のスペースを削除してください: ```{mermaid}',
                    'context': self._trim_context(line)
                })
        
        return issues
    
    def _detect_unclosed_blocks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """未閉鎖のコードブロックを検出する（第1段階）."""
        issues = []
        open_blocks = []
        
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            # コードブロック開始
            if re.match(r'^```\{mermaid\}|^```mermaid', stripped):
                open_blocks.append(line_num)
            # コードブロック終了
            elif stripped == '```' and open_blocks:
                open_blocks.pop()
        
        # 未閉鎖のブロックが残っている
        for line_num in open_blocks:
            issues.append({
                'line': line_num,
                'issue_type': 'unclosed',
                'severity': 'error',
                'pattern': 'unclosed_block',
                'suggestion': 'コードブロックが閉じられていません。```で終了してください',
                'context': self._trim_context(lines[line_num - 1])
            })
        
        return issues
    
    def _detect_unblocked_keywords(self, lines: List[str]) -> List[Dict[str, Any]]:
        """コードブロック外のMermaidキーワードを検出する（第2段階）."""
        issues = []
        in_code_block = False
        in_mermaid_block = False
        reported_lines = set()  # 1行につき1回のみ報告
        
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            # コードブロックの状態管理
            if stripped.startswith('```'):
                if not in_code_block:
                    # コードブロック開始
                    in_code_block = True
                    in_mermaid_block = 'mermaid' in stripped
                else:
                    # コードブロック終了
                    in_code_block = False
                    in_mermaid_block = False
                continue
            
            # コードブロック外の行をチェック
            if not in_code_block and line_num not in reported_lines:
                # インラインコード（バッククォート1つ）を除外
                cleaned_line = re.sub(r'`[^`]+`', '', line)
                
                # Mermaidダイアグラムキーワードをチェック
                for keyword, pattern in self._keyword_patterns:
                    # 事前コンパイル済みのパターンを使用
                    if pattern.search(cleaned_line):
                        issues.append({
                            'line': line_num,
                            'issue_type': 'unblocked',
                            'severity': 'warning',
                            'keyword': keyword,
                            'suggestion': f'Mermaidキーワード "{keyword}" がコードブロック外にあります。コードブロックで囲んでください。',
                            'context': self._trim_context(line)
                        })
                        reported_lines.add(line_num)
                        break  # 1行につき1つの警告のみ
                
                # Mermaid構文要素（矢印記号など）をチェック
                if line_num not in reported_lines:
                    arrow_pattern = r'(-->)'
                    if re.search(arrow_pattern, cleaned_line):
                        issues.append({
                            'line': line_num,
                            'issue_type': 'unblocked',
                            'severity': 'warning',
                            'keyword': 'arrow',
                            'suggestion': 'Mermaid構文要素（矢印）がコードブロック外にあります。',
                            'context': self._trim_context(line)
                        })
                        reported_lines.add(line_num)
        
        return issues
    
    def _merge_duplicate_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重複する問題をマージし、優先順位付けする.
        
        同一行でerrorとwarningが両方検出された場合、errorを優先。
        """
        # 行番号でグループ化
        by_line = {}
        for issue in issues:
            line = issue['line']
            if line not in by_line:
                by_line[line] = []
            by_line[line].append(issue)
        
        # 各行について、errorがあればwarningを除外
        merged = []
        for line, line_issues in by_line.items():
            has_error = any(issue['severity'] == 'error' for issue in line_issues)
            if has_error:
                # errorのみ残す
                merged.extend([issue for issue in line_issues if issue['severity'] == 'error'])
            else:
                # warningを全て残す
                merged.extend(line_issues)
        
        return merged
    
    def _trim_context(self, text: str, max_length: int = 80) -> str:
        """コンテキストテキストを指定長に切り詰める."""
        text = text.strip()
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'
