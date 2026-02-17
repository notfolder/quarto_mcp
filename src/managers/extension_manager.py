"""
Quarto拡張の管理モジュール.

quarto-kroki拡張の取得、保存、配置を管理する。
"""


import shutil
import subprocess
from pathlib import Path
from typing import Optional
import yaml


class ExtensionManager:
    """
    Quarto拡張の取得と配置を管理するクラス.
    
    主な責務:
    - 拡張の存在確認
    - Quarto addコマンドによる拡張のインストール
    - 拡張の一時ディレクトリへのコピー
    - 拡張の検証
    """
    
    def __init__(self, extensions_source: Optional[str] = None):
        """
        ExtensionManagerを初期化する.
        
        Args:
            extensions_source: 拡張ソースディレクトリのパス
                              デフォルト: /opt/quarto-project/_extensions
        """
        default_source = "/opt/quarto-project/_extensions"
        self.extensions_source = Path(extensions_source or default_source).expanduser()
        
        # 親ディレクトリのパス（quarto addコマンドを実行するディレクトリ）
        self.parent_dir = self.extensions_source.parent
        
        # 親ディレクトリの作成は実際に使用するときに行う（初期化時には作成しない）
    
    def deploy_extension(self, target_dir: Path) -> None:
        """
        拡張を指定されたディレクトリに配置する.
        
        処理フロー:
        1. 拡張がソースディレクトリに存在するか確認
        2. 存在すれば_extensionsディレクトリ全体をコピー
        3. 存在しなければquarto addコマンドで取得してからコピー
        4. 配置した拡張を検証
        
        Args:
            target_dir: 配置先ディレクトリのパス（一時ディレクトリ）
            
        Raises:
            RuntimeError: 拡張のインストールまたはコピーに失敗した場合
            FileNotFoundError: 拡張の検証に失敗した場合
        """
        # 拡張が存在するか確認
        if not self._check_extension_exists():
            # 存在しない場合はインストール
            self._install_extension()
        
        # _extensionsディレクトリをコピー
        self._copy_extension(target_dir)
        
        # 検証
        if not self._validate_extension(target_dir):
            raise FileNotFoundError(
                f"EXTENSION_INVALID: 配置後の拡張が無効です。"
                f"{target_dir / '_extensions' / 'resepemb' / 'kroki' / '_extension.yml'} が見つかりません。"
            )
    
    def _check_extension_exists(self) -> bool:
        """
        ソースディレクトリに拡張が存在するか確認する.
        
        Returns:
            拡張が存在する場合はTrue、存在しない場合はFalse
        """
        extension_yml = self.extensions_source / "resepemb" / "kroki" / "_extension.yml"
        return extension_yml.exists()
    
    def _install_extension(self) -> None:
        """
        quarto addコマンドで拡張をインストールする.
        
        親ディレクトリに移動してquarto addコマンドを実行し、
        _extensions/resepemb/krokiに拡張をインストールする。
        
        Raises:
            RuntimeError: quartoコマンドの実行に失敗した場合
        """
        # 親ディレクトリが存在しない場合は作成
        if not self.parent_dir.exists():
            try:
                self.parent_dir.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                raise RuntimeError(
                    f"EXTENSION_INSTALL_FAILED: 親ディレクトリの作成に失敗しました: {e}"
                )
        
        try:
            # quarto addコマンドを実行
            result = subprocess.run(
                ["quarto", "add", "resepemb/quarto-kroki", "--no-prompt"],
                cwd=str(self.parent_dir),
                capture_output=True,
                text=True,
                timeout=300,  # 5分のタイムアウト
            )
            
            if result.returncode != 0:
                raise RuntimeError(
                    f"EXTENSION_INSTALL_FAILED: quarto addコマンドが失敗しました。\n"
                    f"終了コード: {result.returncode}\n"
                    f"標準出力: {result.stdout}\n"
                    f"標準エラー: {result.stderr}"
                )
            
            # インストール後、_extension.ymlの存在を確認
            extension_yml = self.extensions_source / "resepemb" / "kroki" / "_extension.yml"
            if not extension_yml.exists():
                raise RuntimeError(
                    f"EXTENSION_INSTALL_FAILED: quarto addコマンドは成功しましたが、"
                    f"_extension.ymlが見つかりません: {extension_yml}"
                )
                
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "EXTENSION_INSTALL_FAILED: quarto addコマンドがタイムアウトしました。"
            )
        except FileNotFoundError:
            raise RuntimeError(
                "EXTENSION_INSTALL_FAILED: quartoコマンドが見つかりません。"
                "Quarto CLIがインストールされているか確認してください。"
            )
    
    def _copy_extension(self, target_dir: Path) -> None:
        """
        _extensionsディレクトリ全体を配置先にコピーする.
        
        Args:
            target_dir: 配置先ディレクトリのパス
            
        Raises:
            RuntimeError: コピー処理に失敗した場合
        """
        try:
            target_extensions = target_dir / "_extensions"
            
            # 既存の_extensionsディレクトリがあれば削除
            if target_extensions.exists():
                shutil.rmtree(target_extensions)
            
            # _extensionsディレクトリ全体をコピー
            # symlinks=Falseでシンボリックリンクを実体としてコピー
            shutil.copytree(
                self.extensions_source,
                target_extensions,
                symlinks=False,
                dirs_exist_ok=True,
            )
            
        except Exception as e:
            raise RuntimeError(
                f"EXTENSION_COPY_FAILED: 拡張のコピーに失敗しました: {e}"
            )
    
    def _validate_extension(self, target_dir: Path) -> bool:
        """
        配置した拡張を検証する.
        
        Args:
            target_dir: 配置先ディレクトリのパス
            
        Returns:
            検証が成功した場合はTrue、失敗した場合はFalse
        """
        extension_yml = (
            target_dir / "_extensions" / "resepemb" / "kroki" / "_extension.yml"
        )
        
        if not extension_yml.exists():
            return False
        
        try:
            # YAMLファイルをパースして必須キーを確認
            with open(extension_yml, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            # 必須キーの存在確認
            required_keys = ["name", "author", "version"]
            for key in required_keys:
                if key not in config:
                    return False
            
            return True
            
        except Exception:
            return False
