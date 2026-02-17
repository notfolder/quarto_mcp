"""quarto_render MCPツールの実装."""

from pathlib import Path
from typing import Optional, Dict, Any

from src.core.renderer import QuartoRenderer, QuartoRenderError
from src.core.template_manager import (
    TemplateError,
    TemplateNotFoundError,
    TemplateDownloadError,
    TemplateDownloadTimeoutError,
    TemplateSizeExceededError,
    InvalidTemplateUrlError,
)
from src.models.schemas import RenderResult, ErrorResponse, ErrorInfo


async def render(
    content: str,
    format: str,
    output_filename: str,
    template: Optional[str] = None,
    format_options: Optional[Dict[str, Any]] = None,
    config_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Quarto Markdownを指定形式に変換する.
    
    Args:
        content: Quarto Markdown形式の文字列
        format: 出力形式ID
        output_filename: 出力ファイル名
        template: テンプレート指定（IDまたはURL）
        format_options: 出力形式固有のオプション設定
        config_path: テンプレート設定ファイルのパス
        
    Returns:
        変換結果（成功時はRenderResult、失敗時はErrorResponse）
    """
    if format_options is None:
        format_options = {}
    
    try:
        # レンダラーを初期化
        renderer = QuartoRenderer(config_path=config_path)
        
        # 変換を実行
        result = await renderer.render(
            content=content,
            format_id=format,
            output_filename=output_filename,
            template=template,
            format_options=format_options,
        )
        
        # 成功レスポンスを返す
        return result.model_dump()
        
    except TemplateNotFoundError as e:
        # テンプレートが見つからない
        error_response = ErrorResponse(
            success=False,
            error=ErrorInfo(
                code="TEMPLATE_NOT_FOUND",
                message=str(e),
                details=f"The specified template was not found. Please check the template ID or URL: {template}",
            )
        )
        return error_response.model_dump()
        
    except InvalidTemplateUrlError as e:
        # 不正なURL
        error_response = ErrorResponse(
            success=False,
            error=ErrorInfo(
                code="INVALID_TEMPLATE_URL",
                message=str(e),
                details="The template URL is invalid. Please provide a valid HTTP or HTTPS URL pointing to a .pptx file.",
            )
        )
        return error_response.model_dump()
        
    except TemplateSizeExceededError as e:
        # ファイルサイズ超過
        error_response = ErrorResponse(
            success=False,
            error=ErrorInfo(
                code="TEMPLATE_SIZE_EXCEEDED",
                message=str(e),
                details="The template file is too large. Maximum allowed size is 50MB.",
            )
        )
        return error_response.model_dump()
        
    except TemplateDownloadTimeoutError as e:
        # ダウンロードタイムアウト
        error_response = ErrorResponse(
            success=False,
            error=ErrorInfo(
                code="TEMPLATE_DOWNLOAD_TIMEOUT",
                message=str(e),
                details="Template download timed out. Please check the URL and try again.",
            )
        )
        return error_response.model_dump()
        
    except TemplateDownloadError as e:
        # ダウンロード失敗
        error_response = ErrorResponse(
            success=False,
            error=ErrorInfo(
                code="TEMPLATE_DOWNLOAD_FAILED",
                message=str(e),
                details="Failed to download the template from the URL. Please check the URL and network connection.",
            )
        )
        return error_response.model_dump()
        
    except TemplateError as e:
        # その他のテンプレートエラー
        error_response = ErrorResponse(
            success=False,
            error=ErrorInfo(
                code="TEMPLATE_ERROR",
                message=str(e),
                details="An error occurred while processing the template.",
            )
        )
        return error_response.model_dump()
        
    except QuartoRenderError as e:
        # Quarto変換エラー
        error_response = ErrorResponse(
            success=False,
            error=ErrorInfo(
                code=e.code,
                message=str(e),
                details=f"Quarto rendering failed. Please check the input content and format.",
                quarto_stderr=e.stderr,
            )
        )
        return error_response.model_dump()
        
    except Exception as e:
        # その他のエラー
        error_response = ErrorResponse(
            success=False,
            error=ErrorInfo(
                code="UNKNOWN_ERROR",
                message=f"An unexpected error occurred: {str(e)}",
                details="An unexpected error occurred during rendering. Please check the logs for more information.",
            )
        )
        return error_response.model_dump()
