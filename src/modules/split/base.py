# SPDX-License-Identifier: AGPL-3.0-or-later

from abc import ABC, abstractmethod

from .spec import SplitSpec


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
