"""Quarto MCP Server - メインサーバー実装."""

import asyncio
from pathlib import Path

import yaml
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from src.tools import render, formats  # , validate_mermaid


# サーバーインスタンス
server = Server("quarto-mcp-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    利用可能なMCPツールの一覧を返す.
    
    Returns:
        ツール定義のリスト
    """
    # テンプレート設定ファイルからテンプレートIDを読み込む
    config_path = Path(__file__).parent.parent / "config" / "templates.yaml"
    template_ids = []
    template_descriptions = {}
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and "templates" in config and config["templates"]:
                    for template_id, template_info in config["templates"].items():
                        template_ids.append(template_id)
                        if isinstance(template_info, dict) and "description" in template_info:
                            template_descriptions[template_id] = template_info["description"]
        except Exception:
            # YAMLパースエラーは無視してデフォルトの説明を使用
            pass
    
    # テンプレートIDのリストを説明文に追加
    template_info_text = ""
    if template_ids:
        template_info_text = "\n\nAvailable template IDs:"
        for tid in template_ids:
            desc = template_descriptions.get(tid, "")
            if desc:
                template_info_text += f"\n  - {tid}: {desc}"
            else:
                template_info_text += f"\n  - {tid}"
    
    return [
        Tool(
            name="quarto_render",
            description=(
                "Convert Quarto Markdown to various formats (PowerPoint, PDF, HTML, etc.). "
                "Supports custom PowerPoint templates via template ID or HTTP/HTTPS URL."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Quarto Markdown content to convert",
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format ID (e.g., pptx, html, pdf, docx)",
                        "enum": [
                            "pptx", "html", "pdf", "docx", "revealjs", "beamer",
                            "gfm", "commonmark", "hugo", "docusaurus", "markua",
                            "mediawiki", "dokuwiki", "zimwiki", "jira", "xwiki",
                            "jats", "ipynb", "rtf", "rst", "asciidoc", "org",
                            "context", "texinfo", "man", "odt", "epub", "typst",
                        ],
                    },
                    "output_filename": {
                        "type": "string",
                        "description": "output file name",
                    },
                    "template": {
                        "type": "string",
                        "description": (
                            "Template specification for PowerPoint format. "
                            "Can be either a template ID (registered in templates.yaml) "
                            "or an HTTP/HTTPS URL to a .pptx file. "
                            f"URL will be automatically downloaded.{template_info_text}"
                        ),
                    },
                    "format_options": {
                        "type": "object",
                        "description": "Format-specific options (Quarto YAML header equivalent)",
                        "additionalProperties": True,
                    },
                },
                "required": ["content", "format", "output_filename"],
            },
        ),
        Tool(
            name="quarto_list_formats",
            description="List all supported Quarto output formats",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Tool(
        #     name="quarto_validate_mermaid",
        #     description=(
        #         "Validate Mermaid diagram syntax in Quarto Markdown content. "
        #         "This is an independent pre-validation tool that should be called before quarto_render. "
        #         "Requires Mermaid CLI (mmdc) to be installed: npm install -g @mermaid-js/mermaid-cli"
        #     ),
        #     inputSchema={
        #         "type": "object",
        #         "properties": {
        #             "content": {
        #                 "type": "string",
        #                 "description": "Quarto Markdown content to validate",
        #             },
        #             "strict_mode": {
        #                 "type": "boolean",
        #                 "description": "Strict mode: treat warnings as errors (default: false)",
        #             },
        #         },
        #         "required": ["content"],
        #     },
        # ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    MCPツールを実行する.
    
    Args:
        name: ツール名
        arguments: ツール引数
        
    Returns:
        実行結果
    """
    # テンプレート設定ファイルのパス
    config_path = Path(__file__).parent.parent / "config" / "templates.yaml"
    
    if name == "quarto_render":
        # 必須パラメータの検証
        content = arguments.get("content")
        format_id = arguments.get("format")
        output_filename = arguments.get("output_filename")
        
        if not content or not format_id or not output_filename:
            return [
                TextContent(
                    type="text",
                    text="Error: Missing required parameters (content, format, output_filename)",
                )
            ]
        
        # オプショナルパラメータ
        template = arguments.get("template")
        format_options = arguments.get("format_options", {})
        
        # レンダリング実行
        result = await render.render(
            content=content,
            format=format_id,
            output_filename=output_filename,
            template=template,
            format_options=format_options,
            config_path=config_path if config_path.exists() else None,
        )
        
        # 結果をJSON文字列として返す
        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
    elif name == "quarto_list_formats":
        # フォーマット一覧取得
        format_list = await formats.list_formats()
        
        # 結果をJSON文字列として返す
        import json
        return [TextContent(type="text", text=json.dumps(format_list, indent=2, ensure_ascii=False))]
    
    # elif name == "quarto_validate_mermaid":
    #     # 必須パラメータの検証
    #     content = arguments.get("content")
    #     
    #     if not content:
    #         return [
    #             TextContent(
    #                 type="text",
    #                 text="Error: Missing required parameter (content)",
    #             )
    #         ]
    #     
    #     # オプショナルパラメータ
    #     strict_mode = arguments.get("strict_mode", False)
    #     
    #     # バリデーション実行
    #     result = await validate_mermaid.validate_mermaid(
    #         content=content,
    #         strict_mode=strict_mode,
    #     )
    #     
    #     # 結果をJSON文字列として返す
    #     import json
    #     return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
    else:
        return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]


async def run_server():
    """MCPサーバーを起動する."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """エントリーポイント."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
