from pathlib import Path

from PIL import Image

from constants import DEFAULT_TEMPLATE, TEMPLATES_DIR, DEFAULT_OUTPUT_DIR

from core.fileops import (
    load_image_and_template,
    save_separations,
    import_template,
    export_template,
)
from core.pipeline import SepPipeline
from .spec import SepSpec


class Sep:
    def __init__(self, image_path: str | Path | None = None):
        self.spec = SepSpec()
        self.image: Image.Image | None = None
        self.folder: Path | None = None
        self.separations: dict[str, tuple[Image.Image, Image.Image]] = {}

        try:
            self.import_template(DEFAULT_TEMPLATE)
        except Exception as e:
            print(f"Warning: failed to load default template: {e}")

        if image_path:
            self.load(image_path)

    def __repr__(self):
        return (
            f"<Sep("
            f"spec={self.spec}, "
            f"image={'loaded' if self.image else 'None'}, "
            f"separations={len(self.separations)}, "
            f"folder='{self.folder}'"
            f")>"
        )

    def load(self, image_path: str | Path):
        self.image, self.folder, local_template = load_image_and_template(image_path)
        if local_template:
            self.import_template(local_template)

    def save(self, output_folder: str = DEFAULT_OUTPUT_DIR):
        save_separations(
            self.separations, self.folder, self.spec.halftone_spec.dpi, output_folder
        )

    def generate(self):
        if self.image is None:
            raise RuntimeError("No image loaded. Use load first.")
        print(self.spec)
        pipeline = SepPipeline(self.spec)

        try:
            self.separations = pipeline.run(self.image)
        except Exception as e:
            raise RuntimeError(f"Failed to generate separations: {e}") from e

    def export_template(
        self, filename: str = "template.yaml", folder: Path = TEMPLATES_DIR
    ):
        export_template(filename=filename, folder=folder, **self.spec.__dict__)

    def import_template(self, path: Path):
        template_data = import_template(path)
        for key, value in template_data.items():
            if value is not None:
                setattr(self.spec, key, value)
