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
                self._pre,  # NEW
                self._pre_spec,  # NEW
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
        if not all(
            [self._pre_spec, self._split_spec, self._halftone_spec, self._dot_spec]
        ):
            raise ValueError("Cannot export template — specs are incomplete.")

        template = {
            "Pre": self._pre.__class__.__name__,
            "PreSpec": self._asdict_excluding_inherited(self._pre_spec),
            "Split": self._split.__class__.__name__,
            "SplitSpec": self._asdict_excluding_inherited(self._split_spec),
            "Halftone": self._halftone.__class__.__name__,
            "HalftoneSpec": self._asdict_excluding_inherited(self._halftone_spec),
            "Dot": self._dot.__class__.__name__,
            "DotSpec": self._asdict_excluding_inherited(self._dot_spec),
        }

        clean_template = self._convert_tuples_to_lists(template)
        path = TEMPLATES_DIR / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            yaml.dump(clean_template, f, sort_keys=False, indent=4)

    def import_template(self, filename=DEFAULT_TEMPLATE):
        path = TEMPLATES_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            template = yaml.safe_load(f)

        # Convert all list values in specs back to tuples
        template = self._convert_lists_to_tuples(template)

        # Instantiate Spec objects from saved config
        self._pre_spec = PreSpec(**template["PreSpec"])
        self._split_spec = SplitSpec(**template["SplitSpec"])
        self._halftone_spec = HalftoneSpec(**template["HalftoneSpec"])
        self._dot_spec = DotSpec(**template["DotSpec"])

        # Set up on_change listeners
        self._pre_spec.set_on_change(self._refresh)
        self._split_spec.set_on_change(self._refresh)
        self._halftone_spec.set_on_change(self._refresh)
        self._dot_spec.set_on_change(self._refresh)

        # Load functional component classes from names
        pre_cls = self._class_from_name(template["Pre"])
        split_cls = self._class_from_name(template["Split"])
        halftone_cls = self._class_from_name(template["Halftone"])
        dot_cls = self._class_from_name(template["Dot"])

        # Instantiate functional components using the specs
        self._pre = pre_cls(self._pre_spec)
        self._split = split_cls(self._split_spec)
        self._halftone = halftone_cls(self._halftone_spec)
        self._dot = dot_cls(self._dot_spec)

        # Trigger regeneration
        self._refresh()
