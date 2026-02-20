"""Quarto CLI実行とレンダリング処理."""

import asyncio
import os
import re
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

from src.core.file_manager import TempFileManager
from src.core.template_manager import TemplateManager
from src.models.schemas import RenderResult, OutputInfo, Metadata
from src.models.formats import FORMAT_DEFINITIONS
from src.converters.kroki_converter import KrokiConverter
from src.managers.yaml_frontmatter_manager import YAMLFrontmatterManager
from src.managers.extension_manager import ExtensionManager


class QuartoRenderError(Exception):
    """Quarto変換処理のエラー."""
    
    def __init__(self, message: str, stderr: Optional[str] = None, code: str = "RENDER_FAILED"):
        # stderrがある場合はメッセージに含める
        if stderr and stderr.strip():
            full_message = f"{message}\n\nQuarto stderr:\n{stderr}"
        else:
            full_message = message
        super().__init__(full_message)
        self.stderr = stderr
        self.code = code


class QuartoRenderer:
    """Quarto CLIを使用した変換処理を実装するクラス."""
    
    def __init__(
        self,
        quarto_path: str = "quarto",
        timeout: int = 600,  # デフォルト10分（600秒）
        config_path: Optional[Path] = None,
    ):
        """
        Args:
            quarto_path: Quarto CLI実行ファイルのパス
            timeout: 変換処理のタイムアウト秒数
            config_path: テンプレート設定ファイルのパス
        """
        import os
        # 環境変数QUARTO_TIMEOUTがあれば優先
        env_timeout = os.environ.get("QUARTO_TIMEOUT")
        if env_timeout is not None:
            try:
                timeout = int(env_timeout)
            except ValueError:
                pass  # 不正な値は無視してデフォルト/引数を使う
        self.quarto_path = quarto_path
        self.timeout = timeout
        self.temp_manager = TempFileManager()
        self.template_manager = TemplateManager(config_path=config_path)
    
    async def render(
        self,
        content: str,
        format_id: str,
        output_filename: str,
        template: Optional[str] = None,
        format_options: Optional[Dict[str, Any]] = None,
    ) -> RenderResult:
        """
        Quarto Markdownを指定形式に変換する.
        
        Args:
            content: Quarto Markdown形式の文字列
            format_id: 出力形式ID
            output_filename: 出力ファイルの絶対パス
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
        
        # Kroki統合機能の適用
        if self._is_kroki_enabled():
            try:
                content = self._apply_kroki_conversion(content, format_id, format_options)
            except Exception as e:
                # Kroki変換でエラーが発生した場合はフォールバック
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Kroki conversion failed, falling back to standard flow: {e}")
        else:
            # Krokiが無効な場合は標準Mermaid記法をQuarto拡張記法に変換
            try:
                content = self._apply_mermaid_conversion(content)
            except Exception as e:
                # Mermaid変換でエラーが発生した場合はフォールバック
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Mermaid conversion failed, falling back to standard flow: {e}")
        
        # 一時作業ディレクトリを作成
        with self.temp_manager.create_workspace() as temp_dir:
            # Kroki有効時は拡張を配置
            if self._is_kroki_enabled():
                try:
                    self._deploy_kroki_extension(temp_dir)
                except Exception as e:
                    # 拡張配置に失敗した場合は例外を発生
                    raise QuartoRenderError(
                        f"Failed to deploy Kroki extension: {e}",
                        code="EXTENSION_DEPLOY_FAILED"
                    )
            # テンプレートを解決（URLからダウンロードまたはIDから解決）
            template_path = await self.template_manager.resolve_template(
                template, format_id, temp_dir
            )
            
            # .qmdファイルを作成
            qmd_path = temp_dir / "document.qmd"
            self._write_qmd(qmd_path, content, format_id, format_options, template_path)
            
            # 最終的な出力パス
            final_output_path = Path(output_filename)
            final_output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 一時ディレクトリ内での出力ファイル名（拡張子を取得）
            temp_output = temp_dir / f"document{format_info.extension}"
            
            # Quarto CLIコマンドを構築（一時ディレクトリ内に出力）
            command = self._build_command(qmd_path, format_id, temp_output)
            
            # Quarto CLIを実行（カレントディレクトリを一時ディレクトリに設定）
            stdout, stderr = await self._execute_quarto(command, cwd=temp_dir)
            
            # 一時ディレクトリ内の出力ファイルの存在を確認
            if not temp_output.exists():
                raise QuartoRenderError(
                    f"Output file was not generated: {temp_output}",
                    stderr=stderr,
                    code="OUTPUT_NOT_FOUND"
                )
            
            # 一時ファイルを最終出力パスにコピー
            shutil.copy2(temp_output, final_output_path)
            
            # 出力ファイル情報を取得
            file_info = self._get_file_info(final_output_path, format_info.mime_type)
            
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
        # 空のYAMLヘッダーにも対応するため、改行を\s*に変更
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            yaml_str = match.group(1).strip()  # 前後の空白を削除
            body = match.group(2)
            
            # 空の場合は空辞書を返す
            if not yaml_str:
                return {}, body
            
            try:
                yaml_dict = yaml.safe_load(yaml_str)
                # 辞書でない場合は空の辞書を返す
                if not isinstance(yaml_dict, dict):
                    return {}, body
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
        # ベースとなるYAML（辞書でない場合は空の辞書を使用）
        if existing_yaml and isinstance(existing_yaml, dict):
            merged = existing_yaml.copy()
        else:
            merged = {}
        
        # format固有の設定を追加
        if format_id not in merged:
            merged[format_id] = {}
        
        # format_optionsを適用（上書き）
        if isinstance(merged[format_id], dict):
            merged[format_id].update(format_options)
        else:
            merged[format_id] = format_options
        
        # PowerPoint形式の場合、追加設定を適用
        if format_id == "pptx":
            if not isinstance(merged[format_id], dict):
                merged[format_id] = {}
            
            # テンプレート指定があれば追加
            if template_path:
                merged[format_id]["reference-doc"] = template_path
            
            # fig-formatをsvgに強制設定（ユーザー指定がない場合のみ）
            if "fig-format" not in merged[format_id]:
                merged[format_id]["fig-format"] = "svg"
        
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
            output_path: 出力ファイルのパス（一時ディレクトリ内）
            
        Returns:
            コマンドライン引数のリスト
        """
        # パスからファイル名のみを取得（カレントディレクトリが一時ディレクトリなので）
        qmd_filename = Path(qmd_path).name
        output_filename = Path(output_path).name
        
        return [
            self.quarto_path,
            "render",
            qmd_filename,
            "--to", format_id,
            "--output", output_filename,
            "--no-execute",
        ]
    
    async def _execute_quarto(self, command: list[str], cwd: Optional[Path] = None) -> tuple[str, str]:
        """
        Quarto CLIを非同期で実行する.
        
        Args:
            command: コマンドライン引数のリスト
            cwd: 実行時のカレントディレクトリ（オプション）
            
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
                cwd=str(cwd) if cwd else None,
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
    
    def _is_kroki_enabled(self) -> bool:
        """
        Kroki統合が有効かどうかを判定する.
        
        環境変数 QUARTO_MCP_KROKI_URL が設定されていて、
        有効なURL形式（http または https で始まる）であれば有効と判定する.
        
        Returns:
            Kroki統合が有効な場合True、それ以外False
        """
        kroki_url = os.environ.get("QUARTO_MCP_KROKI_URL", "").strip()
        
        if not kroki_url:
            return False
        
        # URL形式の検証（http または https で始まるか）
        if not (kroki_url.startswith("http://") or kroki_url.startswith("https://")):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid Kroki URL format: {kroki_url}")
            return False
        
        return True
    
    def _deploy_kroki_extension(self, temp_dir: Path) -> None:
        """
        Kroki拡張を一時ディレクトリに配置する.
        
        Args:
            temp_dir: 一時作業ディレクトリのパス
            
        Raises:
            RuntimeError: 拡張の配置に失敗した場合
            FileNotFoundError: 拡張の検証に失敗した場合
        """
        # 環境変数から拡張ソースを取得
        extensions_source = os.environ.get("QUARTO_MCP_EXTENSIONS_SOURCE")
        
        # ExtensionManagerを初期化
        ext_manager = ExtensionManager(extensions_source=extensions_source)
        
        # 拡張を配置
        ext_manager.deploy_extension(temp_dir)
    
    def _apply_kroki_conversion(
        self,
        content: str,
        format_id: str,
        format_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Kroki統合変換を適用する.
        
        処理内容:
        1. KrokiConverterでMermaid記法をKroki記法に変換
        2. YAMLFrontmatterManagerでKroki設定をYAMLヘッダーに追加
        
        Args:
            content: 元のQuarto Markdownコンテンツ
            format_id: 出力形式ID
            format_options: 形式固有オプション（未使用だが将来の拡張用）
            
        Returns:
            Kroki統合が適用されたコンテンツ
            
        Raises:
            Exception: 変換処理でエラーが発生した場合
        """
        # 環境変数からKroki URLを取得
        kroki_url = os.environ.get("QUARTO_MCP_KROKI_URL", "").strip()
        
        # 環境変数から画像形式を取得（オプション）
        image_format_env = os.environ.get("QUARTO_MCP_KROKI_IMAGE_FORMAT", "").lower()
        image_format = image_format_env if image_format_env in ("svg", "png") else None
        
        # 1. Mermaid記法をKroki記法に変換
        converter = KrokiConverter(format_id=format_id, image_format=image_format)
        content = converter.convert(content)
        
        # 2. YAMLフロントマターにKroki設定を追加
        yaml_manager = YAMLFrontmatterManager(kroki_service_url=kroki_url)
        content = yaml_manager.add_kroki_config(content)
        
        return content
    
    def _apply_mermaid_conversion(self, content: str) -> str:
        """
        標準Mermaid記法をQuarto拡張記法に変換する.
        
        処理内容:
        - 標準Markdown記法（```mermaid）をQuarto拡張記法（```{mermaid}）に変換
        
        Args:
            content: 元のQuarto Markdownコンテンツ
            
        Returns:
            Quarto拡張記法に変換されたコンテンツ
            
        Raises:
            Exception: 変換処理でエラーが発生した場合
        """
        # 標準Markdown記法（```mermaid）をQuarto拡張記法（```{mermaid}）に変換
        # 既に```{mermaid}形式のものはそのまま保持される
        pattern = re.compile(r'^```mermaid', re.MULTILINE)
        content = pattern.sub('```{mermaid}', content)
        
        return content
