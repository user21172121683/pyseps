# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass
from pathlib import Path

from PIL import Image
import numpy as np

from constants import Globals, Defaults


@dataclass
class Separation:
    name: str
    split: np.ndarray
    screen: np.ndarray
    halftone: np.ndarray
    angle: int
    tone: tuple[int, int, int]


@dataclass
class ImageManager:
    original: Image.Image | None = None
    separations: list[Separation] | None = None
    preview: Image.Image | None = None
    folder: Path | None = None

    def load(self, path: Path) -> None:
        """Load an image and store its folder."""

        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        with Image.open(str(path)) as img:
            self.original = img.copy()

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

        for separation in self.separations:
            use_subfolders = splits and halftones

            if splits:
                split_dir = output_dir / "splits" if use_subfolders else output_dir
                split_dir.mkdir(parents=True, exist_ok=True)
                Image.fromarray(separation.split).convert("L").save(
                    split_dir / f"{separation.name}.{fmt}",
                    dpi=(dpi, dpi),
                    **dict(options["L"].items()),
                )

            if halftones:
                halftone_dir = (
                    output_dir / "halftones" if use_subfolders else output_dir
                )
                halftone_dir.mkdir(parents=True, exist_ok=True)
                Image.fromarray(separation.halftone).convert("1").save(
                    halftone_dir / f"{separation.name}.{fmt}",
                    dpi=(dpi, dpi),
                    **dict(options["1"].items()),
                )
        if preview:
            self.preview.save(
                output_dir / f"preview.{fmt}",
                dpi=(dpi, dpi),
                **dict(options["L"].items()),
            )

        print(f"Saved separations to {output_dir}")
