# SPDX-License-Identifier: AGPL-3.0-or-later

from PIL import Image
import numpy as np

from modules import Halftone

from .template import TemplateManager
from .image import Separation


class Pipeline:
    """Stateless image separation and preview generation."""

    @staticmethod
    def process_image(
        image: Image.Image, template: TemplateManager
    ) -> list[Separation]:
        """Generate separations with screens from a given image and template."""

        split = template.split_type(template.split_spec)
        screen = template.screen_type(template.screen_spec)
        dot = template.dot_type(template.dot_spec)
        halftone = Halftone(
            dot=dot, hardmix=screen.spec.hardmix, spacing=screen.spacing
        )

        split_result = split.split(image)
        angles = split.spec.angles

        separations = []
        for i, (name, split_img) in enumerate(split_result.items()):
            angle = angles[i % len(angles)]
            screen_img = screen.compute_intensity_map(split_img, angle)
            halftone_img = halftone.render(
                intensity_map=screen_img,
                base_image=split_img,
                angle=angle,
                ppi=screen.spec.ppi,
                dpi=screen.spec.dpi,
            )
            separation = Separation(
                name=name,
                split=split_img,
                screen=screen_img,
                halftone=halftone_img,
                angle=angle,
                tone=split.spec.tones[i],
            )
            separations.append(separation)

        return separations

    @staticmethod
    def create_preview(
        separations: list[Separation],
        substrate: tuple[int, int, int],
    ) -> Image.Image | None:
        """Combine separations into a preview image."""

        if not separations or not substrate:
            return None

        try:
            width, height = separations[0].halftone.size
            image_array = np.full((height, width, 3), substrate, dtype=np.uint8)

            for separation in separations:
                arr = np.array(separation.halftone)
                mask = arr == 0
                image_array[mask] = separation.tone

            return Image.fromarray(image_array)
        except Exception as e:
            raise RuntimeError(f"Pipeline preview generation failed: {e}") from e
