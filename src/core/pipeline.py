# SPDX-License-Identifier: AGPL-3.0-or-later

from PIL import Image
import numpy as np

from .template import TemplateManager


class Pipeline:
    """Stateless image separation and preview generation."""

    @staticmethod
    def process_image(
        image: Image.Image, template: TemplateManager
    ) -> dict[str, tuple[Image.Image, Image.Image]]:
        """Generate separations with screens from a given image and template."""

        split = template.split_type(template.split_spec)
        screen = template.screen_type(template.screen_spec)
        dot = template.dot_type(template.dot_spec)

        split_result = split.split(image)
        angles = split.spec.angles

        separations = {}
        for i, (name, split_img) in enumerate(split_result.items()):
            angle = angles[i % len(angles)]
            screen_img = screen.generate(split_img, dot, angle)
            separations[name] = (split_img, screen_img)

        return separations

    @staticmethod
    def create_preview(
        separations: dict[str, tuple[Image.Image, Image.Image]],
        tones: list[tuple[int, int, int]],
        substrate: tuple[int, int, int],
    ) -> Image.Image | None:
        """Combine separations into a preview image."""

        if not separations or not tones or not substrate:
            return None

        try:
            first_size = next(iter(separations.values()))[1].size
            width, height = first_size
            image_array = np.full((height, width, 3), substrate, dtype=np.uint8)

            for i, (_, (_, screen)) in enumerate(separations.items()):
                arr = np.array(screen.convert("L"))
                if arr.shape != image_array.shape[:2]:
                    arr = np.array(screen.resize((width, height)).convert("L"))
                mask = arr == 0
                image_array[mask] = tones[i]

            return Image.fromarray(image_array)
        except Exception as e:
            raise RuntimeError(f"Pipeline preview generation failed: {e}") from e
