"""正規表現ベースのMermaidバリデータ."""

import re
from typing import List, Dict, Any


class RegexValidator:
    """正規表現ベースのMermaid構文検証."""
    
    # 対応ダイアグラムタイプキーワード
    DIAGRAM_KEYWORDS = [
        "graph", "flowchart", "sequenceDiagram", "classDiagram",
        "stateDiagram", "erDiagram", "gantt", "pie", "gitGraph",
        "journey", "quadrantChart", "requirementDiagram", "C4Context"
    ]
    
    def __init__(self):
        """初期化."""
        pass
    
    def validate(self, mermaid_code: str) -> Dict[str, Any]:
        """
        正規表現ベースでMermaidコードを検証する.
        
        これは簡易的な検証で、Mermaid CLI検証と並行して実行される。
        
        Args:
            mermaid_code: Mermaidダイアグラムコード
            
        Returns:
            バリデーション結果の辞書:
            - is_valid: バリデーション結果
            - diagram_type: ダイアグラムタイプ
            - error_message: エラーメッセージ（失敗時）
            - warnings: 警告メッセージのリスト
        """
        warnings = []
        
        # ダイアグラムタイプを検出
        diagram_type = self._detect_diagram_type(mermaid_code)
        
        if not diagram_type:
            return {
                'is_valid': False,
                'diagram_type': None,
                'error_message': 'ダイアグラムタイプが検出できません',
                'warnings': warnings
            }
        
        # 空のコードをチェック
        if not mermaid_code.strip():
            return {
                'is_valid': False,
                'diagram_type': None,
                'error_message': '空のMermaidコードブロック',
                'warnings': warnings
            }
        
        # 基本的な構文チェック
        issues = self._check_basic_syntax(mermaid_code, diagram_type)
        
        if issues:
            # 最初の問題をエラーメッセージとして返す
            return {
                'is_valid': False,
                'diagram_type': diagram_type,
                'error_message': issues[0],
                'warnings': warnings
            }
        
        # 警告レベルの問題をチェック
        warnings.extend(self._check_warnings(mermaid_code, diagram_type))
        
        return {
            'is_valid': True,
            'diagram_type': diagram_type,
            'warnings': warnings
        }
    
    def _detect_diagram_type(self, mermaid_code: str) -> str:
        """
        ダイアグラムタイプを検出する.
        
        Args:
            mermaid_code: Mermaidコード
            
        Returns:
            ダイアグラムタイプ、検出できない場合は空文字列
        """
        # 最初の非空行・非コメント行からダイアグラムタイプを抽出
        for line in mermaid_code.split('\n'):
            line = line.strip()
            if line and not line.startswith('%%'):
                for keyword in self.DIAGRAM_KEYWORDS:
                    if line.startswith(keyword):
                        return keyword
                break
        
        return ""
    
    def _check_basic_syntax(self, mermaid_code: str, diagram_type: str) -> List[str]:
        """
        基本的な構文チェックを実行する.
        
        Args:
            mermaid_code: Mermaidコード
            diagram_type: ダイアグラムタイプ
            
        Returns:
            エラーメッセージのリスト
        """
        issues = []
        
        # 引用符の対応をチェック
        quote_issues = self._check_quote_matching(mermaid_code)
        issues.extend(quote_issues)
        
        # 括弧の対応をチェック
        bracket_issues = self._check_bracket_matching(mermaid_code)
        issues.extend(bracket_issues)
        
        return issues
    
    def _check_quote_matching(self, mermaid_code: str) -> List[str]:
        """引用符の対応をチェックする."""
        issues = []
        
        for line_num, line in enumerate(mermaid_code.split('\n'), start=1):
            # ダブルクォートのカウント
            double_quotes = line.count('"')
            if double_quotes % 2 != 0:
                issues.append(f'行 {line_num}: 引用符が対応していません')
            
            # シングルクォートのカウント
            single_quotes = line.count("'")
            if single_quotes % 2 != 0:
                issues.append(f'行 {line_num}: 引用符が対応していません')
        
        return issues
    
    def _check_bracket_matching(self, mermaid_code: str) -> List[str]:
        """括弧の対応をチェックする."""
        issues = []
        
        # 全体の括弧の対応をチェック
        brackets = {'[': 0, '{': 0, '(': 0}
        closing = {']': '[', '}': '{', ')': '('}
        
        for char in mermaid_code:
            if char in brackets:
                brackets[char] += 1
            elif char in closing:
                opening = closing[char]
                brackets[opening] -= 1
                if brackets[opening] < 0:
                    issues.append(f'閉じ括弧 "{char}" に対応する開き括弧がありません')
                    brackets[opening] = 0  # リセット
        
        # 未閉鎖の開き括弧をチェック
        for bracket, count in brackets.items():
            if count > 0:
                issues.append(f'開き括弧 "{bracket}" が閉じられていません')
        
        return issues
    
    def _check_warnings(self, mermaid_code: str, diagram_type: str) -> List[str]:
        """警告レベルの問題をチェックする."""
        warnings = []
        
        # スタイル定義の警告（一部のバージョンでサポートされない可能性）
        if 'style ' in mermaid_code or 'classDef ' in mermaid_code:
            warnings.append('スタイル定義が含まれています（一部のバージョンでサポートされない可能性があります）')
        
        return warnings
