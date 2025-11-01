# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "src" / "templates"
DEFAULT_TEMPLATE = TEMPLATES_DIR / "default.yaml"
DEFAULT_OUTPUT_DIR = "seps"
APP_NAME = "pyseps"
BANNER = """
+      _/_/_/    _/    _/    _/_/_/    _/_/    _/_/_/      _/_/_/ +
      _/    _/  _/    _/  _/_/      _/_/_/_/  _/    _/  _/_/       
     _/    _/  _/    _/      _/_/  _/        _/    _/      _/_/    
    _/_/_/      _/_/_/  _/_/_/      _/_/_/  _/_/_/    _/_/_/       
   _/--------------_/----------------------_/-----------------     
+ _/          _/_/                        _/                      +
"""
