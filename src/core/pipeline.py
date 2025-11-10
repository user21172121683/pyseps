# SPDX-License-Identifier: AGPL-3.0-or-later

from PIL import Image
import numpy as np

from .template import TemplateManager
from .image import ImageManager, Separation


class Pipeline:
    """Image separation and preview generation pipeline."""

    def __init__(self, image: ImageManager, template: TemplateManager):
        self.image = image
        self.template = template

        # Internal modules
        self._split = None
        self._screen = None
        self._dot = None

    def run(self):
        """Orchestrates the full pipeline."""

        self._instantiate_modules()
        self._process_image()
        self._render_preview()

    def _instantiate_modules(self):
        """Create split, screen, and dot instances from template specs."""

        self._split = self.template.split_type(self.template.split_spec)
        self._screen = self.template.screen_type(self.template.screen_spec)
        self._dot = self.template.dot_type(self.template.dot_spec, self.template.screen_spec)

    def _process_image(self):
        """Split the input image and compute screen and halftone for each separation."""

        split_result = self._split.split(self.image.original)
        angles = self._split.spec.angles
        tones = self._split.spec.tones

        self.image.separations = []

        for i, (name, split_img) in enumerate(split_result.items()):
            angle = angles[i % len(angles)]
            tone = tones[i]

            # Compute screen
            intensity_flow_array = self._screen.compute_intensity_flow_array(
                split_img, angle
            )

            # Compute halftone
            halftone_img = self._dot.render(
                intensity_flow_array=intensity_flow_array,
                base_image=split_img,
            )

            separation = Separation(
                name=name,
                split=split_img,
                screen=intensity_flow_array,
                halftone=halftone_img,
                angle=angle,
                tone=tone,
            )
            self.image.separations.append(separation)

    def _render_preview(self) -> None:
        """Combine separations into a preview image."""
        if not self.image.separations or not self.template.split_spec.substrate:
            self.image.preview = None
            return

        try:
            height, width = self.image.separations[0].halftone.shape
            image_array = (
                np.full(
                    (height, width, 3),
                    self.template.split_spec.substrate,
                    dtype=np.float32,
                )
                / 255.0
            )
            for separation in self.image.separations:
                halftone = separation.halftone.astype(np.float32)
                mask = 1.0 - (halftone / 255.0)
                mask = mask[..., np.newaxis]

                tone = np.array(separation.tone, dtype=np.float32) / 255.0

                image_array = image_array * (1 - mask * (1 - tone))
                self.image.preview = Image.fromarray(
                    np.clip(image_array * 255, 0, 255).astype(np.uint8)
                )
        except Exception as e:
            raise RuntimeError(f"Pipeline preview generation failed: {e}") from e
