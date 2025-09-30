import sys
from ui import AppCLI, AppGUI


def main():
    if len(sys.argv) == 1:
        app = AppGUI()
    else:
        app = AppCLI()
    app.run()


if __name__ == "__main__":
    main()
