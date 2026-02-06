"""
PowerPointテンプレートの管理と解決
"""
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class TemplateError(Exception):
    """テンプレート関連のエラー基底クラス"""
    pass


class TemplateNotFoundError(TemplateError):
    """指定されたテンプレートIDが存在しない"""
    pass


class TemplateAccessError(TemplateError):
    """テンプレートファイルへのアクセス権限がない"""
    pass


class InvalidTemplateError(TemplateError):
    """テンプレートファイルが不正"""
    pass


class TemplateManager:
    """PowerPointテンプレートの管理と解決を行うクラス"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初期化
        
        Args:
            config_path: テンプレート設定ファイル（templates.yaml）のパス
                        Noneの場合、デフォルトパスを使用
        """
        if config_path is None:
            # デフォルトの設定ファイルパス
            config_path = Path(__file__).parent.parent.parent / "config" / "templates.yaml"
        
        self.config_path = config_path
        self.templates: Dict[str, Dict[str, Any]] = {}
        
        # 設定ファイルが存在する場合は読み込み
        if self.config_path.exists():
            self._load_config()
    
    def _load_config(self) -> None:
        """
        設定ファイルからテンプレート定義を読み込み
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and 'templates' in config:
                    self.templates = config['templates']
        except Exception as e:
            # 設定ファイルの読み込みに失敗しても継続（テンプレートなしで動作）
            print(f"Warning: Failed to load template config: {e}")
    
    def resolve_template(self, template_spec: Optional[str], format: str) -> Optional[str]:
        """
        テンプレート指定を解決して実際のファイルパスを返す
        
        Args:
            template_spec: テンプレート指定（IDまたはパス）
            format: 出力形式（pptx等）
            
        Returns:
            解決されたテンプレートファイルの絶対パス、またはNone
            
        Raises:
            TemplateNotFoundError: 指定されたテンプレートIDが存在しない
            TemplateAccessError: テンプレートファイルへのアクセス権限がない
            InvalidTemplateError: テンプレートファイルが不正
        """
        # PowerPoint以外の形式ではテンプレート不要
        if format != "pptx":
            return None
        
        # テンプレート指定がない場合はNone（デフォルトテンプレート使用）
        if not template_spec:
            return None
        
        # 絶対パスとして指定されているか確認
        template_path = Path(template_spec)
        if template_path.is_absolute():
            # 絶対パスの場合、ファイルの存在と拡張子を確認
            if not template_path.exists():
                raise TemplateNotFoundError(f"Template file not found: {template_path}")
            
            if not template_path.is_file():
                raise InvalidTemplateError(f"Template path is not a file: {template_path}")
            
            if template_path.suffix.lower() != ".pptx":
                raise InvalidTemplateError(f"Template file must have .pptx extension: {template_path}")
            
            return str(template_path.absolute())
        
        # テンプレートIDとして扱う
        if template_spec not in self.templates:
            raise TemplateNotFoundError(
                f"Template ID '{template_spec}' not found in configuration. "
                f"Available templates: {list(self.templates.keys())}"
            )
        
        # テンプレート設定からパスを取得
        template_config = self.templates[template_spec]
        template_path_str = template_config.get('path')
        
        if not template_path_str:
            raise InvalidTemplateError(f"Template '{template_spec}' has no path configured")
        
        template_path = Path(template_path_str)
        
        # パスの存在確認
        if not template_path.exists():
            raise TemplateNotFoundError(
                f"Template file not found for ID '{template_spec}': {template_path}"
            )
        
        if not template_path.is_file():
            raise TemplateAccessError(
                f"Template path is not a file for ID '{template_spec}': {template_path}"
            )
        
        return str(template_path.absolute())
