# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass


@dataclass
class PreSpec:
    grayscale: bool = False
    resize: tuple[int, int] = (0, 0)
