# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import Path

from constants import Globals, Defaults

from .image import ImageManager
from .template import TemplateManager
from .pipeline import Pipeline


class Seps:
    """Main separation orchestrator."""

    def __init__(self):
        self.template = TemplateManager()
        self.image = ImageManager()
        self.pipeline = Pipeline()

    def load(self, image_path: Path):
        self.image.load(path=image_path)

    def save(
        self,
        *,
        splits: bool = Defaults.SAVE_SPLITS,
        screens: bool = Defaults.SAVE_HALFTONES,
        preview: bool = Defaults.SAVE_PREVIEW,
        fmt: str = Defaults.FORMAT,
        dpi: int = 300,
        output_folder: str = Defaults.OUTPUT,
    ):
        self.image.save(
            splits=splits,
            screens=screens,
            preview=preview,
            fmt=fmt,
            dpi=dpi,
            output_folder=output_folder,
        )

    def export_template(self, path: Path = Globals.TEMPLATES_DIR / "template.yaml"):
        self.template.save_yaml(path=path)

    def import_template(self, path: Path):
        self.template.load_yaml(path=path)

    def generate(self):
        if not self.image.image:
            raise RuntimeError("No image loaded. Use load() first.")
        self.image.separations = self.pipeline.process_image(
            image=self.image.image, template=self.template
        )
