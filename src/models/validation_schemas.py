"""Mermaidバリデーション用スキーマ定義."""

from typing import Optional, List
from pydantic import BaseModel, Field


class MermaidBlockResult(BaseModel):
    """個別のMermaidコードブロックのバリデーション結果."""
    
    block_index: int = Field(description="コードブロックのインデックス（0始まり）")
    start_line: int = Field(description="コードブロック開始行番号（1始まり）")
    end_line: int = Field(description="コードブロック終了行番号（1始まり）")
    is_valid: bool = Field(description="バリデーション結果の真偽値")
    diagram_type: Optional[str] = Field(default=None, description="ダイアグラムタイプ（graph、flowchart等）")
    error_message: Optional[str] = Field(default=None, description="エラーメッセージ")
    error_line: Optional[int] = Field(default=None, description="エラー発生行番号（コードブロック内の相対行番号）")
    warnings: List[str] = Field(default_factory=list, description="警告メッセージのリスト")


class UnblockedIssue(BaseModel):
    """コードブロック外のMermaid記法検出結果."""
    
    line: int = Field(description="検出された行番号（1始まり）")
    issue_type: str = Field(description="問題のタイプ（unblocked, malformed, typo, unclosed）")
    severity: str = Field(description="重大度（error, warning）")
    keyword: Optional[str] = Field(default=None, description="検出されたキーワード")
    pattern: Optional[str] = Field(default=None, description="検出されたパターン")
    suggestion: str = Field(description="修正提案メッセージ")
    context: str = Field(description="該当行のテキスト（前後トリミング済み）")


class ValidationMetadata(BaseModel):
    """バリデーションメタデータ."""
    
    total_validation_time_ms: int = Field(description="バリデーション実行時間（ミリ秒）")
    mermaid_cli_version: Optional[str] = Field(default=None, description="Mermaid CLIバージョン")


class MermaidValidationResponse(BaseModel):
    """Mermaidバリデーション全体のレスポンス."""
    
    success: bool = Field(description="全体の成功フラグ")
    total_blocks: int = Field(description="検出されたMermaidブロック数")
    valid_blocks: int = Field(description="有効なブロック数")
    invalid_blocks: int = Field(description="無効なブロック数")
    results: List[MermaidBlockResult] = Field(description="各ブロックの詳細結果リスト")
    unblocked_issues: List[UnblockedIssue] = Field(description="コードブロック外の問題リスト")
    validation_engine: str = Field(description="使用したバリデーションエンジン名")
    metadata: ValidationMetadata = Field(description="メタデータ")
