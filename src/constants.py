from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "templates"
DEFAULT_TEMPLATE = TEMPLATES_DIR / "default.yaml"
APP_NAME = "pyseps"
BANNER = """
+      _/_/_/    _/    _/    _/_/_/    _/_/    _/_/_/      _/_/_/ +
      _/    _/  _/    _/  _/_/      _/_/_/_/  _/    _/  _/_/       
     _/    _/  _/    _/      _/_/  _/        _/    _/      _/_/    
    _/_/_/      _/_/_/  _/_/_/      _/_/_/  _/_/_/    _/_/_/       
   _/--------------_/----------------------_/-----------------     
+ _/          _/_/                        _/                      +
"""
