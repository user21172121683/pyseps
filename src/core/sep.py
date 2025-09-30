from dataclasses import is_dataclass, fields
from typing import Optional
from PIL import Image
import yaml

from core.specs import Spec, PreSpec, SplitSpec, HalftoneSpec, DotSpec
from core.pre import Pre
from core.split import Split
from core.halftone import Halftone
from core.dot import Dot
from constants import TEMPLATES_DIR, DEFAULT_TEMPLATE


class Sep:
    def __init__(
        self,
        image: Image.Image | None = None,
        folder: str = "",
        pre: Pre | None = None,
        pre_spec: PreSpec | None = None,
        split: Split | None = None,
        split_spec: SplitSpec | None = None,
        halftone: Halftone | None = None,
        halftone_spec: HalftoneSpec | HalftoneSpec = None,
        dot: Dot | None = None,
        dot_spec: DotSpec | None = None,
    ):
        self._pre: Pre | None = pre
        self._pre_spec: PreSpec | None = pre_spec
        self._split: Split | None = split
        self._split_spec: SplitSpec | None = split_spec
        self._halftone: Halftone | None = halftone
        self._halftone_spec: HalftoneSpec | None = halftone_spec
        self._dot: Dot | None = dot
        self._dot_spec: DotSpec | None = dot_spec

        self.image: Image.Image | None = image
        self.folder: str = folder
        self.separations: dict[str, tuple[Image.Image, Image.Image]] = {}

        # Set change listeners on specs if available
        if self._pre_spec:
            self._pre_spec.set_on_change(self._refresh)
        if self._split_spec:
            self._split_spec.set_on_change(self._refresh)
        if self._halftone_spec:
            self._halftone_spec.set_on_change(self._refresh)
        if self._dot_spec:
            self._dot_spec.set_on_change(self._refresh)

        if self._split and self._halftone and self._dot:
            self._refresh()

        # Try importing the default template
        try:
            self.import_template(DEFAULT_TEMPLATE)
        except FileNotFoundError:
            print(
                f"Default template not found in folder '{self.folder}', skipping import."
            )

    def __repr__(self):
        return (
            f"<Sep("
            f"split={self.split if self.split else None}, "
            f"halftone={self.halftone if self.halftone else None}, "
            f"dot={self.dot if self.dot else None}, "
            f"image={self.image if self.image else None}, "
            f"separations={len(self.separations)}, "
            f"folder='{self.folder}'"
            f")>"
        )

    # PROPERTY SETTERS WITH REFRESH #

    @property
    def pre_spec(self) -> Optional[PreSpec]:
        return self._pre_spec

    @pre_spec.setter
    def pre_spec(self, value: PreSpec):
        self._pre_spec = value
        self._pre_spec.set_on_change(self._refresh)
        self._refresh()

    @property
    def pre(self) -> Optional[Pre]:
        return self._pre

    @pre.setter
    def pre(self, value: Pre):
        self._pre = value
        self._refresh()

    @property
    def split_spec(self) -> Optional[SplitSpec]:
        return self._split_spec

    @split_spec.setter
    def split_spec(self, value: SplitSpec):
        self._split_spec = value
        self._split_spec.set_on_change(self._refresh)
        self._refresh()

    @property
    def halftone_spec(self) -> Optional[HalftoneSpec]:
        return self._halftone_spec

    @halftone_spec.setter
    def halftone_spec(self, value: HalftoneSpec):
        self._halftone_spec = value
        self._halftone_spec.set_on_change(self._refresh)
        self._refresh()

    @property
    def dot_spec(self) -> Optional[DotSpec]:
        return self._dot_spec

    @dot_spec.setter
    def dot_spec(self, value: DotSpec):
        self._dot_spec = value
        self._dot_spec.set_on_change(self._refresh)
        self._refresh()

    @property
    def split(self) -> Optional[Split]:
        return self._split

    @split.setter
    def split(self, value: Split):
        self._split = value
        self._refresh()

    @property
    def halftone(self) -> Optional[Halftone]:
        return self._halftone

    @halftone.setter
    def halftone(self, value: Halftone):
        self._halftone = value
        self._refresh()

    @property
    def dot(self) -> Optional[Dot]:
        return self._dot

    @dot.setter
    def dot(self, value: Dot):
        self._dot = value
        self._refresh()

    # INTERNAL METHODS #

    def _refresh(self):
        if not all(
            [
                self._pre,
                self._pre_spec,
                self._split,
                self._split_spec,
                self._halftone,
                self._halftone_spec,
                self._dot,
                self._dot_spec,
                self.image,
            ]
        ):
            print(">>> REFRESH SKIPPED (Incomplete configuration) <<<")
            return

        print(">>> REFRESHED SEP <<<")
        self._generate()

    def _generate(self):
        self.separations = {}

        # Apply preprocessing step
        preprocessed_image = self._pre.process(self.image)

        angles = self._split_spec.angles
        for i, (name, positive) in enumerate(
            self._split.split(preprocessed_image).items()
        ):
            angle = angles[i % len(angles)]
            halftoned = self._halftone.generate(positive, self._dot, angle)
            self.separations[name] = (positive, halftoned)

    def _class_from_name(self, class_name: str):
        def all_subclasses(cls):
            """Recursively find all subclasses of a given class."""
            return set(cls.__subclasses__()).union(
                [s for c in cls.__subclasses__() for s in all_subclasses(c)]
            )

        # List of known root base classes for functional components and specs
        base_classes = [Dot, Halftone, Split, Pre, Spec]

        # Search all subclasses across all base classes
        for base in base_classes:
            for subclass in all_subclasses(base).union({base}):
                if subclass.__name__ == class_name:
                    return subclass

        raise ValueError(f"Unknown class name: {class_name}")

    def _asdict_excluding_inherited(self, instance):
        cls = instance.__class__
        base_fields = set()
        for base in cls.__bases__:
            if is_dataclass(base):
                base_fields.update(f.name for f in fields(base))
        return {
            f.name: getattr(instance, f.name)
            for f in fields(cls)
            if f.name not in base_fields
        }

    def _convert_tuples_to_lists(self, obj):
        if isinstance(obj, tuple):
            return list(obj)
        elif isinstance(obj, list):
            return [self._convert_tuples_to_lists(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: self._convert_tuples_to_lists(v) for k, v in obj.items()}
        else:
            return obj

    def _convert_lists_to_tuples(self, obj):
        if isinstance(obj, list):
            return tuple(self._convert_lists_to_tuples(i) for i in obj)
        elif isinstance(obj, dict):
            return {k: self._convert_lists_to_tuples(v) for k, v in obj.items()}
        else:
            return obj

    # PUBLIC METHODS #

    def save(self):
        for name, (_, halftone) in self.separations.items():
            halftone.save(
                self.folder + name + ".tiff",
                compression="group4",
                dpi=(self.halftone_spec.dpi, self.halftone_spec.dpi),
            )

    def export_template(self, filename="template.yaml"):
        def block(component, spec):
            if not (component and spec):
                return None
            data = self._asdict_excluding_inherited(spec)
            data["type"] = component.__class__.__name__
            return self._convert_tuples_to_lists(data)

        template = {
            "pre": block(self._pre, self._pre_spec),
            "split": block(self._split, self._split_spec),
            "halftone": block(self._halftone, self._halftone_spec),
            "dot": block(self._dot, self._dot_spec),
        }

        # Remove None entries
        template = {k: v for k, v in template.items() if v is not None}

        path = TEMPLATES_DIR / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(template, f, sort_keys=False, indent=4)

    def import_template(self, filename=DEFAULT_TEMPLATE):
        path = TEMPLATES_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            template = yaml.safe_load(f)

        def apply_component(
            key, spec_cls, current_spec, current_func, default_func_cls
        ):
            block = template.get(key)
            if not block:
                return current_spec, current_func  # Nothing to update

            block = self._convert_lists_to_tuples(block)

            # Get class from 'type' field if present
            cls_name = block.pop("type", None)
            func_cls = self._class_from_name(cls_name) if cls_name else default_func_cls

            # Build updated spec (merge if already exists)
            if current_spec:
                # Update existing spec in-place
                for k, v in block.items():
                    setattr(current_spec, k, v)
                spec = current_spec
            else:
                spec = spec_cls(**block)

            spec.set_on_change(self._refresh)
            func = func_cls(spec)

            return spec, func

        # Pre
        self._pre_spec, self._pre = apply_component(
            "pre",
            PreSpec,
            self._pre_spec,
            self._pre,
            type(self._pre) if self._pre else Pre,
        )
        # Split
        self._split_spec, self._split = apply_component(
            "split",
            SplitSpec,
            self._split_spec,
            self._split,
            type(self._split) if self._split else Split,
        )
        # Halftone
        self._halftone_spec, self._halftone = apply_component(
            "halftone",
            HalftoneSpec,
            self._halftone_spec,
            self._halftone,
            type(self._halftone) if self._halftone else Halftone,
        )
        # Dot
        self._dot_spec, self._dot = apply_component(
            "dot",
            DotSpec,
            self._dot_spec,
            self._dot,
            type(self._dot) if self._dot else Dot,
        )

        self._refresh()
