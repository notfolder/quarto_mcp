"""ExtensionManagerのテスト."""

from pathlib import Path
from unittest.mock import Mock, patch
import pytest
import yaml

from src.managers.extension_manager import ExtensionManager


class TestExtensionManager:
    """ExtensionManagerのテストクラス."""
    
    def test_init_default_source(self):
        """デフォルトの拡張ソースパスで初期化できることを確認."""
        manager = ExtensionManager()
        assert manager.extensions_source == Path("/opt/quarto-project/_extensions")
        assert manager.parent_dir == Path("/opt/quarto-project")
    
    def test_init_custom_source(self):
        """カスタム拡張ソースパスで初期化できることを確認."""
        custom_path = "/custom/path/_extensions"
        manager = ExtensionManager(extensions_source=custom_path)
        assert manager.extensions_source == Path(custom_path)
        assert manager.parent_dir == Path("/custom/path")
    
    def test_init_with_tilde_expansion(self):
        """チルダ展開が正しく機能することを確認."""
        manager = ExtensionManager(extensions_source="~/.quarto/_extensions")
        assert str(manager.extensions_source).startswith(str(Path.home()))
    
    def test_check_extension_exists_true(self, tmp_path):
        """拡張が存在する場合にTrueを返すことを確認."""
        # テスト用の拡張ディレクトリを作成
        ext_dir = tmp_path / "_extensions" / "resepemb" / "kroki"
        ext_dir.mkdir(parents=True)
        (ext_dir / "_extension.yml").write_text("name: kroki\n")
        
        manager = ExtensionManager(extensions_source=str(tmp_path / "_extensions"))
        assert manager._check_extension_exists() is True
    
    def test_check_extension_exists_false(self, tmp_path):
        """拡張が存在しない場合にFalseを返すことを確認."""
        manager = ExtensionManager(extensions_source=str(tmp_path / "_extensions"))
        assert manager._check_extension_exists() is False
    
    @patch("subprocess.run")
    def test_install_extension_success(self, mock_run, tmp_path):
        """quarto addコマンドが成功する場合のテスト."""
        # 拡張ディレクトリを作成
        ext_dir = tmp_path / "_extensions" / "resepemb" / "kroki"
        ext_dir.mkdir(parents=True)
        (ext_dir / "_extension.yml").write_text("name: kroki\n")
        
        # subprocess.runのモック
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Extension installed successfully"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        manager = ExtensionManager(extensions_source=str(tmp_path / "_extensions"))
        manager._install_extension()
        
        # quarto addコマンドが正しく呼ばれたことを確認
        mock_run.assert_called_once()
        args = mock_run.call_args
        assert args[0][0] == ["quarto", "add", "resepemb/quarto-kroki", "--no-prompt"]
        assert args[1]["cwd"] == str(tmp_path)
    
    @patch("subprocess.run")
    def test_install_extension_command_failed(self, mock_run, tmp_path):
        """quarto addコマンドが失敗した場合のテスト."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Failed to install extension"
        mock_run.return_value = mock_result
        
        manager = ExtensionManager(extensions_source=str(tmp_path / "_extensions"))
        
        with pytest.raises(RuntimeError, match="EXTENSION_INSTALL_FAILED"):
            manager._install_extension()
    
    @patch("subprocess.run")
    def test_install_extension_not_found(self, mock_run, tmp_path):
        """quartoコマンドが見つからない場合のテスト."""
        mock_run.side_effect = FileNotFoundError("quarto command not found")
        
        manager = ExtensionManager(extensions_source=str(tmp_path / "_extensions"))
        
        with pytest.raises(RuntimeError, match="quartoコマンドが見つかりません"):
            manager._install_extension()
    
    def test_copy_extension_success(self, tmp_path):
        """拡張のコピーが成功する場合のテスト."""
        # ソースディレクトリを作成
        source_dir = tmp_path / "source" / "_extensions"
        ext_dir = source_dir / "resepemb" / "kroki"
        ext_dir.mkdir(parents=True)
        (ext_dir / "_extension.yml").write_text("name: kroki\n")
        (ext_dir / "kroki.lua").write_text("-- Lua code\n")
        
        # ターゲットディレクトリを作成
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        
        manager = ExtensionManager(extensions_source=str(source_dir))
        manager._copy_extension(target_dir)
        
        # コピーされたファイルの確認
        assert (target_dir / "_extensions" / "resepemb" / "kroki" / "_extension.yml").exists()
        assert (target_dir / "_extensions" / "resepemb" / "kroki" / "kroki.lua").exists()
    
    def test_copy_extension_overwrites_existing(self, tmp_path):
        """既存の_extensionsディレクトリを上書きすることを確認."""
        # ソースディレクトリを作成
        source_dir = tmp_path / "source" / "_extensions"
        ext_dir = source_dir / "resepemb" / "kroki"
        ext_dir.mkdir(parents=True)
        (ext_dir / "_extension.yml").write_text("name: kroki\nversion: 2.0\n")
        
        # ターゲットディレクトリに既存のファイルを作成
        target_dir = tmp_path / "target"
        existing_ext = target_dir / "_extensions" / "resepemb" / "kroki"
        existing_ext.mkdir(parents=True)
        (existing_ext / "_extension.yml").write_text("name: kroki\nversion: 1.0\n")
        
        manager = ExtensionManager(extensions_source=str(source_dir))
        manager._copy_extension(target_dir)
        
        # 新しいバージョンで上書きされていることを確認
        content = (target_dir / "_extensions" / "resepemb" / "kroki" / "_extension.yml").read_text()
        assert "version: 2.0" in content
    
    def test_validate_extension_success(self, tmp_path):
        """拡張の検証が成功する場合のテスト."""
        # 有効な拡張を作成
        ext_dir = tmp_path / "_extensions" / "resepemb" / "kroki"
        ext_dir.mkdir(parents=True)
        
        config = {
            "title": "kroki",
            "author": "Test Author",
            "version": "1.0.0",
        }
        with open(ext_dir / "_extension.yml", "w") as f:
            yaml.dump(config, f)
        
        manager = ExtensionManager()
        is_valid, error_message = manager._validate_extension(tmp_path)
        assert is_valid is True
        assert error_message == ""
    
    def test_validate_extension_missing_file(self, tmp_path):
        """_extension.ymlが存在しない場合の検証テスト."""
        manager = ExtensionManager()
        is_valid, error_message = manager._validate_extension(tmp_path)
        assert is_valid is False
        assert "_extension.ymlが存在しません" in error_message
    
    def test_validate_extension_missing_required_keys(self, tmp_path):
        """必須キーが欠けている場合の検証テスト."""
        ext_dir = tmp_path / "_extensions" / "resepemb" / "kroki"
        ext_dir.mkdir(parents=True)
        
        # titleキーのみ（authorとversionが欠けている）
        config = {"title": "kroki"}
        with open(ext_dir / "_extension.yml", "w") as f:
            yaml.dump(config, f)
        
        manager = ExtensionManager()
        is_valid, error_message = manager._validate_extension(tmp_path)
        assert is_valid is False
        assert "必須キーが不足しています" in error_message
    
    def test_validate_extension_invalid_yaml(self, tmp_path):
        """無効なYAMLの場合の検証テスト."""
        ext_dir = tmp_path / "_extensions" / "resepemb" / "kroki"
        ext_dir.mkdir(parents=True)
        
        # 無効なYAMLを書き込む
        (ext_dir / "_extension.yml").write_text("invalid: yaml: content:\n")
        
        manager = ExtensionManager()
        is_valid, error_message = manager._validate_extension(tmp_path)
        assert is_valid is False
        assert "YAMLパースエラー" in error_message
    
    def test_deploy_extension_full_flow(self, tmp_path):
        """deploy_extensionの完全なフローのテスト（拡張が既に存在する場合）."""
        # ソースディレクトリに拡張を作成
        source_dir = tmp_path / "source" / "_extensions"
        ext_dir = source_dir / "resepemb" / "kroki"
        ext_dir.mkdir(parents=True)
        
        config = {
            "title": "kroki",
            "author": "Test Author",
            "version": "1.0.0",
        }
        with open(ext_dir / "_extension.yml", "w") as f:
            yaml.dump(config, f)
        
        # ターゲットディレクトリ
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        
        manager = ExtensionManager(extensions_source=str(source_dir))
        manager.deploy_extension(target_dir)
        
        # 拡張が正しく配置されたことを確認
        assert (target_dir / "_extensions" / "resepemb" / "kroki" / "_extension.yml").exists()
    
    @patch("subprocess.run")
    def test_deploy_extension_with_install(self, mock_run, tmp_path):
        """deploy_extensionの完全なフローのテスト（拡張をインストールする場合）."""
        # ソースディレクトリは空
        source_dir = tmp_path / "source" / "_extensions"
        
        # subprocess.runのモック
        def side_effect(*args, **kwargs):
            # quarto addコマンド実行後に拡張ディレクトリを作成
            ext_dir = source_dir / "resepemb" / "kroki"
            ext_dir.mkdir(parents=True)
            config = {
                "title": "kroki",
                "author": "Test Author",
                "version": "1.0.0",
            }
            with open(ext_dir / "_extension.yml", "w") as f:
                yaml.dump(config, f)
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Extension installed"
            mock_result.stderr = ""
            return mock_result
        
        mock_run.side_effect = side_effect
        
        # ターゲットディレクトリ
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        
        manager = ExtensionManager(extensions_source=str(source_dir))
        manager.deploy_extension(target_dir)
        
        # quarto addが呼ばれたことを確認
        assert mock_run.called
        
        # 拡張が正しく配置されたことを確認
        assert (target_dir / "_extensions" / "resepemb" / "kroki" / "_extension.yml").exists()
    
    def test_deploy_extension_validation_failed(self, tmp_path):
        """拡張の検証に失敗した場合のテスト."""
        # ソースディレクトリに無効な拡張を作成
        source_dir = tmp_path / "source" / "_extensions"
        ext_dir = source_dir / "resepemb" / "kroki"
        ext_dir.mkdir(parents=True)
        
        # _extension.ymlを作成するが、titleキーがない（無効）
        config = {
            "author": "Test Author",
            "version": "1.0.0",
        }
        with open(ext_dir / "_extension.yml", "w") as f:
            yaml.dump(config, f)
        
        # ターゲットディレクトリ
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        
        manager = ExtensionManager(extensions_source=str(source_dir))
        
        with pytest.raises(FileNotFoundError, match="EXTENSION_INVALID"):
            manager.deploy_extension(target_dir)
