"""
Quarto CLIを使用した変換処理の実装
"""
import asyncio
import re
import yaml
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .file_manager import TempFileManager
from .template_manager import TemplateManager, TemplateError
from ..models.formats import get_mime_type, get_extension, SUPPORTED_FORMATS
from ..models.schemas import OutputInfo, RenderMetadata, RenderSuccess, RenderError, ErrorDetail


class QuartoRenderError(Exception):
    """Quarto変換処理のエラー"""
    pass


class QuartoRenderer:
    """Quarto CLIを使用した変換処理を実行するクラス"""
    
    def __init__(self, quarto_path: str = "quarto"):
        """
        初期化
        
        Args:
            quarto_path: Quarto CLI実行ファイルのパス（デフォルト: "quarto"）
        """
        self.quarto_path = quarto_path
        self.temp_manager = TempFileManager()
        self.template_manager = TemplateManager()
    
    async def render(
        self,
        content: str,
        format: str,
        output_path: str,
        template: Optional[str] = None,
        format_options: Optional[Dict[str, Any]] = None
    ) -> RenderSuccess:
        """
        Quarto Markdownを指定形式に変換
        
        Args:
            content: 変換対象のQuarto Markdown文字列
            format: 出力形式ID
            output_path: 出力ファイルの絶対パス
            template: PowerPointテンプレート指定（任意）
            format_options: 形式固有オプション（任意）
            
        Returns:
            RenderSuccess: 変換成功時のレスポンス
            
        Raises:
            QuartoRenderError: 変換処理が失敗した場合
        """
        start_time = time.time()
        
        # 形式の検証
        if format not in SUPPORTED_FORMATS:
            raise QuartoRenderError(
                f"Unsupported format: {format}. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
            )
        
        if format_options is None:
            format_options = {}
        
        # 出力パスの検証と準備
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 一時作業ディレクトリで作業
        with self.temp_manager.create_workspace() as temp_dir:
            # テンプレートの解決
            template_path = None
            try:
                template_path = self.template_manager.resolve_template(template, format)
            except TemplateError as e:
                raise QuartoRenderError(f"Template error: {str(e)}")
            
            # .qmdファイルを作成
            qmd_file = temp_dir / "document.qmd"
            self._write_qmd(qmd_file, content, format, format_options, template_path)
            
            # Quarto CLIコマンドを構築
            command = self._build_command(qmd_file, format, output_file)
            
            # Quarto CLIを実行
            stdout, stderr, return_code = await self._execute_quarto(command)
            
            # エラーチェック
            if return_code != 0:
                raise QuartoRenderError(
                    f"Quarto render failed with exit code {return_code}.\n"
                    f"stderr: {stderr}\n"
                    f"stdout: {stdout}"
                )
            
            # 出力ファイルの存在確認
            if not output_file.exists():
                raise QuartoRenderError(
                    f"Output file was not created: {output_file}\n"
                    f"Quarto stderr: {stderr}"
                )
            
            # Quartoバージョンを取得
            quarto_version = await self._get_quarto_version()
            
            # ファイル情報を取得
            file_info = self._get_file_info(output_file, format)
            
            # 処理時間を計算
            render_time_ms = int((time.time() - start_time) * 1000)
            
            # 警告メッセージを抽出
            warnings = self._extract_warnings(stderr)
            
            # レスポンスを構築
            metadata = RenderMetadata(
                quarto_version=quarto_version,
                render_time_ms=render_time_ms,
                warnings=warnings
            )
            
            return RenderSuccess(
                format=format,
                output=file_info,
                metadata=metadata
            )
    
    def _write_qmd(
        self,
        qmd_file: Path,
        content: str,
        format: str,
        format_options: Dict[str, Any],
        template_path: Optional[str]
    ) -> None:
        """
        .qmdファイルを作成
        
        Args:
            qmd_file: 作成する.qmdファイルのパス
            content: Quarto Markdownコンテンツ
            format: 出力形式
            format_options: 形式固有オプション
            template_path: テンプレートファイルのパス（任意）
        """
        # 既存のYAMLヘッダーを抽出
        yaml_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        yaml_match = re.match(yaml_pattern, content, re.DOTALL)
        
        existing_yaml = {}
        body_content = content
        
        if yaml_match:
            # 既存YAMLを解析
            yaml_str = yaml_match.group(1)
            try:
                existing_yaml = yaml.safe_load(yaml_str) or {}
            except yaml.YAMLError:
                # YAMLパースエラーの場合は既存YAMLを無視
                pass
            
            # コンテンツ本文を抽出（YAMLヘッダーを除去）
            body_content = content[yaml_match.end():]
        
        # YAMLをマージ（format_optionsが優先）
        merged_yaml = {**existing_yaml, **format_options}
        
        # テンプレート指定を追加（PowerPointの場合）
        if template_path and format == "pptx":
            # format固有の設定を更新
            if format not in merged_yaml:
                merged_yaml[format] = {}
            if not isinstance(merged_yaml[format], dict):
                merged_yaml[format] = {}
            merged_yaml[format]["reference-doc"] = template_path
        
        # .qmdファイルを書き込み
        with open(qmd_file, 'w', encoding='utf-8') as f:
            if merged_yaml:
                # YAMLヘッダーを追加
                f.write("---\n")
                yaml.dump(merged_yaml, f, default_flow_style=False, allow_unicode=True)
                f.write("---\n\n")
            
            # コンテンツ本文を書き込み
            f.write(body_content)
    
    def _build_command(self, qmd_file: Path, format: str, output_file: Path) -> list:
        """
        Quarto CLIコマンドを構築
        
        Args:
            qmd_file: 入力.qmdファイル
            format: 出力形式
            output_file: 出力ファイルパス
            
        Returns:
            コマンドライン引数のリスト
        """
        return [
            self.quarto_path,
            "render",
            str(qmd_file),
            "--to", format,
            "--output", str(output_file),
            "--no-execute"  # セキュリティのためコード実行を無効化
        ]
    
    async def _execute_quarto(self, command: list, timeout: int = 60) -> tuple:
        """
        Quarto CLIを非同期で実行
        
        Args:
            command: コマンドライン引数のリスト
            timeout: タイムアウト時間（秒）
            
        Returns:
            (stdout, stderr, return_code)のタプル
            
        Raises:
            QuartoRenderError: タイムアウトまたは実行エラー
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')
            
            return stdout, stderr, process.returncode
            
        except asyncio.TimeoutError:
            # タイムアウト時はプロセスを強制終了
            try:
                process.kill()
                await process.wait()
            except (ProcessLookupError, asyncio.CancelledError):
                pass
            raise QuartoRenderError(f"Quarto render timed out after {timeout} seconds")
        except Exception as e:
            raise QuartoRenderError(f"Failed to execute Quarto CLI: {str(e)}")
    
    async def _get_quarto_version(self) -> str:
        """
        Quarto CLIのバージョンを取得
        
        Returns:
            バージョン文字列
        """
        try:
            process = await asyncio.create_subprocess_exec(
                self.quarto_path,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout_bytes, _ = await asyncio.wait_for(process.communicate(), timeout=5)
            version = stdout_bytes.decode('utf-8').strip()
            return version
        except (asyncio.TimeoutError, OSError, FileNotFoundError) as e:
            return "unknown"
    
    def _get_file_info(self, output_file: Path, format: str) -> OutputInfo:
        """
        出力ファイルの情報を取得
        
        Args:
            output_file: 出力ファイルのパス
            format: 出力形式
            
        Returns:
            OutputInfo: ファイル情報
        """
        file_size = output_file.stat().st_size
        mime_type = get_mime_type(format)
        
        return OutputInfo(
            path=str(output_file.absolute()),
            filename=output_file.name,
            mime_type=mime_type,
            size_bytes=file_size
        )
    
    def _extract_warnings(self, stderr: str) -> list:
        """
        標準エラー出力から警告メッセージを抽出
        
        Args:
            stderr: 標準エラー出力
            
        Returns:
            警告メッセージのリスト
        """
        warnings = []
        for line in stderr.split('\n'):
            line = line.strip()
            if line and ('warning' in line.lower() or 'warn' in line.lower()):
                warnings.append(line)
        return warnings
