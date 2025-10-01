from dataclasses import is_dataclass, fields
from pathlib import Path

from PIL import Image
import yaml

from modules.pre import Pre, PreSpec
from modules.split import Split, SplitSpec
from modules.halftone import Halftone, HalftoneSpec
from modules.dot import Dot, DotSpec
from constants import TEMPLATES_DIR, DEFAULT_TEMPLATE


class Sep:
    def __init__(
        self,
        image_path: str | None = None,
        folder: str = "",
        pre: Pre | None = None,
        pre_spec: PreSpec | None = None,
        split: Split | None = None,
        split_spec: SplitSpec | None = None,
        halftone: Halftone | None = None,
        halftone_spec: HalftoneSpec | None = None,
        dot: Dot | None = None,
        dot_spec: DotSpec | None = None,
    ):
        self.pre: Pre | None = pre
        self.pre_spec: PreSpec | None = pre_spec
        self.split: Split | None = split
        self.split_spec: SplitSpec | None = split_spec
        self.halftone: Halftone | None = halftone
        self.halftone_spec: HalftoneSpec | None = halftone_spec
        self.dot: Dot | None = dot
        self.dot_spec: DotSpec | None = dot_spec

        self.image: Image.Image | None = None
        self.folder: str = folder
        self.separations: dict[str, tuple[Image.Image, Image.Image]] = {}

        # Load default template
        try:
            self.import_template(DEFAULT_TEMPLATE)
        except FileNotFoundError:
            print("Default template not found, skipping import.")

        # If an image path is provided, load the image and look for a local template
        if image_path:
            self.load(image_path)

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

    # INTERNAL METHODS #

    def _class_from_name(self, class_name: str):
        def all_subclasses(cls):
            """Recursively find all subclasses of a given class."""
            return set(cls.__subclasses__()).union(
                [s for c in cls.__subclasses__() for s in all_subclasses(c)]
            )

        # List of known root base classes for functional components and specs
        base_classes = [Dot, Halftone, Split, Pre]

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

    def generate(self):
        self.separations = {}

        # Apply preprocessing step
        preprocessed_image = self.pre.process(self.image)

        angles = self.split_spec.angles
        for i, (name, positive) in enumerate(
            self.split.split(preprocessed_image).items()
        ):
            angle = angles[i % len(angles)]
            halftoned = self.halftone.generate(positive, self.dot, angle)
            self.separations[name] = (positive, halftoned)

    def load(self, image_path: str):
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        self.image = Image.open(path)
        self.folder = str(path.parent) + "/"

        # Look for a YAML template in the same folder
        for file in path.parent.glob("*.yaml"):
            try:
                self.import_template(file.name)
                print(f"Imported local template: {file.name}")
                break  # Only use the first matching template
            except Exception as e:
                print(f"Failed to import local template '{file.name}': {e}")

    def save(self):
        output_dir = Path(self.folder) / "seps"
        output_dir.mkdir(parents=True, exist_ok=True)

        for name, (_, halftone) in self.separations.items():
            halftone.save(
                output_dir / f"{name}.tiff",
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
            "pre": block(self.pre, self.pre_spec),
            "split": block(self.split, self.split_spec),
            "halftone": block(self.halftone, self.halftone_spec),
            "dot": block(self.dot, self.dot_spec),
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

            func = func_cls(spec)

            return spec, func

        # Pre
        self.pre_spec, self.pre = apply_component(
            "pre",
            PreSpec,
            self.pre_spec,
            self.pre,
            type(self.pre) if self.pre else Pre,
        )
        # Split
        self.split_spec, self.split = apply_component(
            "split",
            SplitSpec,
            self.split_spec,
            self.split,
            type(self.split) if self.split else Split,
        )
        # Halftone
        self.halftone_spec, self.halftone = apply_component(
            "halftone",
            HalftoneSpec,
            self.halftone_spec,
            self.halftone,
            type(self.halftone) if self.halftone else Halftone,
        )
        # Dot
        self.dot_spec, self.dot = apply_component(
            "dot",
            DotSpec,
            self.dot_spec,
            self.dot,
            type(self.dot) if self.dot else Dot,
        )
