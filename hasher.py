import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import imagehash
from PIL import Image


@dataclass
class ImageInfo:
    path: Path
    file_size: int
    width: int
    height: int
    mtime: float
    exact_hash: str = ""
    perceptual_hash: imagehash.ImageHash | None = None


@dataclass
class DuplicateGroup:
    id: str
    method: str
    images: list[ImageInfo] = field(default_factory=list)
    suggested_keep: int = 0  # index into images


def get_image_info(path: Path) -> ImageInfo:
    """Collect metadata for a single image file."""
    stat = path.stat()
    with Image.open(path) as img:
        width, height = img.size
    return ImageInfo(
        path=path,
        file_size=stat.st_size,
        width=width,
        height=height,
        mtime=stat.st_mtime,
    )


def hash_exact(path: Path) -> str:
    """Compute SHA-256 hash of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_perceptual(path: Path, method: str = "phash") -> imagehash.ImageHash:
    """Compute perceptual hash using the specified method."""
    with Image.open(path) as img:
        if method == "dhash":
            return imagehash.dhash(img)
        return imagehash.phash(img)


def _suggest_keep(images: list[ImageInfo]) -> int:
    """Pick the best image to keep: highest resolution > largest file > oldest."""

    def sort_key(info: ImageInfo) -> tuple:
        return (info.width * info.height, info.file_size, -info.mtime)

    return max(range(len(images)), key=lambda i: sort_key(images[i]))


def group_duplicates(
    paths: list[Path],
    method: str = "exact",
    threshold: int = 5,
) -> list[DuplicateGroup]:
    """Find duplicate groups among the given image paths.

    method: "exact" for SHA-256, "phash" or "dhash" for perceptual hashing.
    threshold: max hamming distance for perceptual matches (ignored for exact).
    """
    infos: list[ImageInfo] = []
    for p in paths:
        try:
            infos.append(get_image_info(p))
        except Exception:
            continue

    if method == "exact":
        return _group_exact(infos)
    return _group_perceptual(infos, method, threshold)


def _group_exact(infos: list[ImageInfo]) -> list[DuplicateGroup]:
    for info in infos:
        info.exact_hash = hash_exact(info.path)

    buckets: dict[str, list[ImageInfo]] = {}
    for info in infos:
        buckets.setdefault(info.exact_hash, []).append(info)

    groups = []
    for hash_val, images in buckets.items():
        if len(images) < 2:
            continue
        group = DuplicateGroup(
            id=hash_val[:12],
            method="exact",
            images=images,
            suggested_keep=_suggest_keep(images),
        )
        groups.append(group)
    return groups


def _group_perceptual(
    infos: list[ImageInfo], method: str, threshold: int
) -> list[DuplicateGroup]:
    for info in infos:
        info.perceptual_hash = hash_perceptual(info.path, method)

    # Union-find for grouping
    parent = list(range(len(infos)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        pa, pb = find(a), find(b)
        if pa != pb:
            parent[pa] = pb

    # O(n^2) pairwise comparison
    for i in range(len(infos)):
        for j in range(i + 1, len(infos)):
            h1 = infos[i].perceptual_hash
            h2 = infos[j].perceptual_hash
            if h1 is not None and h2 is not None and (h1 - h2) <= threshold:
                union(i, j)

    # Collect groups
    clusters: dict[int, list[ImageInfo]] = {}
    for i, info in enumerate(infos):
        root = find(i)
        clusters.setdefault(root, []).append(info)

    groups = []
    group_counter = 0
    for images in clusters.values():
        if len(images) < 2:
            continue
        group_counter += 1
        group = DuplicateGroup(
            id=f"{method}_{group_counter}",
            method=method,
            images=images,
            suggested_keep=_suggest_keep(images),
        )
        groups.append(group)
    return groups
