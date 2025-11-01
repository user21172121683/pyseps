# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass


@dataclass
class DotSpec:
    gradient: bool = False
    gain: float = 0.0
    modulate: bool = True
