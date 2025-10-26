from PIL import Image


class SepPipeline:
    def __init__(self, spec):
        self.spec = spec

    def run(self, image: Image.Image) -> dict[str, tuple[Image.Image, Image.Image]]:
        pre, split, halftone, dot = self._instantiate_classes()
        print("Processing...")

        preprocessed = pre.process(image)

        split_result = split.split(preprocessed)

        separations = {}
        angles = split.spec.angles
        for i, (name, split_img) in enumerate(split_result.items()):
            angle = angles[i % len(angles)]
            halftone_img = halftone.generate(split_img, dot, angle)
            separations[name] = (split_img, halftone_img)

        return separations

    def _instantiate_classes(self):
        pre = self.spec.pre_type(self.spec.pre_spec)
        split = self.spec.split_type(self.spec.split_spec)
        halftone = self.spec.halftone_type(self.spec.halftone_spec)
        dot = self.spec.dot_type(self.spec.dot_spec)
        return pre, split, halftone, dot
