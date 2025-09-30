import argparse

from PIL import Image

from core.sep import Sep


class AppCLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="My Tool CLI")
        self._setup_arguments()

    def _setup_arguments(self):
        self.parser.add_argument("-f", "--file", required=True, help="Input file")
        self.parser.add_argument("-t", "--template", help="Template file")

    def run(self):
        args = self.parser.parse_args()
        self.handle(args)

    def handle(self, args):
        sep = Sep(Image.open(args.file))

        if args.template:
            try:
                sep.import_template(args.template)
            except Exception as e:
                print(f"Error importing template: {e}")
                return

        try:
            sep.save()
        except Exception as e:
            print(f"Error saving: {e}")
