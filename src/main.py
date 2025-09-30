import sys
from ui import AppCLI, AppGUI
from constants import BANNER


def main():
    print(BANNER)
    if len(sys.argv) == 1:
        app = AppGUI()
    else:
        app = AppCLI()
    app.run()


if __name__ == "__main__":
    main()
