from pathlib import Path

from PIL import Image
import numpy as np

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
        self.preview: Image.Image | None = None

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

    def save(self, output_folder: Path | str = DEFAULT_OUTPUT_DIR):
        save_separations(
            self.separations, self.folder, self.spec.halftone_spec.dpi, output_folder
        )

    def colorize_preview(self):
        if not self.image:
            return
        if not self.separations:
            return
        if not self.spec.split_spec.tones:
            return

        try:
            first_key = next(iter(self.separations))

            # Unpack the halftone from the first separation
            first_entry = self.separations[first_key]
            if not (isinstance(first_entry, tuple) and len(first_entry) == 2):
                return
            halftone = first_entry[1]

            width, height = halftone.size

            # Create blank numpy array for RGB image, initialized with substrate color
            image_array = np.full(
                (height, width, 3), self.spec.split_spec.substrate, dtype=np.uint8
            )

            # Check if tones is list and substrate is tuple of length 3
            if not isinstance(self.spec.split_spec.tones, (list, tuple)):
                return
            if not all(len(tone) == 3 for tone in self.spec.split_spec.tones):
                return
            if not (
                isinstance(self.spec.split_spec.substrate, (list, tuple))
                and len(self.spec.split_spec.substrate) == 3
            ):
                return

            # Process each separation and apply tones where needed
            for i, (_, (_, halftone)) in enumerate(self.separations.items()):

                arr = np.array(halftone)

                # Check arr shape matches image_array's first two dims
                if arr.shape != image_array.shape[:2]:
                    return

                # Apply tones where arr == 0
                mask0 = arr == 0
                image_array[mask0] = self.spec.split_spec.tones[i]

            # Convert numpy array to image and save it
            self.preview = Image.fromarray(image_array)

        except Exception as e:
            print(f"Exception occurred: {e}")

    def generate(self):
        if self.image is None:
            raise RuntimeError("No image loaded. Use load first.")
        print(self.spec)
        pipeline = SepPipeline(self.spec)

        try:
            self.separations = pipeline.run(self.image)
            self.colorize_preview()
        except Exception as e:
            raise RuntimeError(f"Failed to generate separations: {e}") from e

    def export_template(
        self, filename: str = "template.yaml", folder: Path | str = TEMPLATES_DIR
    ):
        export_template(filename=filename, folder=folder, **self.spec.__dict__)

    def import_template(self, path: Path):
        template_data = import_template(path)
        for key, value in template_data.items():
            if value is not None:
                setattr(self.spec, key, value)
