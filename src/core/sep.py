from abc import ABC, abstractmethod
from PIL import Image, ImageOps
import numpy as np


class Sep(ABC):
    def __init__(self, image: Image):
        self.image = image
        self.separations = {}

    def _ensure_mode(self, fmt):
        if self.image.mode.upper() != fmt:
            image = self.image.convert(fmt)
        else:
            image = self.image
        return image

    @abstractmethod
    def split(self):
        pass


class ProcessSep(Sep):
    def split(self):
        """Split CMYK image into C, M, Y, K channels."""
        image = self._ensure_mode("CMYK")
        c, m, y, k = image.split()
        self.separations = {"C": c, "M": m, "Y": y, "K": k}


class RGBSep(Sep):
    def split(self):
        """Split image into R, G, B (and A) channels."""
        image = self._ensure_mode("RGBA" if self.image.mode == "RGBA" else "RGB")
        channels = image.split()

        r, g, b = channels[:3]

        self.separations = {"R": r, "G": g, "B": b}

        if image.mode == "RGBA" and len(channels) == 4:
            a = channels[3]
            self.separations["A"] = a


class LSep(Sep):
    def split(self):
        """Return grayscale image."""
        image = self._ensure_mode("L")
        l = ImageOps.invert(image)
        self.separations = {"L": l}


class SimProcessSep(Sep):
    def __init__(self, image: Image, tones: dict[str, tuple[int, int, int]]):
        super().__init__(image)
        self.tones = tones

    def split(self):
        """Simulate spot color separation using color distance."""

        # Ensure image is RGB
        rgb_image = self._ensure_mode("RGB")
        img_array = np.array(rgb_image).astype(np.float32)  # shape: (H, W, 3)

        separations = {}

        for name, tone_rgb in self.tones.items():
            # Calculate Euclidean distance to the tone color
            tone_array = np.array(tone_rgb).astype(np.float32).reshape((1, 1, 3))
            dist = np.linalg.norm(img_array - tone_array, axis=2)

            # Normalize distance to [0, 255], invert so that closer = more ink
            dist = 1 - (dist / np.sqrt(3 * (255**2)))  # Now in [0,1]
            mask = (dist * 255).clip(0, 255).astype(np.uint8)

            # Convert to grayscale image
            separations[name] = Image.fromarray(mask, mode="L")

        self.separations = separations
