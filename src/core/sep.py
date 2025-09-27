from abc import ABC, abstractmethod

from PIL import Image


class Sep(ABC):
    def __init__(self, image: Image):
        self.image = image
        self.separations = {}

    @abstractmethod
    def split(self):
        pass
