# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import cairo

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
        base_image: np.ndarray,
        ppi: int,
        dpi: int,
        angle: float,
    ) -> np.ndarray:
        """
        Render a halftone pattern from intensity data.
        """

        scale = dpi / ppi
        base_image = self._resize(base_image, dpi, ppi)
        height, width = base_image.shape

        # Create Cairo image surface
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
        ctx = cairo.Context(surface)

        # Fill background white
        ctx.set_source_rgb(1, 1, 1)
        ctx.paint()

        # Draw dots
        for x, y, intensity in intensity_map:
            self.dot.draw(
                ctx=ctx,
                center=(x * scale, y * scale),
                size=self.spacing * scale,
                angle=angle,
                intensity=intensity,
            )

        # Convert Cairo RGB surface to NumPy grayscale
        buf = surface.get_data()
        screen_image = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 4))

        screen_gray = screen_image[:, :, 0]

        if self.hardmix:
            screen_gray = self._hardmix(base_image, screen_gray)

        return screen_gray

    def _hardmix(self, base_image: np.ndarray, screen_gray: np.ndarray) -> np.ndarray:
        """
        Apply hardmix blending of the halftone over the base grayscale image.
        """
        # Invert the base image
        inverted_base = 255 - base_image.astype(int)

        # Combine with the halftone
        combined = inverted_base + screen_gray.astype(int)

        # Apply hardmix threshold
        result = np.where(combined < 255, 0, 255).astype(np.uint8)

        return result

    def _resize(self, image: np.ndarray, dpi: int, ppi: int) -> np.ndarray:
        """Resize the NumPy image array to match the screen DPI (nearest-neighbor)."""
        if ppi != dpi:
            scale = dpi / ppi
            new_height = max(1, int(image.shape[0] * scale))
            new_width = max(1, int(image.shape[1] * scale))
            # Nearest-neighbor resizing
            y_indices = (np.arange(new_height) / scale).astype(int)
            x_indices = (np.arange(new_width) / scale).astype(int)
            resized = image[y_indices[:, None], x_indices]
            return resized
        return image
