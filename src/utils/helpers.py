import sys
from pathlib import Path


def clear_pycache():
    # Don't clear pycache if running as a frozen binary
    if getattr(sys, "frozen", False):
        return

    for pycache_dir in Path(".").rglob("__pycache__"):
        if pycache_dir.is_dir():
            try:
                for item in pycache_dir.iterdir():
                    item.unlink()
                pycache_dir.rmdir()
            except Exception as e:
                print(f"Failed to remove {pycache_dir}: {e}")


def find_by_extension(folder: str, extension: str) -> Path | None:
    folder_path = Path(folder)
    for file in folder_path.glob(f"*.{extension.lstrip('.')}"):
        return file
    return None


def convert_tuples_to_lists(obj):
    if isinstance(obj, tuple):
        return [convert_tuples_to_lists(i) for i in obj]
    if isinstance(obj, list):
        return [convert_tuples_to_lists(i) for i in obj]
    if isinstance(obj, dict):
        return {k: convert_tuples_to_lists(v) for k, v in obj.items()}
    return obj


def convert_lists_to_tuples(obj):
    if isinstance(obj, list):
        return tuple(convert_lists_to_tuples(i) for i in obj)
    if isinstance(obj, dict):
        return {k: convert_lists_to_tuples(v) for k, v in obj.items()}
    return obj
