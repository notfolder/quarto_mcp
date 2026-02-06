"""
一時ファイルとディレクトリの管理
"""
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager
from typing import Generator


class TempFileManager:
    """一時ファイルとディレクトリの安全な管理を行うクラス"""
    
    @contextmanager
    def create_workspace(self) -> Generator[Path, None, None]:
        """
        一時作業ディレクトリを作成するコンテキストマネージャー
        
        Yields:
            Path: 作成された一時ディレクトリのパス
            
        Note:
            コンテキスト終了時に自動的にディレクトリを削除
        """
        temp_dir = None
        try:
            # 一時ディレクトリを作成（プレフィックス付き）
            temp_dir = Path(tempfile.mkdtemp(prefix="quarto_mcp_"))
            yield temp_dir
        finally:
            # クリーンアップ（エラー時も確実に削除）
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
