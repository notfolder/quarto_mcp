"""
コンポーネント単体テスト
各コンポーネントが正しく動作することを確認
"""
import sys
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.file_manager import TempFileManager
from src.core.template_manager import TemplateManager, TemplateNotFoundError
from src.models.formats import (
    SUPPORTED_FORMATS, get_mime_type, get_extension
)
from src.models.schemas import (
    RenderRequest, RenderSuccess, RenderError,
    OutputInfo, RenderMetadata, ErrorDetail
)


def test_file_manager():
    """TempFileManagerのテスト"""
    manager = TempFileManager()
    
    # ワークスペース作成テスト
    with manager.create_workspace() as workspace:
        assert workspace.exists(), "ワークスペースが存在すること"
        
        # テストファイル作成
        test_file = workspace / "test.txt"
        test_file.write_text("Test content")
        assert test_file.exists(), "テストファイルが作成されること"
    
    # クリーンアップの確認
    assert not workspace.exists(), "ワークスペースがクリーンアップされること"
    print("✓ TempFileManager tests passed")


def test_template_manager():
    """TemplateManagerのテスト"""
    manager = TemplateManager(config_path=Path("/nonexistent/path.yaml"))
    
    # 非pptx形式ではNoneを返す
    result = manager.resolve_template("any_template", "html")
    assert result is None, "非pptx形式ではNoneを返すこと"
    
    # テンプレート未指定ではNoneを返す
    result = manager.resolve_template(None, "pptx")
    assert result is None, "テンプレート未指定ではNoneを返すこと"
    
    # 絶対パスの解決
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        dummy_template = Path(f.name)
    
    try:
        result = manager.resolve_template(str(dummy_template), "pptx")
        assert result == str(dummy_template.absolute()), "絶対パスが正しく解決されること"
    finally:
        dummy_template.unlink()
    
    # 存在しないテンプレートID
    try:
        manager.resolve_template("nonexistent_template", "pptx")
        assert False, "TemplateNotFoundErrorが発生すること"
    except TemplateNotFoundError:
        pass
    
    print("✓ TemplateManager tests passed")


def test_formats():
    """形式定義のテスト"""
    # サポート形式の確認
    assert "pptx" in SUPPORTED_FORMATS
    assert "html" in SUPPORTED_FORMATS
    assert "pdf" in SUPPORTED_FORMATS
    assert len(SUPPORTED_FORMATS) > 20, "20以上の形式をサポートすること"
    
    # MIMEタイプの確認
    assert get_mime_type("pptx") == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert get_mime_type("html") == "text/html"
    assert get_mime_type("pdf") == "application/pdf"
    
    # 拡張子の確認
    assert get_extension("pptx") == ".pptx"
    assert get_extension("html") == ".html"
    assert get_extension("pdf") == ".pdf"
    
    print("✓ Format definition tests passed")


def test_schemas():
    """Pydanticスキーマのテスト"""
    # RenderRequestのテスト
    req = RenderRequest(
        content="# Test",
        format="pptx",
        output_path="/tmp/test.pptx"
    )
    assert req.format == "pptx"
    assert req.output_path == "/tmp/test.pptx"
    
    # テンプレート付きリクエスト
    req_with_template = RenderRequest(
        content="# Test",
        format="pptx",
        output_path="/tmp/test.pptx",
        template="corporate_standard",
        format_options={"slide-level": 2}
    )
    assert req_with_template.template == "corporate_standard"
    assert req_with_template.format_options["slide-level"] == 2
    
    # バリデーションエラー
    try:
        RenderRequest(
            content="# Test",
            format="pptx"
            # output_pathが必須
        )
        assert False, "バリデーションエラーが発生すること"
    except Exception:
        pass
    
    # OutputInfoのテスト
    output = OutputInfo(
        path="/tmp/output.pptx",
        filename="output.pptx",
        mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        size_bytes=1024
    )
    assert output.filename == "output.pptx"
    assert output.size_bytes == 1024
    
    # RenderMetadataのテスト
    metadata = RenderMetadata(
        quarto_version="1.4.0",
        render_time_ms=500,
        warnings=[]
    )
    assert metadata.quarto_version == "1.4.0"
    assert metadata.render_time_ms == 500
    
    # RenderSuccessのテスト
    success = RenderSuccess(
        format="pptx",
        output=output,
        metadata=metadata
    )
    assert success.success == True
    assert success.format == "pptx"
    
    # シリアライズのテスト
    success_dict = success.model_dump()
    assert success_dict["success"] == True
    assert success_dict["format"] == "pptx"
    
    # ErrorDetailのテスト
    error = ErrorDetail(
        code="RENDER_FAILED",
        message="Test error",
        details="Detailed error message"
    )
    assert error.code == "RENDER_FAILED"
    
    # RenderErrorのテスト
    error_response = RenderError(error=error)
    assert error_response.success == False
    
    error_dict = error_response.model_dump()
    assert error_dict["success"] == False
    assert error_dict["error"]["code"] == "RENDER_FAILED"
    
    print("✓ Schema tests passed")


def test_server_initialization():
    """サーバー初期化のテスト"""
    from src.server import create_server
    from src.tools.render import TOOL_DEFINITION
    
    # サーバーの作成
    server = create_server()
    assert server.name == "quarto-mcp-server"
    
    # ツール定義の確認
    assert TOOL_DEFINITION["name"] == "quarto_render"
    assert "inputSchema" in TOOL_DEFINITION
    
    schema = TOOL_DEFINITION["inputSchema"]
    assert "content" in schema["required"]
    assert "format" in schema["required"]
    assert "output_path" in schema["required"]
    
    print("✓ Server initialization tests passed")


def main():
    """全テストを実行"""
    print("="*60)
    print("Quarto MCP Server - Component Unit Tests")
    print("="*60)
    print()
    
    try:
        test_file_manager()
        test_template_manager()
        test_formats()
        test_schemas()
        test_server_initialization()
        
        print()
        print("="*60)
        print("✓ All unit tests passed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
