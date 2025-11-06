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

class SplitBase(ABC):
    def __init__(self, spec: SplitSpec):
        self.spec = spec

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(spec={repr(self.spec)})"

    def _ensure_mode(self, image, mode):
        if image.mode.upper() != mode:
            image = image.convert(mode)
        return image

    @abstractmethod
    def split(self, image):
        pass


@MODULE_REGISTRY.register("process", "cmyk")
class ProcessSplit(SplitBase):
    def split(self, image):
        """Split CMYK image into C, M, Y, K channels."""
        image = self._ensure_mode(image, "CMYK")
        self.spec.tones = ((255, 0, 0), (0, 255, 0), (0, 0, 255))
        c, m, y, k = image.split()
        return {"C": c, "M": m, "Y": y, "K": k}


@MODULE_REGISTRY.register("rgb")
class RGBSplit(SplitBase):
    def split(self, image):
        """Split image into R, G, B (and A) channels."""
        image = self._ensure_mode(image, "RGBA" if image.mode == "RGBA" else "RGB")
        channels = image.split()

        self.spec.tones = (
            (0, 255, 255),
            (255, 0, 255),
            (255, 255, 0),
            (0, 0, 0),
        )

        r, g, b = channels[:3]

        separations = {"R": r, "G": g, "B": b}

        if image.mode == "RGBA" and len(channels) == 4:
            separations["A"] = channels[3]

        return separations


@MODULE_REGISTRY.register("gray", "grey", "grayscale", "greyscale")
class LSplit(SplitBase):
    def split(self, image):
        """Return grayscale image."""
        image = self._ensure_mode(image, "L")
        self.spec.tones = None
        l = ImageOps.invert(image)
        return {"L": l}


@MODULE_REGISTRY.register(
    "simulatedprocess", "simulated process", "sim", "simprocess", "simp"
)
class SimProcessSplit(SplitBase):
    def split(self, image):
        """Simulate spot color separation using color distance,
        optionally accounting for a substrate color."""

        # Ensure image is RGB
        rgb_image = self._ensure_mode(image, "RGB")
        img_array = np.array(rgb_image).astype(np.float32)  # shape: (H, W, 3)

        # Optional substrate color
        if self.spec.substrate is not None:
            substrate_array = (
                np.array(self.spec.substrate).astype(np.float32).reshape((1, 1, 3))
            )
            substrate_dist = np.linalg.norm(img_array - substrate_array, axis=2)
            substrate_dist = substrate_dist / np.sqrt(
                3 * (255**2)
            )  # Normalize to [0,1]
            substrate_mask = substrate_dist.clip(
                0, 1
            )  # Closer to substrate => lower value
        else:
            substrate_mask = None

        separations = {}

        for name, tone_rgb in self.spec.tones.items():
            # Tone distance
            tone_array = np.array(tone_rgb).astype(np.float32).reshape((1, 1, 3))
            tone_dist = np.linalg.norm(img_array - tone_array, axis=2)
            tone_dist = 1 - (tone_dist / np.sqrt(3 * (255**2)))  # Closer => more ink
            tone_mask = tone_dist.clip(0, 1)

            if substrate_mask is not None:
                # Reduce ink where substrate already contributes
                tone_mask *= substrate_mask  # Avoid printing over substrate

            # Scale to 8-bit grayscale
            mask = (tone_mask * 255).astype(np.uint8)
            separations[name] = Image.fromarray(mask, mode="L")

        return separations


@MODULE_REGISTRY.register("spot")
class SpotSplit(SplitBase):
    def split(self, image):
        """Split image into spot color channels based on color similarity (within threshold),
        optionally avoiding substrate-colored regions."""

        rgb_image = self._ensure_mode(image, "RGB")
        img_array = np.array(rgb_image).astype(np.int16)

        separations = {}

        # Compute distance to substrate if provided
        if self.spec.substrate is not None:
            substrate_array = (
                np.array(self.spec.substrate).reshape((1, 1, 3)).astype(np.int16)
            )
            substrate_dist = np.linalg.norm(img_array - substrate_array, axis=2)
        else:
            substrate_dist = None

        for name, color in self.spec.tones.items():
            color_array = np.array(color).reshape((1, 1, 3)).astype(np.int16)
            color_dist = np.linalg.norm(img_array - color_array, axis=2)

            # Initial match: within threshold to spot color
            mask = color_dist <= self.spec.threshold

            if substrate_dist is not None:
                # Also require that pixel is not too close to the substrate
                mask &= substrate_dist > self.spec.threshold

            # Convert boolean mask to binary image
            separations[name] = Image.fromarray(mask.astype(np.uint8) * 255, mode="L")

        return separations
