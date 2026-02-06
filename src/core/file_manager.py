"""一時ファイル・ディレクトリ管理."""

import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager
from typing import Generator


class TempFileManager:
    """一時ファイルとディレクトリの安全な管理を担当するクラス."""
    
    @contextmanager
    def create_workspace(self) -> Generator[Path, None, None]:
        """
        一時作業ディレクトリを作成するコンテキストマネージャー.
        
        Yields:
            Path: 一時ディレクトリのパス
            
        Note:
            コンテキスト終了時に自動的にディレクトリを削除する
        """
        temp_dir = None
        try:
            # 一時ディレクトリを作成
            temp_dir = tempfile.mkdtemp(prefix="quarto_mcp_")
            yield Path(temp_dir)
        finally:
            # クリーンアップ（エラーが発生しても必ず実行）
            if temp_dir and Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
