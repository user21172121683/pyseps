# SPDX-License-Identifier: AGPL-3.0-or-later

import sys
import argparse
import logging

from log import setup_logging
from constants import Globals

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-v", "--verbose", action="count", default=0)
parser.add_argument("-q", "--quiet", action="store_true")
early_args, _ = parser.parse_known_args()
setup_logging(early_args.verbose, early_args.quiet)
logger = logging.getLogger(__name__)

from ui import AppCLI, AppGUI  # pylint: disable=wrong-import-position


def main():
    print(Globals.BANNER)
    try:
        app = AppGUI() if len(sys.argv) == 1 else AppCLI()
        app.run()
    except Exception:
        logging.exception("An unhandled error occurred:")
        sys.exit(1)


if __name__ == "__main__":
    main()
