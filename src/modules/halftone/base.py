# SPDX-License-Identifier: AGPL-3.0-or-later

from abc import ABC, abstractmethod
from typing import Iterator

from PIL import Image, ImageDraw, ImageOps, ImageFilter
import numpy as np

from modules.dot import DotBase
from .spec import HalftoneSpec


class HalftoneBase(ABC):
    """Base halftone."""

    def __init__(self, spec: HalftoneSpec):
        self.spec = spec
        self.spacing = spec.dpi / spec.lpi

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(spec={repr(self.spec)})"

    def generate(self, image: Image.Image, dot: DotBase, angle: float) -> Image:
        """Draw modulated dots based on local image intenity."""

        resized_image = self._resize(image)

        mode = "L" if self.spec.hardmix else "1"
        halftone = Image.new(mode, resized_image.size, "white")
        canvas = ImageDraw.Draw(halftone)

        pixels = np.array(resized_image)
        width, height = resized_image.size

        for x, y in self._iter_grid_points(resized_image, angle):
            block = self._get_clipped_block(x, y, width, height, pixels)
            if block is None or block.size == 0:
                continue

            avg = np.mean(block)
            intensity = max(0.0, min(1.0, max(0.0, min(1.0, int(avg) / 255.0))))

            dot.draw(
                canvas=canvas,
                center=(x, y),
                size=self.spacing,
                angle=angle,
                intensity=intensity,
            )

        if self.spec.hardmix:
            halftone = self._hardmix(resized_image, halftone)

        return halftone

    def _resize(self, image: Image) -> tuple[Image, int]:
        """Resize image to match spec.dpi and return resized image."""
        ppi = image.info.get("dpi", (300, 300))[0] or self.spec.ppi or 300
        if ppi != self.spec.dpi:
            scale = self.spec.dpi / ppi
            new_size = tuple(int(dim * scale) for dim in image.size)
            resized_image = image.resize(new_size, resample=Image.Resampling.LANCZOS)
        else:
            resized_image = image
        return resized_image

    def _get_clipped_block(
        self, x: float, y: float, width: int, height: int, pixels: np.ndarray
    ) -> np.ndarray | None:
        """Return the pixel block centered at (x, y), clipped to image bounds."""
        half = self.spacing / 2
        x0, y0 = int(x - half), int(y - half)
        x1, y1 = int(x + half), int(y + half)

        x0_clip = max(0, x0)
        y0_clip = max(0, y0)
        x1_clip = min(width, x1)
        y1_clip = min(height, y1)

        if x0_clip >= x1_clip or y0_clip >= y1_clip:
            return None

        return pixels[y0_clip:y1_clip, x0_clip:x1_clip]

    def _hardmix(self, resized_image, halftone):
        base_array = np.array(ImageOps.invert(resized_image), dtype=np.uint16)
        mask_array = np.array(
            halftone.filter(ImageFilter.GaussianBlur(radius=self.spacing / 10)),
            dtype=np.uint16,
        )
        combined = base_array + mask_array
        result_array = np.where(combined >= 255, 255, 0).astype(np.uint8)
        return Image.fromarray(result_array, mode="L").convert("1")

    @abstractmethod
    def _iter_grid_points(
        self, resized_image, angle=0
    ) -> Iterator[tuple[float, float]]:
        """Yield center positions for dot placement."""
        raise NotImplementedError
