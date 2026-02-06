"""PowerPointテンプレート管理とHTTP/HTTPSダウンロード対応."""

import re
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlparse
import httpx
import yaml


class TemplateError(Exception):
    """テンプレート関連のエラー基底クラス."""
    pass


class TemplateNotFoundError(TemplateError):
    """テンプレートIDが見つからないエラー."""
    pass


class TemplateDownloadError(TemplateError):
    """URLからのダウンロード失敗エラー."""
    pass


class TemplateDownloadTimeoutError(TemplateError):
    """ダウンロードタイムアウトエラー."""
    pass


class TemplateSizeExceededError(TemplateError):
    """ファイルサイズが制限超過エラー."""
    pass


class InvalidTemplateUrlError(TemplateError):
    """不正なURLエラー."""
    pass


class TemplateManager:
    """
    PowerPointテンプレートの管理と解決を担当するクラス.
    
    テンプレートIDからパス解決、またはHTTP/HTTPSからのダウンロードをサポート.
    """
    
    def __init__(
        self, 
        config_path: Optional[Path] = None,
        download_timeout: int = 30,
        max_download_size: int = 50 * 1024 * 1024,  # 50MB
    ):
        """
        Args:
            config_path: テンプレート設定ファイルのパス
            download_timeout: URLダウンロードのタイムアウト秒数
            max_download_size: ダウンロード可能な最大ファイルサイズ（バイト）
        """
        self.config_path = config_path
        self.templates: Dict[str, str] = {}
        self.download_timeout = download_timeout
        self.max_download_size = max_download_size
        
        # 設定ファイルが存在する場合は読み込む
        if config_path and config_path.exists():
            self._load_templates()
    
    def _load_templates(self) -> None:
        """設定ファイルからテンプレート情報を読み込む."""
        if not self.config_path:
            return
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if config and 'templates' in config:
                for template_id, template_info in config['templates'].items():
                    if 'path' in template_info:
                        self.templates[template_id] = template_info['path']
        except Exception as e:
            # 設定ファイルの読み込みエラーは警告として扱い、継続
            pass
    
    async def resolve_template(
        self, 
        template_spec: Optional[str],
        format_id: str,
        temp_dir: Path,
    ) -> Optional[str]:
        """
        テンプレート指定を解決してファイルパスを返す.
        
        Args:
            template_spec: テンプレート指定（IDまたはURL）
            format_id: 出力形式（pptx等）
            temp_dir: 一時ディレクトリパス（URL時のダウンロード先）
            
        Returns:
            解決されたテンプレートファイルの絶対パス、またはNone
            
        Raises:
            TemplateNotFoundError: テンプレートIDが見つからない
            TemplateDownloadError: URLからのダウンロード失敗
            TemplateDownloadTimeoutError: ダウンロードタイムアウト
            TemplateSizeExceededError: ファイルサイズが制限超過
            InvalidTemplateUrlError: 不正なURL
        """
        # pptx以外の形式ではテンプレート不要
        if format_id != "pptx":
            return None
        
        # テンプレート未指定の場合はNone
        if not template_spec:
            return None
        
        # URLかどうか判定（http://またはhttps://で始まる、または://を含む）
        if self._is_url(template_spec):
            # URLの場合、検証してからダウンロード
            # 検証で不正なスキームの場合はInvalidTemplateUrlErrorが発生
            self._validate_url(template_spec)
            return await self._download_template(template_spec, temp_dir)
        else:
            # テンプレートIDとして解決
            return self._resolve_template_id(template_spec)
    
    def _is_url(self, spec: str) -> bool:
        """文字列がURLかどうか判定する（://が含まれる場合はURLとみなす）."""
        return '://' in spec
    
    def _resolve_template_id(self, template_id: str) -> str:
        """
        テンプレートIDからパスを解決する.
        
        Args:
            template_id: テンプレートID
            
        Returns:
            テンプレートファイルの絶対パス
            
        Raises:
            TemplateNotFoundError: テンプレートIDが見つからない、またはファイルが存在しない
        """
        if template_id not in self.templates:
            raise TemplateNotFoundError(
                f"Template ID '{template_id}' not found in configuration"
            )
        
        template_path = Path(self.templates[template_id])
        
        if not template_path.exists():
            raise TemplateNotFoundError(
                f"Template file not found: {template_path}"
            )
        
        return str(template_path.absolute())
    
    async def _download_template(self, url: str, temp_dir: Path) -> str:
        """
        URLからテンプレートをダウンロードする.
        
        Args:
            url: テンプレートファイルのURL
            temp_dir: ダウンロード先の一時ディレクトリ
            
        Returns:
            ダウンロードしたファイルの絶対パス
            
        Raises:
            InvalidTemplateUrlError: 不正なURL
            TemplateDownloadTimeoutError: ダウンロードタイムアウト
            TemplateSizeExceededError: ファイルサイズが制限超過
            TemplateDownloadError: ダウンロード失敗
            
        Note:
            URL検証は呼び出し側で実施済み
        """
        
        # URLからファイル名を抽出
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        if not filename:
            filename = "template.pptx"
        
        download_path = temp_dir / filename
        
        try:
            async with httpx.AsyncClient(timeout=self.download_timeout) as client:
                # HEADリクエストでファイルサイズをチェック
                try:
                    head_response = await client.head(url, follow_redirects=True)
                    content_length = head_response.headers.get('content-length')
                    if content_length and int(content_length) > self.max_download_size:
                        raise TemplateSizeExceededError(
                            f"Template file size ({int(content_length)} bytes) exceeds "
                            f"maximum allowed size ({self.max_download_size} bytes)"
                        )
                except httpx.HTTPStatusError:
                    # HEADリクエストがサポートされていない場合は続行
                    pass
                
                # ファイルをダウンロード
                async with client.stream('GET', url, follow_redirects=True) as response:
                    response.raise_for_status()
                    
                    # ストリーミングダウンロードでサイズを監視
                    downloaded_size = 0
                    with open(download_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            downloaded_size += len(chunk)
                            if downloaded_size > self.max_download_size:
                                raise TemplateSizeExceededError(
                                    f"Template file size exceeds maximum allowed size "
                                    f"({self.max_download_size} bytes)"
                                )
                            f.write(chunk)
            
            return str(download_path.absolute())
            
        except httpx.TimeoutException as e:
            raise TemplateDownloadTimeoutError(
                f"Template download timed out after {self.download_timeout} seconds: {url}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise TemplateDownloadError(
                f"HTTP error {e.response.status_code} while downloading template: {url}"
            ) from e
        except TemplateSizeExceededError:
            # 既に適切なエラーメッセージがあるので再送出
            raise
        except Exception as e:
            raise TemplateDownloadError(
                f"Failed to download template from {url}: {str(e)}"
            ) from e
    
    def _validate_url(self, url: str) -> None:
        """
        URLの妥当性を検証する.
        
        Args:
            url: 検証するURL
            
        Raises:
            InvalidTemplateUrlError: 不正なURL
        """
        try:
            parsed = urlparse(url)
            
            # スキームチェック（HTTP/HTTPSのみ許可）
            if parsed.scheme not in ['http', 'https']:
                raise InvalidTemplateUrlError(
                    f"Invalid URL scheme: {parsed.scheme}. Only http and https are supported."
                )
            
            # HTTPSの使用を推奨（警告は出さずに許可）
            
            # ドメインチェック
            if not parsed.netloc:
                raise InvalidTemplateUrlError("URL must have a valid domain")
            
            # 拡張子チェック（.pptxのみ許可）
            path = parsed.path.lower()
            if not path.endswith('.pptx'):
                raise InvalidTemplateUrlError(
                    "URL must point to a .pptx file"
                )
                
        except ValueError as e:
            raise InvalidTemplateUrlError(f"Invalid URL format: {url}") from e
