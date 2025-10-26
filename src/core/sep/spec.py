from dataclasses import dataclass, field
from typing import Type
from modules.pre import PreSpec, Pre
from modules.split import SplitSpec, Split
from modules.halftone import HalftoneSpec, Halftone
from modules.dot import DotSpec, Dot


@dataclass
class SepSpec:
    pre_spec: PreSpec = field(default_factory=PreSpec)
    pre_type: Type[Pre] | None = None

    split_spec: SplitSpec = field(default_factory=SplitSpec)
    split_type: Type[Split] | None = None

    halftone_spec: HalftoneSpec = field(default_factory=HalftoneSpec)
    halftone_type: Type[Halftone] | None = None

    dot_spec: DotSpec = field(default_factory=DotSpec)
    dot_type: Type[Dot] | None = None
