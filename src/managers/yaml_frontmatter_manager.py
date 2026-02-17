"""YAMLフロントマターの管理モジュール."""

import re
from typing import Optional, Any
import yaml


class YAMLFrontmatterManager:
    """YAMLフロントマターへのKroki設定の追加と管理を行うクラス."""
    
    # YAMLヘッダーのパターン
    YAML_HEADER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n(.*)$',
        re.DOTALL
    )
    
    def __init__(self, kroki_service_url: str):
        """
        YAMLFrontmatterManagerを初期化する.
        
        Args:
            kroki_service_url: KrokiサービスのURL
        """
        self.kroki_service_url = kroki_service_url
    
    def add_kroki_config(self, content: str) -> str:
        """
        コンテンツのYAMLフロントマターにKroki設定を追加する.
        
        処理内容:
        1. 既存のYAMLヘッダーを抽出
        2. filters配列に 'kroki' を追加（重複チェック）
        3. kroki.serviceUrl を設定
        4. YAMLと本文を結合して返す
        
        Args:
            content: 元のQuarto Markdownコンテンツ
            
        Returns:
            Kroki設定が追加されたコンテンツ
        """
        # YAMLヘッダーを抽出
        yaml_dict, body = self._extract_yaml_header(content)
        
        # Kroki設定をマージ
        merged_yaml = self._merge_kroki_config(yaml_dict)
        
        # YAMLと本文を再構築
        return self._reconstruct_content(merged_yaml, body)
    
    def _extract_yaml_header(self, content: str) -> tuple[Optional[dict[str, Any]], str]:
        """
        コンテンツからYAMLヘッダーを抽出する.
        
        Args:
            content: Quarto Markdownコンテンツ
            
        Returns:
            (YAML辞書, 本文) のタプル
        """
        match = self.YAML_HEADER_PATTERN.match(content)
        
        if match:
            yaml_str = match.group(1).strip()  # 前後の空白を削除
            body = match.group(2)
            
            # 空の場合は空辞書を返す
            if not yaml_str:
                return {}, body
            
            try:
                yaml_dict = yaml.safe_load(yaml_str)
                # 辞書でない場合は空辞書として扱う
                if not isinstance(yaml_dict, dict):
                    return {}, body
                return yaml_dict if yaml_dict else {}, body
            except yaml.YAMLError:
                # YAML解析エラーの場合は空辞書として扱う
                return {}, body
        
        # YAMLヘッダーがない場合
        return {}, content
    
    def _merge_kroki_config(self, yaml_dict: Optional[dict[str, Any]]) -> dict[str, Any]:
        """
        既存のYAML辞書にKroki設定をマージする.
        
        Args:
            yaml_dict: 既存のYAML辞書
            
        Returns:
            Kroki設定がマージされたYAML辞書
        """
        # 辞書でない場合は空辞書を使用
        if not isinstance(yaml_dict, dict):
            yaml_dict = {}
        
        # filtersキーの処理
        if "filters" not in yaml_dict:
            yaml_dict["filters"] = []
        elif not isinstance(yaml_dict["filters"], list):
            # filtersが配列でない場合は配列に変換
            yaml_dict["filters"] = [yaml_dict["filters"]]
        
        # quarto-krokiフィルターが含まれていない場合のみ追加
        if "quarto-kroki" not in yaml_dict["filters"]:
            yaml_dict["filters"].append("quarto-kroki")
        
        # krokiキーの処理
        if "kroki" not in yaml_dict:
            yaml_dict["kroki"] = {}
        elif not isinstance(yaml_dict["kroki"], dict):
            # krokiが辞書でない場合は辞書に変換
            yaml_dict["kroki"] = {}
        
        # serviceUrlを設定（常に上書き）
        yaml_dict["kroki"]["serviceUrl"] = self.kroki_service_url
        
        return yaml_dict
    
    def _reconstruct_content(self, yaml_dict: dict[str, Any], body: str) -> str:
        """
        YAML辞書と本文からコンテンツを再構築する.
        
        Args:
            yaml_dict: YAML辞書
            body: 本文
            
        Returns:
            YAMLヘッダーと本文を結合したコンテンツ
        """
        if not yaml_dict:
            # YAMLが空の場合は本文のみ返す
            return body
        
        # YAML辞書を文字列化
        yaml_str = yaml.dump(
            yaml_dict,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False
        )
        
        # YAMLヘッダーとして構築
        return f"---\n{yaml_str}---\n\n{body}"
