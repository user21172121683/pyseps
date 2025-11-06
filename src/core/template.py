# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass, field, asdict
from pathlib import Path
import yaml

from modules import SplitSpec, SplitBase, HalftoneSpec, HalftoneBase, DotSpec, DotBase


from .registry import MODULE_REGISTRY


@dataclass
class TemplateManager:
    """Manages split, halftone, and dot template specifications."""

    split_spec: SplitSpec = field(default_factory=SplitSpec)
    halftone_spec: HalftoneSpec = field(default_factory=HalftoneSpec)
    dot_spec: DotSpec = field(default_factory=DotSpec)

    split_type: SplitBase | None = None
    halftone_type: HalftoneBase | None = None
    dot_type: DotBase | None = None

    def load_yaml(self, path: Path):
        """Load spec data from a YAML file and modify instance."""

        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self._from_dict(data)
        print(f"Loaded template from {path}")

    def save_yaml(self, path: Path):
        """Export spec to a YAML file."""

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(
                {k: v for k, v in self._to_dict().items() if v is not None},
                f,
                sort_keys=False,
                indent=4,
            )
        print(f"Saved template to {path}")

    def _to_dict(self) -> dict:
        """Serialize spec to dictionary for YAML export."""

        def serialize(spec_obj, type_cls):
            if spec_obj is None or type_cls is None:
                return None
            data = asdict(spec_obj)
            data["type"] = type_cls.__name__
            return data

        return {
            "split": serialize(self.split_spec, self.split_type),
            "halftone": serialize(self.halftone_spec, self.halftone_type),
            "dot": serialize(self.dot_spec, self.dot_type),
        }

    def _from_dict(self, data: dict):
        """Load spec data from a dictionary and modify instance."""

        def parse_section(section_data, spec_cls):
            if not section_data:
                return spec_cls(), None
            type_name = section_data.pop("type", None)
            type_cls = MODULE_REGISTRY.get(type_name) if type_name else None
            spec = spec_cls(**section_data)
            return spec, type_cls

        self.split_spec, self.split_type = parse_section(data.get("split"), SplitSpec)
        self.halftone_spec, self.halftone_type = parse_section(
            data.get("halftone"), HalftoneSpec
        )
        self.dot_spec, self.dot_type = parse_section(data.get("dot"), DotSpec)
