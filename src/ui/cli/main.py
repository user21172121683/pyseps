# SPDX-License-Identifier: AGPL-3.0-or-later

import argparse
from pathlib import Path

from constants import Globals, Defaults
from core import Seps


class AppCLI:
    """Pyseps command-line interface."""

    def __init__(self):
        self.parser = argparse.ArgumentParser(description="pyseps CLI")
        self._setup_arguments()

    def _setup_arguments(self):
        self.parser.add_argument("-f", "--file", required=True, help="Input file")
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
            "-F",
            "--format",
            choices=list(Globals.IMAGE_FORMATS.keys()),
            default="tiff",
            help="Output file format",
        )

    def run(self):
        args = self.parser.parse_args()
        self.handle(args)

    def handle(self, args):
        seps = Seps()
        file = Path(args.file).resolve()
        seps.load(file)

        if args.template:
            template = Path(args.template)
        else:
            yaml_files = list(file.parent.glob("*.yaml")) + list(
                file.parent.glob("*.yml")
            )
            if yaml_files:
                template = yaml_files[0]
            else:
                template = Globals.TEMPLATE

        try:
            seps.import_template(template)
        except Exception as e:
            print(f"Error importing template: {e}")
            return

        seps.generate()

        try:
            seps.save(
                splits=args.splits,
                halftones=args.halftones,
                fmt=args.format,
                output_folder=Path(args.output),
            )
        except Exception as e:
            print(f"Error saving: {e}")
