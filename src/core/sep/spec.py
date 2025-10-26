from dataclasses import dataclass, field
from typing import Type
from modules.pre import PreSpec, Pre
from modules.split import SplitSpec, SplitBase
from modules.halftone import HalftoneSpec, HalftoneBase
from modules.dot import DotSpec, DotBase


@dataclass
class SepSpec:
    pre_spec: PreSpec = field(default_factory=PreSpec)
    pre_type: Type[Pre] | None = None

    split_spec: SplitSpec = field(default_factory=SplitSpec)
    split_type: Type[SplitBase] | None = None

    halftone_spec: HalftoneSpec = field(default_factory=HalftoneSpec)
    halftone_type: Type[HalftoneBase] | None = None

    dot_spec: DotSpec = field(default_factory=DotSpec)
    dot_type: Type[DotBase] | None = None
