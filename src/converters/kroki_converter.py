"""Mermaid記法をKroki記法に変換するモジュール."""

import os
import re
from typing import Optional, Literal


class KrokiConverter:
    """Quarto MardownコンテンツのMermaid記法をKroki記法に変換するクラス."""
    
    # Quarto拡張記法のパターン（```{mermaid}）
    QUARTO_MERMAID_PATTERN = re.compile(
        r'^```\{mermaid([^\}]*)\}',
        re.MULTILINE
    )
    
    # 標準Markdown記法のパターン（```mermaid）
    MARKDOWN_MERMAID_PATTERN = re.compile(
        r'^```mermaid',
        re.MULTILINE
    )
    
    # 画像形式の型定義
    ImageFormat = Literal["svg", "png", "auto"]
    
    # 出力形式ごとの推奨画像形式
    FORMAT_TO_IMAGE: dict[str, str] = {
        "pptx": "png",
        "docx": "png",
        "pdf": "png",
        "beamer": "png",
        "html": "svg",
        "revealjs": "svg",
        "gfm": "svg",
        "markdown": "svg",
    }
    
    def __init__(
        self,
        format_id: str,
        image_format: Optional[ImageFormat] = None,
    ):
        """
        KrokiConverterを初期化する.
        
        Args:
            format_id: 出力形式ID (pptx, html等)
            image_format: 画像形式 (svg/png/auto/None)
                - svg: 明示的にSVGを指定
                - png: 明示的にPNGを指定
                - auto or None: 出力形式に応じて自動選択
        """
        self.format_id = format_id
        self._image_format = image_format
    
    def convert(self, content: str) -> str:
        """
        Mermaid記法をKroki記法に変換する.
        
        変換処理:
        1. ```{mermaid} → ```{kroki-mermaid} または ```{kroki-mermaid-png/svg}
        2. ```mermaid → ```{kroki-mermaid} または ```{kroki-mermaid-png/svg}
        
        Args:
            content: 元のQuarto Markdownコンテンツ
            
        Returns:
            Kroki記法に変換されたコンテンツ
        """
        # 画像形式を決定
        image_format = self._determine_image_format()
        
        # Quarto拡張記法を変換
        content = self._convert_quarto_syntax(content, image_format)
        
        # 標準Markdown記法を変換
        content = self._convert_markdown_syntax(content, image_format)
        
        return content
    
    def _determine_image_format(self) -> Optional[str]:
        """
        使用する画像形式を決定する.
        
        優先順位:
        1. 環境変数 QUARTO_MCP_KROKI_IMAGE_FORMAT (svg/png)
        2. コンストラクタのimage_format引数 (svg/png)
        3. 出力形式に応じた自動選択
        4. デフォルト: None (Kroki拡張のデフォルトに任せる)
        
        Returns:
            画像形式 ("svg", "png", または None)
        """
        # 1. 環境変数をチェック（最優先）
        env_format = os.environ.get("QUARTO_MCP_KROKI_IMAGE_FORMAT", "").lower()
        if env_format in ("svg", "png"):
            return env_format
        
        # 2. 明示的な指定をチェック
        if self._image_format and self._image_format != "auto":
            return self._image_format
        
        # 3. 出力形式に応じた自動選択
        return self.FORMAT_TO_IMAGE.get(self.format_id)
    
    def _convert_quarto_syntax(self, content: str, image_format: Optional[str]) -> str:
        """
        Quarto拡張記法を変換する.
        
        ```{mermaid #fig-example}
        ↓
        ```{kroki-mermaid #fig-example}  (image_format=None)
        ```{kroki-mermaid-png #fig-example}  (image_format="png")
        ```{kroki-mermaid-svg #fig-example}  (image_format="svg")
        
        Args:
            content: 元のコンテンツ
            image_format: 画像形式 (svg/png/None)
            
        Returns:
            変換後のコンテンツ
        """
        def replacer(match: re.Match) -> str:
            options = match.group(1)  # セルオプション部分
            
            # Kroki記法を生成
            if image_format:
                kroki_lang = f"kroki-mermaid-{image_format}"
            else:
                kroki_lang = "kroki-mermaid"
            
            return f"```{{{kroki_lang}{options}}}"
        
        return self.QUARTO_MERMAID_PATTERN.sub(replacer, content)
    
    def _convert_markdown_syntax(self, content: str, image_format: Optional[str]) -> str:
        """
        標準Markdown記法を変換する.
        
        ```mermaid
        ↓
        ```{kroki-mermaid}  (image_format=None)
        ```{kroki-mermaid-png}  (image_format="png")
        ```{kroki-mermaid-svg}  (image_format="svg")
        
        Args:
            content: 元のコンテンツ
            image_format: 画像形式 (svg/png/None)
            
        Returns:
            変換後のコンテンツ
        """
        # Kroki記法を生成
        if image_format:
            kroki_lang = f"kroki-mermaid-{image_format}"
        else:
            kroki_lang = "kroki-mermaid"
        
        replacement = f"```{{{kroki_lang}}}"
        
        return self.MARKDOWN_MERMAID_PATTERN.sub(replacement, content)
