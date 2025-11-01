# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import Path
import yaml

from modules.pre import PreSpec
from modules.split import SplitSpec
from modules.halftone import HalftoneSpec
from modules.dot import DotSpec
from core.registry import MODULE_REGISTRY
from utils.helpers import convert_lists_to_tuples, convert_tuples_to_lists


def import_template(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    pre_spec, pre_type = _parse_section(data.get("pre"), PreSpec)
    split_spec, split_type = _parse_section(data.get("split"), SplitSpec)
    halftone_spec, halftone_type = _parse_section(data.get("halftone"), HalftoneSpec)
    dot_spec, dot_type = _parse_section(data.get("dot"), DotSpec)

    print(f"Loaded template at {path}!")

    return {
        "pre_spec": pre_spec,
        "pre_type": pre_type,
        "split_spec": split_spec,
        "split_type": split_type,
        "halftone_spec": halftone_spec,
        "halftone_type": halftone_type,
        "dot_spec": dot_spec,
        "dot_type": dot_type,
    }


def _parse_section(section_data, spec_cls):
    if not section_data:
        return None, None

    section_data = convert_lists_to_tuples(section_data)
    type_alias = section_data.pop("type", None)

    type_cls = MODULE_REGISTRY.get(type_alias) if type_alias else None
    spec = spec_cls(**section_data)

    return spec, type_cls


def export_template(filename: str = "template.yaml", folder: Path = Path("."), **spec):
    def serialize(spec_obj, type_cls):
        if not spec_obj or not type_cls:
            return None
        data = spec_obj.__dict__.copy()
        data["type"] = type_cls.__name__
        return convert_tuples_to_lists(data)

    template_dict = {
        "pre": serialize(spec.get("pre_spec"), spec.get("pre_type")),
        "split": serialize(spec.get("split_spec"), spec.get("split_type")),
        "halftone": serialize(spec.get("halftone_spec"), spec.get("halftone_type")),
        "dot": serialize(spec.get("dot_spec"), spec.get("dot_type")),
    }

    template_dict = {k: v for k, v in template_dict.items() if v is not None}

    path = folder / filename
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        yaml.dump(template_dict, f, sort_keys=False, indent=4)

    print(f"Saved template to {path}!")
