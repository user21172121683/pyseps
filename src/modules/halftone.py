# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFilter

from .dot import DotBase


class Halftone:
    """Renders halftone dots using precomputed intensities from a ScreenBase."""

    def __init__(self, dot: DotBase, hardmix: bool = False, spacing: float = 1.0):
        self.dot = dot
        self.hardmix = hardmix
        self.spacing = spacing

    def render(
        self,
        intensity_map: list[tuple[float, float, float]],
        base_image: Image.Image,
        ppi: int,
        dpi: int,
        angle: float,
    ) -> Image.Image:
        """Render a halftone pattern from intensity data."""

        scale = dpi / ppi

        scaled_base = self._resize_to_dpi(base_image, dpi, ppi)
        image_size = scaled_base.size

        mode = "L" if self.hardmix else "1"
        result = Image.new(mode, image_size, "white")
        canvas = ImageDraw.Draw(result)

        for x, y, intensity in intensity_map:
            self.dot.draw(
                canvas=canvas,
                center=(x * scale, y * scale),
                size=self.spacing * scale,
                angle=angle,
                intensity=intensity,
            )

        if self.hardmix:
            result = self._hardmix(scaled_base, result)

        return result

    def _resize_to_dpi(self, image: Image.Image, dpi: int, ppi: int) -> Image.Image:
        """Resize the input image to match the screen DPI."""

        ppi = image.info.get("dpi")[0] or ppi
        if ppi != dpi:
            scale = dpi / ppi
            new_size = tuple(int(dim * scale) for dim in image.size)
            resized = image.resize(new_size, resample=Image.Resampling.LANCZOS)
            resized.info["dpi"] = (dpi, dpi)
            return resized
        return image

    def _hardmix(
        self, base_image: Image.Image, screen_image: Image.Image
    ) -> Image.Image:
        base_array = np.array(ImageOps.invert(base_image.convert("L")), dtype=np.uint16)
        mask_array = np.array(
            screen_image.filter(ImageFilter.GaussianBlur(radius=self.spacing / 10)),
            dtype=np.uint16,
        )
        combined = base_array + mask_array
        result_array = np.where(combined >= 255, 255, 0).astype(np.uint8)
        return Image.fromarray(result_array, mode="L").convert("1")
