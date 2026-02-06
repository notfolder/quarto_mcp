"""Quarto出力形式の定義."""

from typing import Dict
from pydantic import BaseModel


class FormatInfo(BaseModel):
    """出力形式の情報."""
    
    format_id: str
    description: str
    extension: str
    mime_type: str
    category: str
    supports_template: bool = False


# サポートする出力形式の定義
FORMAT_DEFINITIONS: Dict[str, FormatInfo] = {
    # プレゼンテーション形式
    "pptx": FormatInfo(
        format_id="pptx",
        description="Microsoft PowerPoint",
        extension=".pptx",
        mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        category="presentation",
        supports_template=True,
    ),
    "revealjs": FormatInfo(
        format_id="revealjs",
        description="Reveal.js HTML Presentation",
        extension=".html",
        mime_type="text/html",
        category="presentation",
        supports_template=True,
    ),
    "beamer": FormatInfo(
        format_id="beamer",
        description="LaTeX Beamer",
        extension=".pdf",
        mime_type="application/pdf",
        category="presentation",
        supports_template=True,
    ),
    
    # ドキュメント形式
    "html": FormatInfo(
        format_id="html",
        description="HTML5 Document",
        extension=".html",
        mime_type="text/html",
        category="document",
    ),
    "pdf": FormatInfo(
        format_id="pdf",
        description="PDF (via LaTeX)",
        extension=".pdf",
        mime_type="application/pdf",
        category="document",
    ),
    "docx": FormatInfo(
        format_id="docx",
        description="Microsoft Word",
        extension=".docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        category="document",
    ),
    "odt": FormatInfo(
        format_id="odt",
        description="OpenDocument Text",
        extension=".odt",
        mime_type="application/vnd.oasis.opendocument.text",
        category="document",
    ),
    "epub": FormatInfo(
        format_id="epub",
        description="EPUB",
        extension=".epub",
        mime_type="application/epub+zip",
        category="document",
    ),
    "typst": FormatInfo(
        format_id="typst",
        description="Typst",
        extension=".pdf",
        mime_type="application/pdf",
        category="document",
    ),
    
    # Markdown形式
    "gfm": FormatInfo(
        format_id="gfm",
        description="GitHub Flavored Markdown",
        extension=".md",
        mime_type="text/markdown",
        category="markdown",
    ),
    "commonmark": FormatInfo(
        format_id="commonmark",
        description="CommonMark",
        extension=".md",
        mime_type="text/markdown",
        category="markdown",
    ),
    "hugo": FormatInfo(
        format_id="hugo",
        description="Hugo",
        extension=".md",
        mime_type="text/markdown",
        category="markdown",
    ),
    "docusaurus": FormatInfo(
        format_id="docusaurus",
        description="Docusaurus",
        extension=".md",
        mime_type="text/markdown",
        category="markdown",
    ),
    "markua": FormatInfo(
        format_id="markua",
        description="Markua (Leanpub)",
        extension=".md",
        mime_type="text/markdown",
        category="markdown",
    ),
    
    # Wiki形式
    "mediawiki": FormatInfo(
        format_id="mediawiki",
        description="MediaWiki",
        extension=".wiki",
        mime_type="text/plain",
        category="wiki",
    ),
    "dokuwiki": FormatInfo(
        format_id="dokuwiki",
        description="DokuWiki",
        extension=".txt",
        mime_type="text/plain",
        category="wiki",
    ),
    "zimwiki": FormatInfo(
        format_id="zimwiki",
        description="Zim Wiki",
        extension=".txt",
        mime_type="text/plain",
        category="wiki",
    ),
    "jira": FormatInfo(
        format_id="jira",
        description="Jira Wiki",
        extension=".txt",
        mime_type="text/plain",
        category="wiki",
    ),
    "xwiki": FormatInfo(
        format_id="xwiki",
        description="XWiki",
        extension=".txt",
        mime_type="text/plain",
        category="wiki",
    ),
    
    # その他形式
    "jats": FormatInfo(
        format_id="jats",
        description="JATS XML",
        extension=".xml",
        mime_type="application/xml",
        category="other",
    ),
    "ipynb": FormatInfo(
        format_id="ipynb",
        description="Jupyter Notebook",
        extension=".ipynb",
        mime_type="application/x-ipynb+json",
        category="other",
    ),
    "rtf": FormatInfo(
        format_id="rtf",
        description="Rich Text Format",
        extension=".rtf",
        mime_type="application/rtf",
        category="other",
    ),
    "rst": FormatInfo(
        format_id="rst",
        description="reStructuredText",
        extension=".rst",
        mime_type="text/x-rst",
        category="other",
    ),
    "asciidoc": FormatInfo(
        format_id="asciidoc",
        description="AsciiDoc",
        extension=".adoc",
        mime_type="text/asciidoc",
        category="other",
    ),
    "org": FormatInfo(
        format_id="org",
        description="Emacs Org-Mode",
        extension=".org",
        mime_type="text/org",
        category="other",
    ),
    "context": FormatInfo(
        format_id="context",
        description="ConTeXt",
        extension=".tex",
        mime_type="application/x-tex",
        category="other",
    ),
    "texinfo": FormatInfo(
        format_id="texinfo",
        description="GNU Texinfo",
        extension=".texi",
        mime_type="application/x-texinfo",
        category="other",
    ),
    "man": FormatInfo(
        format_id="man",
        description="Groff man page",
        extension=".man",
        mime_type="text/troff",
        category="other",
    ),
}
