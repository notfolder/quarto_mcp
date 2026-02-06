"""quarto_list_formats MCPツールの実装."""

from src.models.formats import FORMAT_DEFINITIONS, FormatInfo
from typing import List, Dict, Any


async def list_formats() -> List[Dict[str, Any]]:
    """
    サポートされている出力形式の一覧を取得する.
    
    Returns:
        出力形式情報のリスト
    """
    formats = []
    
    for format_info in FORMAT_DEFINITIONS.values():
        formats.append({
            "format_id": format_info.format_id,
            "description": format_info.description,
            "extension": format_info.extension,
            "mime_type": format_info.mime_type,
            "category": format_info.category,
            "supports_template": format_info.supports_template,
        })
    
    return formats
