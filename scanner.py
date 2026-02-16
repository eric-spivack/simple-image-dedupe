from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def scan_directory(path: str | Path) -> list[Path]:
    """Recursively find image files in the given directory."""
    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError(f"Not a valid directory: {root}")

    images = [
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(images)
