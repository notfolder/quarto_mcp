"""
Quarto出力形式の定義
"""
from typing import Dict

# 出力形式とMIMEタイプのマッピング
FORMAT_MIME_TYPES: Dict[str, str] = {
    # プレゼンテーション形式
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "revealjs": "text/html",
    "beamer": "application/pdf",
    
    # ドキュメント形式
    "html": "text/html",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "odt": "application/vnd.oasis.opendocument.text",
    "epub": "application/epub+zip",
    "typst": "application/pdf",
    
    # Markdown形式
    "gfm": "text/markdown",
    "commonmark": "text/markdown",
    "hugo": "text/markdown",
    "docusaurus": "text/markdown",
    "markua": "text/markdown",
    
    # Wiki形式
    "mediawiki": "text/plain",
    "dokuwiki": "text/plain",
    "zimwiki": "text/plain",
    "jira": "text/plain",
    "xwiki": "text/plain",
    
    # その他形式
    "jats": "application/xml",
    "ipynb": "application/x-ipynb+json",
    "rtf": "application/rtf",
    "rst": "text/x-rst",
    "asciidoc": "text/asciidoc",
    "org": "text/org",
    "context": "application/x-tex",
    "texinfo": "text/x-texinfo",
    "man": "text/troff",
}

# 出力形式と拡張子のマッピング
FORMAT_EXTENSIONS: Dict[str, str] = {
    # プレゼンテーション形式
    "pptx": ".pptx",
    "revealjs": ".html",
    "beamer": ".pdf",
    
    # ドキュメント形式
    "html": ".html",
    "pdf": ".pdf",
    "docx": ".docx",
    "odt": ".odt",
    "epub": ".epub",
    "typst": ".pdf",
    
    # Markdown形式
    "gfm": ".md",
    "commonmark": ".md",
    "hugo": ".md",
    "docusaurus": ".md",
    "markua": ".md",
    
    # Wiki形式
    "mediawiki": ".wiki",
    "dokuwiki": ".txt",
    "zimwiki": ".txt",
    "jira": ".txt",
    "xwiki": ".txt",
    
    # その他形式
    "jats": ".xml",
    "ipynb": ".ipynb",
    "rtf": ".rtf",
    "rst": ".rst",
    "asciidoc": ".adoc",
    "org": ".org",
    "context": ".tex",
    "texinfo": ".texi",
    "man": ".man",
}

# サポートされている形式のリスト
SUPPORTED_FORMATS = list(FORMAT_MIME_TYPES.keys())

def get_mime_type(format_id: str) -> str:
    """
    形式IDからMIMEタイプを取得
    
    Args:
        format_id: 出力形式ID
        
    Returns:
        MIMEタイプ文字列
    """
    return FORMAT_MIME_TYPES.get(format_id, "application/octet-stream")

def get_extension(format_id: str) -> str:
    """
    形式IDから拡張子を取得
    
    Args:
        format_id: 出力形式ID
        
    Returns:
        拡張子文字列（ドット含む）
    """
    return FORMAT_EXTENSIONS.get(format_id, "")
