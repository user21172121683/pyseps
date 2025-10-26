from pathlib import Path
from PIL import Image
from constants import DEFAULT_OUTPUT_DIR
from utils.helpers import find_by_extension


def load_image_and_template(image_path: str | Path):
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        with Image.open(str(path)) as img:
            image = img.copy()
    except Exception as e:
        print(f"Error opening image file: {e}")
        raise

    folder = path.parent
    local_template = find_by_extension(folder, "yaml")

    print(f"Loaded image at {path}!")
    return image, folder, local_template


def save_separations(separations, folder: Path, dpi: int, output_folder: str = None):
    if not separations:
        raise RuntimeError("No separations to save.")

    if folder is None:
        raise RuntimeError("Image folder is unknown.")

    if output_folder is None:
        output_folder = DEFAULT_OUTPUT_DIR

    output_dir = folder / output_folder
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, (_, halftone) in separations.items():
        halftone.save(
            output_dir / f"{name}.tiff",
            compression="group4",
            dpi=(dpi, dpi),
        )

    print(f"Saved separations to {output_dir}!")
