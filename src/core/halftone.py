from abc import ABC, abstractmethod
import math
from typing import Iterator

from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np

from core.specs import HalftoneSpec
from core.dot import Dot
from utils.helpers import norm_intensity


class Halftone(ABC):
    """Base halftone."""

    def __init__(self, spec: HalftoneSpec):
        self.spec = spec
        self.spacing = spec.dpi / spec.lpi

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(spec={repr(self.spec)})"

    def generate(self, image: Image.Image, dot: Dot, angle: float) -> Image:
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
            intensity = max(0.0, min(1.0, norm_intensity(int(avg))))

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


class AMHalftone(Halftone):
    """Uniform cell grid."""

    def _iter_grid_points(self, resized_image, angle=0):
        width, height = resized_image.size
        angle_rad = math.radians(angle)

        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        cx, cy = width / 2, height / 2

        # Rotated bounds of image
        corners = [
            (-cx, -cy),
            (width - cx, -cy),
            (-cx, height - cy),
            (width - cx, height - cy),
        ]

        rotated_x = []
        rotated_y = []
        for x, y in corners:
            rx = x * cos_a + y * sin_a
            ry = -x * sin_a + y * cos_a
            rotated_x.append(rx)
            rotated_y.append(ry)

        min_rx = min(rotated_x)
        max_rx = max(rotated_x)
        min_ry = min(rotated_y)
        max_ry = max(rotated_y)

        nx = int(math.ceil((max_rx - min_rx) / self.spacing))
        ny = int(math.ceil((max_ry - min_ry) / self.spacing))

        for i in range(nx + 1):
            for j in range(ny + 1):
                rx = min_rx + i * self.spacing
                ry = min_ry + j * self.spacing

                # Inverse rotation to image space
                dx = rx * cos_a - ry * sin_a
                dy = rx * sin_a + ry * cos_a

                x = dx + cx
                y = dy + cy

                if 0 <= x < width and 0 <= y < height:
                    yield x, y


class DitherHalftone(Halftone):
    """Floyd-Steinberg dithered cell grid."""

    def _iter_grid_points(
        self, resized_image, angle=0
    ) -> Iterator[tuple[float, float]]:
        spacing = int(self.spacing)
        w, h = resized_image.size

        # Downscale to dot grid size
        small = resized_image.resize(
            (w // spacing, h // spacing),
            resample=Image.Resampling.LANCZOS,
        ).convert("L")

        arr = np.array(small, dtype=np.float32) / 255.0
        height, width = arr.shape
        out = np.zeros_like(arr)

        # Floyd-Steinberg error diffusion
        for y in range(height):
            for x in range(width):
                old_pixel = arr[y, x]
                new_pixel = 1.0 if old_pixel >= 0.5 else 0.0
                out[y, x] = new_pixel
                error = old_pixel - new_pixel

                if x + 1 < width:
                    arr[y, x + 1] += error * 7 / 16
                if x - 1 >= 0 and y + 1 < height:
                    arr[y + 1, x - 1] += error * 3 / 16
                if y + 1 < height:
                    arr[y + 1, x] += error * 5 / 16
                if x + 1 < width and y + 1 < height:
                    arr[y + 1, x + 1] += error * 1 / 16

        # Yield positions for dots where dither map is "on"
        for j in range(height):
            for i in range(width):
                if out[j, i] >= 1.0:
                    x = (i + 0.5) * spacing
                    y = (j + 0.5) * spacing
                    yield (x, y)


class ThresholdHalftone(Halftone):
    """Threshold-based halftone."""

    def _iter_grid_points(
        self, resized_image, angle=0
    ) -> Iterator[tuple[float, float]]:
        grayscale = resized_image.convert("L")
        pixels = np.array(grayscale)

        height, width = pixels.shape

        for y in range(height):
            for x in range(width):
                if pixels[y, x] > 127:
                    yield float(x), float(y)
