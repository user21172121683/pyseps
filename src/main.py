import sys
from ui import AppCLI, AppGUI
from constants import BANNER
from utils import clear_pycache


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
