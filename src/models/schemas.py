"""入出力スキーマの定義."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class OutputInfo(BaseModel):
    """出力ファイル情報."""
    
    path: str = Field(description="生成された出力ファイルの絶対パス")
    filename: str = Field(description="ファイル名のみ")
    mime_type: str = Field(description="MIMEタイプ")
    size_bytes: int = Field(description="ファイルサイズ（バイト単位）")


class Metadata(BaseModel):
    """変換メタデータ."""
    
    quarto_version: str = Field(description="使用したQuarto CLIのバージョン")
    render_time_ms: int = Field(description="変換処理時間（ミリ秒）")
    warnings: List[str] = Field(default_factory=list, description="警告メッセージのリスト")


class RenderResult(BaseModel):
    """変換成功時のレスポンス."""
    
    success: bool = Field(default=True, description="成功フラグ")
    format: str = Field(description="使用した出力形式ID")
    output: OutputInfo = Field(description="出力ファイル情報")
    metadata: Metadata = Field(description="変換メタデータ")


class ErrorInfo(BaseModel):
    """エラー詳細情報."""
    
    code: str = Field(description="エラーコード")
    message: str = Field(description="エラーの概要メッセージ")
    details: str = Field(description="エラーの詳細説明")
    quarto_stderr: Optional[str] = Field(default=None, description="Quarto CLIの標準エラー出力内容")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(), 
        description="エラー発生日時"
    )


class ErrorResponse(BaseModel):
    """変換失敗時のレスポンス."""
    
    success: bool = Field(default=False, description="失敗フラグ")
    error: ErrorInfo = Field(description="エラー詳細情報")


class RenderRequest(BaseModel):
    """レンダリングリクエスト."""
    
    content: str = Field(description="Quarto Markdown形式の文字列")
    format: str = Field(description="出力形式ID")
    output_filename: str = Field(description="出力ファイル名")
    template: Optional[str] = Field(default=None, description="テンプレート指定（IDまたはURL）")
    format_options: Dict[str, Any] = Field(default_factory=dict, description="出力形式固有のオプション設定")
