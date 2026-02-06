"""
MCPツールの入出力スキーマ定義
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class RenderRequest(BaseModel):
    """quarto_renderツールのリクエストパラメータ"""
    content: str = Field(..., description="Quarto Markdown形式の文字列")
    format: str = Field(..., description="出力形式ID（例: pptx, html, pdf）")
    output_path: str = Field(..., description="出力ファイルの絶対パス")
    template: Optional[str] = Field(None, description="テンプレートIDまたはパス（PowerPoint用）")
    format_options: Dict[str, Any] = Field(default_factory=dict, description="形式固有のオプション")


class OutputInfo(BaseModel):
    """出力ファイル情報"""
    path: str = Field(..., description="生成された出力ファイルの絶対パス")
    filename: str = Field(..., description="ファイル名のみ")
    mime_type: str = Field(..., description="MIMEタイプ")
    size_bytes: int = Field(..., description="ファイルサイズ（バイト単位）")


class RenderMetadata(BaseModel):
    """変換メタデータ"""
    quarto_version: str = Field(..., description="使用したQuarto CLIのバージョン")
    render_time_ms: int = Field(..., description="変換処理時間（ミリ秒）")
    warnings: List[str] = Field(default_factory=list, description="警告メッセージのリスト")


class RenderSuccess(BaseModel):
    """成功時のレスポンス"""
    success: bool = Field(True, description="常にTrue")
    format: str = Field(..., description="使用した出力形式ID")
    output: OutputInfo = Field(..., description="出力ファイル情報")
    metadata: RenderMetadata = Field(..., description="変換メタデータ")


class ErrorDetail(BaseModel):
    """エラー詳細情報"""
    code: str = Field(..., description="エラーコード")
    message: str = Field(..., description="エラーの概要メッセージ")
    details: str = Field(..., description="エラーの詳細説明")
    quarto_stderr: Optional[str] = Field(None, description="Quarto CLIの標準エラー出力")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="エラー発生日時")


class RenderError(BaseModel):
    """失敗時のレスポンス"""
    success: bool = Field(False, description="常にFalse")
    error: ErrorDetail = Field(..., description="エラー詳細情報")
