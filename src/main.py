import sys
from pathlib import Path
from ui import AppCLI, AppGUI
from constants import BANNER

def clear_pycache():
    # Don't clear pycache if running as a frozen binary
    if getattr(sys, 'frozen', False):
        return

    for pycache_dir in Path(".").rglob("__pycache__"):
        if pycache_dir.is_dir():
            try:
                for item in pycache_dir.iterdir():
                    item.unlink()
                pycache_dir.rmdir()
            except Exception as e:
                print(f"Failed to remove {pycache_dir}: {e}")

def main():
    print(BANNER)
    try:
        if len(sys.argv) == 1:
            app = AppGUI()
        else:
            app = AppCLI()
        app.run()
    finally:
        clear_pycache()

if __name__ == "__main__":
    main()
