"""
Quarto MCP Server - メインサーバーエントリポイント
"""
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .tools.render import quarto_render, TOOL_DEFINITION


def create_server() -> Server:
    """
    MCPサーバーを作成して設定
    
    Returns:
        設定済みのMCPサーバーインスタンス
    """
    server = Server("quarto-mcp-server")
    
    # quarto_renderツールを登録
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """利用可能なツールのリストを返す"""
        return [
            Tool(
                name=TOOL_DEFINITION["name"],
                description=TOOL_DEFINITION["description"],
                inputSchema=TOOL_DEFINITION["inputSchema"]
            )
        ]
    
    # ツール呼び出しハンドラーを登録
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[dict]:
        """
        ツール呼び出しを処理
        
        Args:
            name: ツール名
            arguments: ツール引数
            
        Returns:
            ツール実行結果のリスト
        """
        if name == "quarto_render":
            result = await quarto_render(arguments)
            return [{"type": "text", "text": str(result)}]
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    return server


async def run_server():
    """
    MCPサーバーを実行（標準入出力で通信）
    """
    server = create_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """
    サーバーのメインエントリポイント
    CLIから実行される
    """
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
