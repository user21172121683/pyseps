# SPDX-License-Identifier: AGPL-3.0-or-later

import sys

from ui import AppCLI, AppGUI
from constants import Globals


def main():
    print(Globals.BANNER)
    try:
        app = AppGUI() if len(sys.argv) == 1 else AppCLI()
        app.run()
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
