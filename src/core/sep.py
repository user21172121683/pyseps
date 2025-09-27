from abc import ABC, abstractmethod

from PIL import Image


class Sep(ABC):
    def __init__(self, image: Image):
        self.image = image
        self.separations = {}

    @abstractmethod
    def split(self):
        pass


class ProcessSep(Sep):
    def split(self):
        """Split CMYK image into C, M, Y, K channels."""
        if self.image.mode.upper() != "CMYK":
            image = self.image.convert("CMYK")
        else:
            image = self.image
        c, m, y, k = image.split()
        self.separations = {"C": c, "M": m, "Y": y, "K": k}
