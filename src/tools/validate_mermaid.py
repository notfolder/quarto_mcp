"""quarto_validate_mermaid MCPツールの実装."""

from typing import Dict, Any

from src.validators.mermaid_validator import MermaidValidator
from src.models.schemas import ErrorResponse, ErrorInfo


async def validate_mermaid(
    content: str,
    strict_mode: bool = False,
) -> Dict[str, Any]:
    """
    Quarto Markdown内のMermaidコードブロックをバリデーションする.
    
    このツールは独立した事前検証ツールであり、quarto_renderとは別に
    明示的に呼び出される必要がある。
    
    Args:
        content: Quarto Markdown形式の文字列
        strict_mode: 厳密モード（警告もエラーとして扱う）デフォルト: False
        
    Returns:
        バリデーション結果（成功時はMermaidValidationResponse、失敗時はErrorResponse）
    """
    try:
        # バリデータを初期化
        validator = MermaidValidator()
        
        # バリデーション実行
        result = await validator.validate(
            content=content,
            strict_mode=strict_mode,
        )
        
        # 成功レスポンスを返す
        return result.model_dump()
        
    except RuntimeError as e:
        # Mermaid CLI未インストールエラー
        error_response = ErrorResponse(
            success=False,
            error=ErrorInfo(
                code="MERMAID_CLI_NOT_FOUND",
                message=str(e),
                details=(
                    "Mermaid CLI (mmdc) is required for validation. "
                    "Please install it with:\n"
                    "npm install -g @mermaid-js/mermaid-cli"
                ),
            )
        )
        return error_response.model_dump()
        
    except Exception as e:
        # その他のエラー
        error_response = ErrorResponse(
            success=False,
            error=ErrorInfo(
                code="VALIDATION_ERROR",
                message=f"An unexpected error occurred during validation: {str(e)}",
                details="Please check the content and try again.",
            )
        )
        return error_response.model_dump()
