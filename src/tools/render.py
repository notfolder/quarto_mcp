"""
quarto_render MCPツールの実装
"""
import asyncio
from typing import Dict, Any
from datetime import datetime

from ..core.renderer import QuartoRenderer, QuartoRenderError
from ..models.schemas import RenderRequest, RenderSuccess, RenderError, ErrorDetail
from ..models.formats import SUPPORTED_FORMATS


async def quarto_render(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Quarto Markdownを指定形式に変換するMCPツール
    
    Args:
        arguments: MCPツール呼び出し時の引数
            - content: Quarto Markdown文字列（必須）
            - format: 出力形式ID（必須）
            - output_path: 出力ファイルの絶対パス（必須）
            - template: テンプレートIDまたはパス（任意）
            - format_options: 形式固有オプション（任意）
    
    Returns:
        変換結果を含む辞書（RenderSuccessまたはRenderError）
    """
    try:
        # リクエストパラメータを検証
        request = RenderRequest(**arguments)
        
        # レンダラーを初期化
        renderer = QuartoRenderer()
        
        # 変換を実行
        result = await renderer.render(
            content=request.content,
            format=request.format,
            output_path=request.output_path,
            template=request.template,
            format_options=request.format_options
        )
        
        # 成功レスポンスを返却
        return result.model_dump()
        
    except QuartoRenderError as e:
        # Quarto変換エラー
        error_detail = ErrorDetail(
            code="RENDER_FAILED",
            message="Quarto render failed",
            details=str(e),
            quarto_stderr=_extract_stderr(str(e)),
            timestamp=datetime.now().isoformat()
        )
        error_response = RenderError(error=error_detail)
        return error_response.model_dump()
        
    except ValueError as e:
        # 入力検証エラー
        error_detail = ErrorDetail(
            code="INVALID_INPUT",
            message="Invalid input parameters",
            details=str(e),
            timestamp=datetime.now().isoformat()
        )
        error_response = RenderError(error=error_detail)
        return error_response.model_dump()
        
    except Exception as e:
        # その他のエラー
        error_detail = ErrorDetail(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details=str(e),
            timestamp=datetime.now().isoformat()
        )
        error_response = RenderError(error=error_detail)
        return error_response.model_dump()


def _extract_stderr(error_message: str) -> str:
    """
    エラーメッセージからQuartoの標準エラー出力を抽出
    
    Args:
        error_message: エラーメッセージ文字列
        
    Returns:
        標準エラー出力部分、または元のメッセージ
    """
    # "stderr:"の後の部分を抽出
    if "stderr:" in error_message:
        parts = error_message.split("stderr:", 1)
        if len(parts) > 1:
            stderr_part = parts[1].split("stdout:", 1)[0]
            return stderr_part.strip()
    
    return error_message


# ツール定義（MCP Server登録用）
TOOL_DEFINITION = {
    "name": "quarto_render",
    "description": (
        "Quarto Markdownを指定形式（PowerPoint、PDF、HTML等）に変換します。"
        "特にPowerPoint出力ではカスタムテンプレートを使用できます。"
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "Quarto Markdown形式の文字列コンテンツ"
            },
            "format": {
                "type": "string",
                "enum": SUPPORTED_FORMATS,
                "description": (
                    f"出力形式ID。サポート形式: {', '.join(SUPPORTED_FORMATS)}。"
                    "推奨: pptx（PowerPoint）"
                )
            },
            "output_path": {
                "type": "string",
                "description": "出力ファイルを生成する絶対パス"
            },
            "template": {
                "type": "string",
                "description": (
                    "PowerPoint形式でのカスタムテンプレート指定（任意）。"
                    "テンプレートIDまたはテンプレートファイルの絶対パスを指定。"
                    "format='pptx'の場合のみ有効。"
                )
            },
            "format_options": {
                "type": "object",
                "description": (
                    "出力形式固有のオプション設定（任意）。"
                    "Quarto YAMLヘッダー相当の設定を指定可能。"
                    "例: {\"toc\": true, \"number-sections\": true}"
                ),
                "additionalProperties": True
            }
        },
        "required": ["content", "format", "output_path"]
    }
}
