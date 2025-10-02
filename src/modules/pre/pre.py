from PIL import Image

from core.registry import MODULE_REGISTRY
from .spec import PreSpec


@MODULE_REGISTRY.register()
class Pre:
    def __init__(self, spec: PreSpec):
        self.spec = spec

    def process(self, image: Image.Image) -> Image.Image:
        if self.spec.grayscale:
            image = image.convert("L")

        if self.spec.resize != (0, 0):
            image = image.resize(self.spec.resize)

        return image
