# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Globals:
    APP_NAME = "pyseps"
    ROOT = Path(__file__).resolve().parents[1]
    TEMPLATES_DIR = ROOT / "src" / "templates"
    TEMPLATE = TEMPLATES_DIR / "default.yaml"
    IMAGE_FORMATS = {
        "tiff": {
            "L": {"compression": "tiff_deflate"},
            "1": {"compression": "group4"},
        },
        "png": {
            "L": {"optimize": True},
            "1": {"optimize": True},
        },
        "jpeg": {
            "L": {"quality": 95},
            "1": {"quality": 95},
        },
        "pdf": {
            "L": {},
            "1": {},
        },
    }
    BANNER = """
+      _/_/_/    _/    _/    _/_/_/    _/_/    _/_/_/      _/_/_/ +
      _/    _/  _/    _/  _/_/      _/_/_/_/  _/    _/  _/_/       
     _/    _/  _/    _/      _/_/  _/        _/    _/      _/_/    
    _/_/_/      _/_/_/  _/_/_/      _/_/_/  _/_/_/    _/_/_/       
   _/--------------_/----------------------_/-----------------     
+ _/          _/_/                        _/                      +
"""


@dataclass(frozen=True)
class Defaults:
    OUTPUT = "seps"
    FORMAT = "tiff"
    SAVE_HALFTONES = True
    SAVE_SPLITS = False
    SAVE_PREVIEW = False
