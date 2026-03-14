from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Union

def make_output_paths() -> tuple[Path, Path, Path]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    code_path = Path(f"generated_app_{timestamp}.py")
    test_path = Path(f"test_generated_app_{timestamp}.py")
    readme_path = Path(f"README_GENERATED_{timestamp}.md")
    return code_path, test_path, readme_path

def write_text_file(path: Union[str, Path], content: str) -> None:
    """Write content to a text file."""
    p = Path(path)
    p.write_text(content or "", encoding="utf-8")
    print(f"Wrote file: {p.resolve()}")