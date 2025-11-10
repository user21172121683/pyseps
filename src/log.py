# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import sys
from typing import Literal


def setup_logging(verbosity: Literal[0, 1, 2] = 0, quiet: bool = False):

    # Determine logging level
    if quiet:
        level = logging.ERROR
    elif verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    else:
        level = logging.WARNING

    # Define formatter
    formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Suppress messages from dependencies
    for dep in ["PIL", "cairo", "numpy", "yaml", "pyyaml"]:
        logging.getLogger(dep).setLevel(logging.ERROR)
