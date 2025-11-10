# SPDX-License-Identifier: AGPL-3.0-or-later

import argparse
from pathlib import Path
import logging

from log import setup_logging
from constants import Globals, Defaults
from core import Seps


class AppCLI:
    """Pyseps command-line interface."""

    def __init__(self):
        self.parser = argparse.ArgumentParser(description="pyseps CLI")
        self._setup_arguments()

    def _setup_arguments(self):
        self.parser.add_argument("file", help="Input file")
        log_group = self.parser.add_argument_group(
            "Logging Verbosity", "Set module chattiness"
        )
        log_group.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="Increase verbosity (-v for INFO, -vv for DEBUG)",
        )
        log_group.add_argument(
            "-q", "--quiet", action="store_true", help="Suppress non-error output"
        )

        opt_group = self.parser.add_argument_group(
            "Optional Features", "Enable or disable extra features"
        )
        opt_group.add_argument("-t", "--template", help="Template file")
        opt_group.add_argument(
            "-o", "--output", default=Defaults.OUTPUT, help="Output folder"
        )
        opt_group.add_argument(
            "-H",
            "--halftones",
            action="store_true",
            default=Defaults.SAVE_HALFTONES,
            help="Enable saving halftones",
        )
        opt_group.add_argument(
            "-S",
            "--splits",
            action="store_true",
            default=Defaults.SAVE_SPLITS,
            help="Enable saving splits",
        )
        opt_group.add_argument(
            "-P",
            "--preview",
            action="store_true",
            default=Defaults.SAVE_PREVIEW,
            help="Enable saving colorized preview",
        )
        opt_group.add_argument(
            "-f",
            "--format",
            choices=list(Globals.IMAGE_FORMATS.keys()),
            default="tiff",
            help="Output file format",
        )

    def run(self):
        args = self.parser.parse_args()
        setup_logging(args.verbose, args.quiet)
        self.handle(args)

    def handle(self, args):
        logger = logging.getLogger(__name__)

        if not (args.splits or args.halftones or args.preview):
            logger.warning(
                "You should enable at least -S/--splits, -H/--halftones, or -P/--preview."
            )
            return

        seps = Seps()
        input_file = Path(args.file).resolve()
        logger.info("Loading file: %s", input_file)
        seps.load(input_file)

        # Determine template
        if args.template:
            template = Path(args.template)
        else:
            yaml_files = list(input_file.parent.glob("*.yaml")) + list(
                input_file.parent.glob("*.yml")
            )
            if yaml_files:
                template = yaml_files[0]
            else:
                template = Globals.TEMPLATE

        logger.info("Using template: %s", template)

        # Import template
        try:
            seps.import_template(template)
        except Exception as e:
            logger.error("Error importing template: %s", e)
            return

        # Generate separations
        logger.info("Generating separations...")
        seps.generate()

        # Save outputs
        logger.info("Saving outputs to %s", args.output)
        try:
            seps.save(
                splits=args.splits,
                halftones=args.halftones,
                preview=args.preview,
                fmt=args.format,
                output_folder=Path(args.output),
            )
        except Exception as e:
            logger.error("Error saving: %s", e)
