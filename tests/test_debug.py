"""デバッグ用テスト - Quartoのエラー詳細を確認."""

import subprocess
import tempfile
from pathlib import Path


def test_quarto_directly():
    """Quarto CLIを直接実行してエラー内容を確認."""
    # シンプルなQuarto Markdown
    content = """# テストドキュメント

これはテストです。

## セクション1

内容1

## セクション2

内容2
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # .qmdファイルを作成
        qmd_path = Path(temp_dir) / "test.qmd"
        qmd_path.write_text(content, encoding='utf-8')
        
        output_path = Path(temp_dir) / "output.html"
        
        # Quarto CLIを直接実行
        result = subprocess.run(
            [
                "quarto", "render", str(qmd_path),
                "--to", "html",
                "--output", str(output_path),
                "--no-execute",
            ],
            capture_output=True,
            text=True,
        )
        
        print("\n=== Quarto Command ===")
        print(f"quarto render {qmd_path} --to html --output {output_path} --no-execute")
        
        print("\n=== Return Code ===")
        print(result.returncode)
        
        print("\n=== STDOUT ===")
        print(result.stdout)
        
        print("\n=== STDERR ===")
        print(result.stderr)
        
        print("\n=== Output File Exists ===")
        print(output_path.exists())
        
        if output_path.exists():
            print(f"File size: {output_path.stat().st_size} bytes")
        
        # エラーの場合は詳細を表示
        if result.returncode != 0:
            print("\n!!! Quarto failed with error code 1 !!!")
            print("Please check the error messages above.")
            
            # quarto checkを実行
            print("\n=== Running 'quarto check' ===")
            check_result = subprocess.run(
                ["quarto", "check"],
                capture_output=True,
                text=True,
            )
            print(check_result.stdout)
            if check_result.stderr:
                print("STDERR:", check_result.stderr)
