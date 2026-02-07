"""Mermaid CLI連携モジュール."""

import asyncio
import os
import re
import shutil
from typing import Optional, Dict, Any


class MermaidCliValidator:
    """Mermaid CLI（mmdc）を使用したバリデーション."""
    
    def __init__(self):
        """初期化."""
        self._cli_path: Optional[str] = None
        self._version: Optional[str] = None
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """
        Mermaid CLIの利用可能性をチェックする.
        
        Returns:
            利用可能な場合True
        """
        # システムパスからmmdcコマンドを検索
        self._cli_path = shutil.which('mmdc')
        if self._cli_path:
            self._version = self._get_version()
            return True
        return False
    
    def _get_version(self) -> Optional[str]:
        """
        Mermaid CLIのバージョン情報を取得する（同期版）.
        
        Returns:
            バージョン文字列、取得失敗時はNone
        """
        if not self._cli_path:
            return None
        
        try:
            # 同期的にバージョン取得を試行
            import subprocess
            result = subprocess.run(
                [self._cli_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version_str = result.stdout.strip()
                return version_str
        except Exception:
            pass
        
        return None
    
    def is_available(self) -> bool:
        """
        Mermaid CLIが利用可能かどうかを返す.
        
        Returns:
            利用可能な場合True
        """
        return self._available
    
    def get_version(self) -> Optional[str]:
        """
        Mermaid CLIのバージョンを返す.
        
        Returns:
            バージョン文字列、未取得の場合はNone
        """
        return self._version
    
    async def validate(self, mermaid_code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Mermaid CLIを使用してMermaidコードをバリデーションする.
        
        Args:
            mermaid_code: Mermaidダイアグラムコード
            timeout: タイムアウト秒数（デフォルト30秒）
            
        Returns:
            バリデーション結果の辞書:
            - is_valid: バリデーション成功/失敗
            - diagram_type: ダイアグラムタイプ
            - error_message: エラーメッセージ（失敗時）
            - error_line: エラー発生行番号（失敗時）
            - warnings: 警告メッセージのリスト
        """
        if not self._available:
            return {
                'is_valid': False,
                'error_message': 'Mermaid CLI is not available',
            }
        
        try:
            # mmdcコマンドを標準入出力方式で実行
            # -i -: 標準入力から読み込み
            # -o <devnull>: 出力を破棄（クロスプラットフォーム対応）
            process = await asyncio.create_subprocess_exec(
                self._cli_path,
                '-i', '-',
                '-o', os.devnull,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Mermaidコードを標準入力に送信
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=mermaid_code.encode('utf-8')),
                timeout=timeout
            )
            
            # 終了コードをチェック
            if process.returncode == 0:
                # バリデーション成功
                diagram_type = self._extract_diagram_type(mermaid_code)
                return {
                    'is_valid': True,
                    'diagram_type': diagram_type,
                    'warnings': []
                }
            else:
                # バリデーション失敗
                error_output = stderr.decode('utf-8')
                error_message = self._parse_error_message(error_output)
                error_line = self._parse_error_line(error_output)
                diagram_type = self._extract_diagram_type(mermaid_code)
                
                return {
                    'is_valid': False,
                    'diagram_type': diagram_type,
                    'error_message': error_message,
                    'error_line': error_line,
                    'warnings': []
                }
        
        except asyncio.TimeoutError:
            return {
                'is_valid': False,
                'error_message': f'Validation timed out after {timeout} seconds',
            }
        except Exception as e:
            return {
                'is_valid': False,
                'error_message': f'Validation error: {str(e)}',
            }
    
    def _extract_diagram_type(self, mermaid_code: str) -> Optional[str]:
        """
        Mermaidコードからダイアグラムタイプを抽出する.
        
        Args:
            mermaid_code: Mermaidコード
            
        Returns:
            ダイアグラムタイプ、検出できない場合はNone
        """
        # 最初の非空行からダイアグラムタイプを抽出
        for line in mermaid_code.split('\n'):
            line = line.strip()
            if line and not line.startswith('%%'):  # コメント行を除外
                # graph, flowchart, sequenceDiagram等を検出
                match = re.match(r'^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitGraph|journey|quadrantChart|requirementDiagram|C4Context)', line)
                if match:
                    return match.group(1)
                break
        
        return None
    
    def _parse_error_message(self, error_output: str) -> str:
        """
        エラー出力からエラーメッセージを抽出する.
        
        Args:
            error_output: 標準エラー出力
            
        Returns:
            エラーメッセージ
        """
        # エラー出力全体を返す（簡略化版）
        # 実際にはより詳細なパースが必要になる場合がある
        lines = error_output.strip().split('\n')
        if lines:
            # 最初の非空行を返す
            for line in lines:
                if line.strip():
                    return line.strip()
        
        return error_output.strip() if error_output else 'Unknown error'
    
    def _parse_error_line(self, error_output: str) -> Optional[int]:
        """
        エラー出力から行番号を抽出する.
        
        Args:
            error_output: 標準エラー出力
            
        Returns:
            行番号、検出できない場合はNone
        """
        # "line X" や "at line X" のようなパターンを検索
        match = re.search(r'(?:at\s+)?line\s+(\d+)', error_output, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        return None
