"""Mermaidバリデーションの統括クラス."""

import time
from typing import List, Dict, Any, Optional

from src.validators.mermaid_extractor import MermaidExtractor
from src.validators.mermaid_cli import MermaidCliValidator
from src.validators.regex_validator import RegexValidator
from src.models.validation_schemas import (
    MermaidValidationResponse,
    MermaidBlockResult,
    UnblockedIssue,
    ValidationMetadata,
)


class MermaidValidator:
    """Mermaidバリデーションの統括クラス."""
    
    def __init__(self):
        """初期化."""
        self.extractor = MermaidExtractor()
        self.cli_validator = MermaidCliValidator()
        self.regex_validator = RegexValidator()
    
    def is_cli_available(self) -> bool:
        """
        Mermaid CLIが利用可能かどうかを返す.
        
        Returns:
            利用可能な場合True
        """
        return self.cli_validator.is_available()
    
    async def validate(self, content: str, strict_mode: bool = False) -> MermaidValidationResponse:
        """
        Quarto Markdown内のMermaidコードブロックを検証する.
        
        多層バリデーション方式:
        1. 正規表現ベース検証（2段階ハイブリッド）
        2. Mermaid CLI検証（mmdc）
        
        Args:
            content: Quarto Markdown形式のコンテンツ
            strict_mode: 厳密モード（警告もエラーとして扱う）
            
        Returns:
            バリデーション結果
            
        Raises:
            RuntimeError: Mermaid CLIが未インストールの場合
        """
        start_time = time.time()
        
        # Mermaid CLIの利用可能性チェック（必須要件）
        if not self.is_cli_available():
            raise RuntimeError(
                "Mermaid CLI is not installed. "
                "Please install it with: npm install -g @mermaid-js/mermaid-cli"
            )
        
        # Mermaidコードブロックを抽出
        blocks = self.extractor.extract_mermaid_blocks(content)
        
        # 不正記法を検出（2段階ハイブリッド方式）
        malformed_issues = self.extractor.detect_malformed_blocks(content)
        
        # 各ブロックをバリデーション（多層検証）
        results = []
        valid_count = 0
        invalid_count = 0
        
        for block in blocks:
            block_result = await self._validate_block(block, strict_mode)
            results.append(block_result)
            
            if block_result.is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        # 不正記法の問題を変換
        unblocked_issues = [
            UnblockedIssue(
                line=issue['line'],
                issue_type=issue['issue_type'],
                severity=issue['severity'],
                keyword=issue.get('keyword'),
                pattern=issue.get('pattern'),
                suggestion=issue['suggestion'],
                context=issue['context']
            )
            for issue in malformed_issues
        ]
        
        # 厳密モードの場合、warningもエラーとして扱う
        if strict_mode:
            for issue in unblocked_issues:
                if issue.severity == 'warning':
                    invalid_count += 1
        
        # 全体の成功判定
        success = invalid_count == 0 and len([i for i in unblocked_issues if i.severity == 'error']) == 0
        if strict_mode:
            success = success and len(unblocked_issues) == 0
        
        # 実行時間を計算
        elapsed_time_ms = int((time.time() - start_time) * 1000)
        
        # メタデータを作成
        metadata = ValidationMetadata(
            total_validation_time_ms=elapsed_time_ms,
            mermaid_cli_version=self.cli_validator.get_version()
        )
        
        return MermaidValidationResponse(
            success=success,
            total_blocks=len(blocks),
            valid_blocks=valid_count,
            invalid_blocks=invalid_count,
            results=results,
            unblocked_issues=unblocked_issues,
            validation_engine="mermaid-cli",
            metadata=metadata
        )
    
    async def _validate_block(self, block: Dict[str, Any], strict_mode: bool) -> MermaidBlockResult:
        """
        単一のMermaidコードブロックを多層検証する.
        
        Args:
            block: コードブロック情報
            strict_mode: 厳密モード
            
        Returns:
            ブロックのバリデーション結果
        """
        block_index = block['block_index']
        start_line = block['start_line']
        end_line = block['end_line']
        code = block['code']
        
        # 空のコードブロックチェック
        if not code.strip():
            return MermaidBlockResult(
                block_index=block_index,
                start_line=start_line,
                end_line=end_line,
                is_valid=False,
                diagram_type=None,
                error_message="空のMermaidコードブロック",
                error_line=None,
                warnings=[]
            )
        
        # 多層バリデーション: 全て実行して結果を統合
        
        # 1. 正規表現ベース検証
        regex_result = self.regex_validator.validate(code)
        
        # 2. Mermaid CLI検証
        cli_result = await self.cli_validator.validate(code)
        
        # 結果を統合
        is_valid = regex_result['is_valid'] and cli_result['is_valid']
        diagram_type = cli_result.get('diagram_type') or regex_result.get('diagram_type')
        
        # エラーメッセージの統合（CLI優先）
        error_message = None
        error_line = None
        if not is_valid:
            if not cli_result['is_valid']:
                error_message = cli_result.get('error_message')
                error_line = cli_result.get('error_line')
            elif not regex_result['is_valid']:
                error_message = regex_result.get('error_message')
        
        # 警告の統合
        warnings = []
        warnings.extend(regex_result.get('warnings', []))
        warnings.extend(cli_result.get('warnings', []))
        
        # 厳密モードの場合、警告があればエラー扱い
        if strict_mode and warnings:
            is_valid = False
            if not error_message:
                error_message = f"警告が検出されました: {warnings[0]}"
        
        return MermaidBlockResult(
            block_index=block_index,
            start_line=start_line,
            end_line=end_line,
            is_valid=is_valid,
            diagram_type=diagram_type,
            error_message=error_message,
            error_line=error_line,
            warnings=warnings
        )
