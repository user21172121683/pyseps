from abc import ABC, abstractmethod
from PIL import Image, ImageOps


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
