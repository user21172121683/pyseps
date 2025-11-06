# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from constants import Globals, Defaults


@dataclass
class ImageManager:
    image: Image.Image | None = None
    separations: dict[str, tuple[Image.Image, Image.Image]] | None = None
    preview: Image.Image | None = None
    folder: Path | None = None

    def load(self, path: Path) -> None:
        """Load an image and store its folder."""

        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        with Image.open(str(path)) as img:
            self.image = img.copy()

        self.folder = path.parent.resolve()
        print(f"Loaded image at {path}")

    def save(
        self,
        *,
        splits: bool = Defaults.SAVE_SPLITS,
        halftones: bool = Defaults.SAVE_HALFTONES,
        preview: bool = Defaults.SAVE_PREVIEW,
        fmt: str = Defaults.FORMAT,
        dpi: int = 300,
        output_folder: str = Defaults.OUTPUT,
    ) -> None:
        """Save separations to disk."""

        if not self.separations:
            raise RuntimeError("No separations to save.")

        if fmt not in Globals.IMAGE_FORMATS:
            raise ValueError(f"Unsupported format: {fmt}")

        options = Globals.IMAGE_FORMATS[fmt]

        output_dir = self.folder / output_folder
        output_dir.mkdir(parents=True, exist_ok=True)

        for name, (split, halftone) in self.separations.items():
            if splits:
                split.save(
                    output_dir / f"{name}.{fmt}",
                    dpi=(dpi, dpi),
                    **dict(options["L"].items()),
                )
            if halftones:
                halftone.save(
                    output_dir / f"{name}.{fmt}",
                    dpi=(dpi, dpi),
                    **dict(options["1"].items()),
                )
        if preview:
            preview.save(
                output_dir / f"preview.{fmt}",
                dpi=(dpi, dpi),
                **dict(options["L"].items()),
            )

        print(f"Saved separations to {output_dir}")
