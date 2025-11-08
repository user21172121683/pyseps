# SPDX-License-Identifier: AGPL-3.0-or-later

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageOps

from core.registry import MODULE_REGISTRY


@dataclass
class SplitSpec:
    tones: tuple[tuple[int, int, int]] | None = field(
        default_factory=lambda: (
            (0, 255, 255),
            (255, 0, 255),
            (255, 255, 0),
            (0, 0, 0),
        )
    )
    threshold: int = 30
    substrate: tuple[int, int, int] = (255, 255, 255)
    angles: tuple[int, ...] = (15, 75, 0, 45)


@dataclass
class ProcessSplitSpec(SplitSpec):
    pass


@dataclass
class RGBSplitSpec(SplitSpec):
    pass


@dataclass
class LSplitSpec(SplitSpec):
    pass


@dataclass
class SimProcessSplitSpec(SplitSpec):
    pass


@dataclass
class SpotSplitSpec(SplitSpec):
    pass


class SplitBase(ABC):
    def __init__(self, spec: SplitSpec):
        self.spec = spec

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(spec={repr(self.spec)})"

    def _ensure_mode(self, image: Image.Image, mode: str):
        if image.mode.upper() != mode:
            image = image.convert(mode)
        return image

    @abstractmethod
    def split(self, image: Image.Image):
        pass


@MODULE_REGISTRY.register("process", "cmyk", spec_cls=ProcessSplitSpec)
class ProcessSplit(SplitBase):
    def split(self, image: Image.Image):
        """Split CMYK image into C, M, Y, K channels."""

        self.spec.tones = ((0, 255, 255), (255, 0, 255), (255, 255, 0), (0, 0, 0))
        image = self._ensure_mode(image, "CMYK")
        c, m, y, k = image.split()
        return {
            "C": np.array(c, dtype=np.uint8),
            "M": np.array(m, dtype=np.uint8),
            "Y": np.array(y, dtype=np.uint8),
            "K": np.array(k, dtype=np.uint8),
        }


@MODULE_REGISTRY.register("rgb", spec_cls=RGBSplitSpec)
class RGBSplit(SplitBase):
    def split(self, image: Image.Image):
        """Split image into R, G, B channels."""

        self.spec.tones = ((255, 0, 0), (0, 255, 0), (0, 0, 255))
        image = self._ensure_mode(image, "RGB")
        r, g, b = image.split()
        return {
            "R": np.array(r, dtype=np.uint8),
            "G": np.array(g, dtype=np.uint8),
            "B": np.array(b, dtype=np.uint8),
        }


@MODULE_REGISTRY.register(
    "gray", "grey", "grayscale", "greyscale", "l", spec_cls=LSplitSpec
)
class LSplit(SplitBase):
    def split(self, image: Image):
        """Return grayscale image."""

        self.spec.tones = (0, 0, 0)
        image = self._ensure_mode(image, "L")
        l = ImageOps.invert(image)
        return {"L": np.array(l, dtype=np.uint8)}


@MODULE_REGISTRY.register(
    "simulatedprocess",
    "simulated process",
    "sim",
    "simprocess",
    "simp",
    spec_cls=SimProcessSplitSpec,
)
class SimProcessSplit(SplitBase):
    def split(self, image: Image.Image):
        """Simulate spot color separation using color distance,
        optionally accounting for a substrate color."""

        # Ensure image is RGB
        rgb_image = self._ensure_mode(image, "RGB")
        img_array = np.array(rgb_image).astype(np.float32)  # shape: (H, W, 3)

        # Optional substrate
        substrate_mask = None
        if self.spec.substrate is not None:
            substrate_array = np.array(self.spec.substrate, dtype=np.float32).reshape(
                (1, 1, 3)
            )
            substrate_dist = np.linalg.norm(img_array - substrate_array, axis=2)
            substrate_mask = substrate_dist / np.sqrt(3 * (255**2))
            substrate_mask = substrate_mask.clip(0, 1)

        separations = {}

        for tone in self.spec.tones:
            tone_array = np.array(tone, dtype=np.float32).reshape((1, 1, 3))
            tone_dist = np.linalg.norm(img_array - tone_array, axis=2)
            tone_mask = (1 - tone_dist / np.sqrt(3 * (255**2))).clip(0, 1)

            if substrate_mask is not None:
                tone_mask *= substrate_mask

            # Convert tone list to tuple so it’s hashable
            separations[tuple(tone)] = (tone_mask * 255).astype(np.uint8)

        return separations


@MODULE_REGISTRY.register("spot", spec_cls=SpotSplitSpec)
class SpotSplit(SplitBase):
    def split(self, image: Image.Image):
        """Split image into spot color channels based on color similarity (within threshold),
        optionally avoiding substrate-colored regions."""

        rgb_image = self._ensure_mode(image, "RGB")
        img_array = np.array(rgb_image).astype(np.int16)

        substrate_dist = None
        if self.spec.substrate is not None:
            substrate_array = np.array(self.spec.substrate, dtype=np.int16).reshape(
                (1, 1, 3)
            )
            substrate_dist = np.linalg.norm(img_array - substrate_array, axis=2)

        separations = {}
        for tone in self.spec.tones:
            tone_array = np.array(tone, dtype=np.int16).reshape((1, 1, 3))
            tone_dist = np.linalg.norm(img_array - tone_array, axis=2)

            mask = tone_dist <= self.spec.threshold
            if substrate_dist is not None:
                mask &= substrate_dist > self.spec.threshold

            separations[tuple(tone)] = mask.astype(np.uint8) * 255

        return separations
