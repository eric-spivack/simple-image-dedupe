# simple-image-dedupe

A web-based tool for finding and removing duplicate images. Scan a directory, review duplicate groups side-by-side, choose which files to keep, and safely trash the rest — with undo support.

## Features

- **Exact matching** — SHA-256 hash to find byte-identical duplicates
- **Perceptual matching** — pHash/dHash to find visually similar images
- **Smart suggestions** — auto-selects the best file to keep (highest resolution, largest size, oldest)
- **Safe deletion** — files are moved to `.dedupe_trash/` inside the scanned directory, not permanently deleted
- **Undo** — restore trashed files with one click
- **No JavaScript framework** — lightweight HTMX-powered UI with server-rendered HTML

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

## Getting Started

```bash
# Install dependencies
uv sync

# Start the server
uv run main.py
```

Open http://127.0.0.1:8000 in your browser.

## Usage

1. Enter the path to a directory containing images
2. Choose a matching method (exact, pHash, or dHash) and threshold
3. Click **Scan** to find duplicates
4. Review each group — the suggested keep is highlighted in green
5. Select which file to keep and click **Keep Selected, Trash Others**
6. Use **Undo** to restore files if needed

## Supported Formats

`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`

## Development

```bash
uv run ruff check .    # lint
uv run ruff format .   # format
```
