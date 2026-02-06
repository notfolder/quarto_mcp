"""Quarto CLI実行とレンダリング処理."""

import asyncio
import os
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

from src.core.file_manager import TempFileManager
from src.core.template_manager import TemplateManager
from src.models.schemas import RenderResult, OutputInfo, Metadata
from src.models.formats import FORMAT_DEFINITIONS


class QuartoRenderError(Exception):
    """Quarto変換処理のエラー."""
    
    def __init__(self, message: str, stderr: Optional[str] = None, code: str = "RENDER_FAILED"):
        super().__init__(message)
        self.stderr = stderr
        self.code = code


class QuartoRenderer:
    """Quarto CLIを使用した変換処理を実装するクラス."""
    
    def __init__(
        self,
        quarto_path: str = "quarto",
        timeout: int = 60,
        config_path: Optional[Path] = None,
    ):
        """
        Args:
            quarto_path: Quarto CLI実行ファイルのパス
            timeout: 変換処理のタイムアウト秒数
            config_path: テンプレート設定ファイルのパス
        """
        self.quarto_path = quarto_path
        self.timeout = timeout
        self.temp_manager = TempFileManager()
        self.template_manager = TemplateManager(config_path=config_path)
    
    async def render(
        self,
        content: str,
        format_id: str,
        output_path: str,
        template: Optional[str] = None,
        format_options: Optional[Dict[str, Any]] = None,
    ) -> RenderResult:
        """
        Quarto Markdownを指定形式に変換する.
        
        Args:
            content: Quarto Markdown形式の文字列
            format_id: 出力形式ID
            output_path: 出力ファイルの絶対パス
            template: テンプレート指定（IDまたはURL）
            format_options: 形式固有オプション
            
        Returns:
            RenderResult: 変換結果
            
        Raises:
            QuartoRenderError: 変換処理が失敗した場合
        """
        if format_options is None:
            format_options = {}
        
        # 出力形式の検証
        if format_id not in FORMAT_DEFINITIONS:
            raise QuartoRenderError(
                f"Unsupported format: {format_id}",
                code="UNSUPPORTED_FORMAT"
            )
        
        format_info = FORMAT_DEFINITIONS[format_id]
        start_time = time.time()
        
        # 一時作業ディレクトリを作成
        with self.temp_manager.create_workspace() as temp_dir:
            # テンプレートを解決（URLからダウンロードまたはIDから解決）
            template_path = await self.template_manager.resolve_template(
                template, format_id, temp_dir
            )
            
            # .qmdファイルを作成
            qmd_path = temp_dir / "document.qmd"
            self._write_qmd(qmd_path, content, format_id, format_options, template_path)
            
            # 出力パスのディレクトリを作成
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Quarto CLIコマンドを構築
            command = self._build_command(qmd_path, format_id, output_file)
            
            # Quarto CLIを実行
            stdout, stderr = await self._execute_quarto(command)
            
            # 出力ファイルの存在を確認
            if not output_file.exists():
                raise QuartoRenderError(
                    f"Output file was not generated: {output_file}",
                    stderr=stderr,
                    code="OUTPUT_NOT_FOUND"
                )
            
            # 出力ファイル情報を取得
            file_info = self._get_file_info(output_file, format_info.mime_type)
            
            # Quartoバージョンを取得
            quarto_version = await self._get_quarto_version()
            
            # 変換時間を計算
            render_time_ms = int((time.time() - start_time) * 1000)
            
            # 警告メッセージを抽出
            warnings = self._extract_warnings(stderr)
            
            # 結果を返す
            return RenderResult(
                success=True,
                format=format_id,
                output=file_info,
                metadata=Metadata(
                    quarto_version=quarto_version,
                    render_time_ms=render_time_ms,
                    warnings=warnings,
                )
            )
    
    def _write_qmd(
        self,
        qmd_path: Path,
        content: str,
        format_id: str,
        format_options: Dict[str, Any],
        template_path: Optional[str],
    ) -> None:
        """
        .qmdファイルを作成する.
        
        YAMLヘッダーのマージ処理:
        - 入力contentに既存のYAMLヘッダーがある場合、それをベースとする
        - format_optionsで既存YAMLを上書き・追加
        - templateパラメータがあればreference-docキーを追加（既存値を上書き）
        
        Args:
            qmd_path: 出力する.qmdファイルのパス
            content: Quarto Markdown形式の文字列
            format_id: 出力形式ID
            format_options: 形式固有オプション
            template_path: テンプレートファイルのパス
        """
        # 既存のYAMLヘッダーを抽出
        yaml_header, body = self._extract_yaml_header(content)
        
        # YAMLヘッダーをマージ
        merged_yaml = self._merge_yaml_headers(yaml_header, format_id, format_options, template_path)
        
        # .qmdファイルを作成
        with open(qmd_path, 'w', encoding='utf-8') as f:
            if merged_yaml:
                f.write("---\n")
                yaml.dump(merged_yaml, f, allow_unicode=True, default_flow_style=False)
                f.write("---\n\n")
            f.write(body)
    
    def _extract_yaml_header(self, content: str) -> tuple[Optional[Dict[str, Any]], str]:
        """
        contentからYAMLヘッダーを抽出する.
        
        Args:
            content: Quarto Markdown形式の文字列
            
        Returns:
            (YAMLヘッダー辞書, 本文) のタプル
        """
        # YAMLヘッダーのパターン（先頭の---で始まる）
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            yaml_str = match.group(1)
            body = match.group(2)
            try:
                yaml_dict = yaml.safe_load(yaml_str)
                return yaml_dict if yaml_dict else {}, body
            except yaml.YAMLError:
                # YAML解析エラーの場合は無視
                return None, content
        
        return None, content
    
    def _merge_yaml_headers(
        self,
        existing_yaml: Optional[Dict[str, Any]],
        format_id: str,
        format_options: Dict[str, Any],
        template_path: Optional[str],
    ) -> Dict[str, Any]:
        """
        YAMLヘッダーをマージする.
        
        Args:
            existing_yaml: 既存のYAMLヘッダー
            format_id: 出力形式ID
            format_options: 形式固有オプション
            template_path: テンプレートファイルのパス
            
        Returns:
            マージされたYAMLヘッダー
        """
        # ベースとなるYAML
        merged = existing_yaml.copy() if existing_yaml else {}
        
        # format固有の設定を追加
        if format_id not in merged:
            merged[format_id] = {}
        
        # format_optionsを適用（上書き）
        if isinstance(merged[format_id], dict):
            merged[format_id].update(format_options)
        else:
            merged[format_id] = format_options
        
        # テンプレート指定があれば追加
        if template_path and format_id == "pptx":
            if not isinstance(merged[format_id], dict):
                merged[format_id] = {}
            merged[format_id]["reference-doc"] = template_path
        
        return merged
    
    def _build_command(
        self,
        qmd_path: Path,
        format_id: str,
        output_path: Path,
    ) -> list[str]:
        """
        Quarto CLIコマンドを構築する.
        
        Args:
            qmd_path: 入力.qmdファイルのパス
            format_id: 出力形式ID
            output_path: 出力ファイルのパス
            
        Returns:
            コマンドライン引数のリスト
        """
        return [
            self.quarto_path,
            "render",
            str(qmd_path),
            "--to", format_id,
            "--output", str(output_path),
            "--no-execute",
        ]
    
    async def _execute_quarto(self, command: list[str]) -> tuple[str, str]:
        """
        Quarto CLIを非同期で実行する.
        
        Args:
            command: コマンドライン引数のリスト
            
        Returns:
            (stdout, stderr) のタプル
            
        Raises:
            QuartoRenderError: 実行エラーまたはタイムアウト
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # タイムアウト付きで完了を待機
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout,
            )
            
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            # 非ゼロ終了コードの場合はエラー
            if process.returncode != 0:
                raise QuartoRenderError(
                    f"Quarto CLI exited with code {process.returncode}",
                    stderr=stderr_str,
                    code="RENDER_FAILED"
                )
            
            return stdout_str, stderr_str
            
        except asyncio.TimeoutError as e:
            raise QuartoRenderError(
                f"Quarto CLI timed out after {self.timeout} seconds",
                code="TIMEOUT"
            ) from e
        except FileNotFoundError as e:
            raise QuartoRenderError(
                f"Quarto CLI not found: {self.quarto_path}",
                code="DEPENDENCY_MISSING"
            ) from e
    
    def _get_file_info(self, output_path: Path, mime_type: str) -> OutputInfo:
        """
        出力ファイルの情報を取得する.
        
        Args:
            output_path: 出力ファイルのパス
            mime_type: MIMEタイプ
            
        Returns:
            OutputInfo: 出力ファイル情報
        """
        size = output_path.stat().st_size
        
        return OutputInfo(
            path=str(output_path.absolute()),
            filename=output_path.name,
            mime_type=mime_type,
            size_bytes=size,
        )
    
    async def _get_quarto_version(self) -> str:
        """
        Quarto CLIのバージョンを取得する.
        
        Returns:
            バージョン文字列
        """
        try:
            process = await asyncio.create_subprocess_exec(
                self.quarto_path,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, _ = await asyncio.wait_for(
                process.communicate(),
                timeout=5,
            )
            
            version = stdout.decode('utf-8').strip()
            return version
            
        except Exception:
            return "unknown"
    
    def _extract_warnings(self, stderr: str) -> list[str]:
        """
        標準エラー出力から警告メッセージを抽出する.
        
        Args:
            stderr: 標準エラー出力
            
        Returns:
            警告メッセージのリスト
        """
        warnings = []
        
        # "WARNING" を含む行を抽出
        for line in stderr.split('\n'):
            if 'WARNING' in line.upper() or 'WARN' in line.upper():
                warnings.append(line.strip())
        
        return warnings
