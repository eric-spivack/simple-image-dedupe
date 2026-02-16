import base64
import shutil
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

from hasher import DuplicateGroup, group_duplicates
from scanner import scan_directory

app = FastAPI(title="simple-image-dedupe")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory state
scan_results: dict[str, DuplicateGroup] = {}  # group_id -> DuplicateGroup
trash_log: dict[str, list[dict]] = {}  # group_id -> [{src, dest}, ...]
scan_root: Path | None = None

TRASH_DIR_NAME = ".dedupe_trash"


def encode_image_id(path: Path) -> str:
    return base64.urlsafe_b64encode(str(path).encode()).decode()


def decode_image_id(image_id: str) -> Path:
    return Path(base64.urlsafe_b64decode(image_id.encode()).decode())


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/api/scan", response_class=HTMLResponse)
async def api_scan(
    request: Request,
    directory: str = Form(...),
    method: str = Form("exact"),
    threshold: int = Form(5),
):
    global scan_root
    scan_results.clear()
    trash_log.clear()

    try:
        paths = scan_directory(directory)
    except ValueError as e:
        return HTMLResponse(f'<div class="error">{e}</div>')

    if not paths:
        return HTMLResponse(
            '<div class="info">No images found in this directory.</div>'
        )

    scan_root = Path(directory).resolve()
    groups = group_duplicates(paths, method=method, threshold=threshold)

    if not groups:
        return HTMLResponse(
            f'<div class="info">Scanned {len(paths)} images — no duplicates found.</div>'
        )

    for group in groups:
        scan_results[group.id] = group

    return templates.TemplateResponse(
        request,
        "partials/groups.html",
        {"groups": groups, "encode_image_id": encode_image_id, "total": len(paths)},
    )


@app.get("/api/thumbnail/{image_id}")
async def api_thumbnail(image_id: str):
    path = decode_image_id(image_id)
    if not path.is_file():
        return Response(status_code=404)

    with Image.open(path) as img:
        img.thumbnail((256, 256))
        from io import BytesIO

        buf = BytesIO()
        fmt = "PNG" if img.mode == "RGBA" else "JPEG"
        img.save(buf, format=fmt)
        buf.seek(0)
        media_type = f"image/{'png' if fmt == 'PNG' else 'jpeg'}"
        return Response(content=buf.read(), media_type=media_type)


@app.post("/api/action", response_class=HTMLResponse)
async def api_action(
    request: Request,
    group_id: str = Form(...),
    keep: str = Form(...),
):
    group = scan_results.get(group_id)
    if not group:
        return HTMLResponse('<div class="error">Group not found.</div>')

    keep_path = decode_image_id(keep)

    # Determine trash directory (inside the scanned root)
    trash_dir = (scan_root or keep_path.parent) / TRASH_DIR_NAME
    trash_dir.mkdir(parents=True, exist_ok=True)

    moved = []
    for img in group.images:
        if img.path == keep_path:
            continue
        dest = trash_dir / img.path.name
        # Handle name collisions
        counter = 1
        while dest.exists():
            dest = trash_dir / f"{img.path.stem}_{counter}{img.path.suffix}"
            counter += 1
        shutil.move(str(img.path), str(dest))
        moved.append({"src": str(img.path), "dest": str(dest)})

    trash_log[group_id] = moved

    return templates.TemplateResponse(
        request,
        "partials/group_resolved.html",
        {"group_id": group_id, "kept": keep_path, "moved_count": len(moved)},
    )


@app.post("/api/undo/{group_id}", response_class=HTMLResponse)
async def api_undo(request: Request, group_id: str):
    moved = trash_log.pop(group_id, [])
    for entry in moved:
        src, dest = Path(entry["src"]), Path(entry["dest"])
        if dest.is_file():
            shutil.move(str(dest), str(src))

    group = scan_results.get(group_id)
    if not group:
        return HTMLResponse('<div class="error">Group not found.</div>')

    return templates.TemplateResponse(
        request,
        "partials/group_card.html",
        {"group": group, "encode_image_id": encode_image_id},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
