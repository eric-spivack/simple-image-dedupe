# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

simple-image-dedupe is a web-based image deduplication tool. Users scan a directory, review duplicate groups (exact or perceptual matches), choose which files to keep, and deleted files are safely moved to a `.dedupe_trash/` folder with undo support.

## Development Setup

- **Python 3.11+** required (pinned in `.python-version`)
- **uv** is the package manager (not pip). Use `uv` for all dependency and environment operations.
- **direnv** manages the virtualenv path via `.envrc` — the venv lives at `~/.virtualenvs/simple-image-dedupe/`, not the default `.venv/`

## Commands

- `uv run main.py` — start the FastAPI server at http://127.0.0.1:8000
- `uv run ruff check .` — lint
- `uv run ruff format .` — format code
- `uv add <package>` — add a dependency
- `uv sync` — install/sync dependencies from lockfile

## Commit Convention

Format: `{emoji} {type}: {message}`

Examples: `🐛 fix: resolve off-by-one error`, `✨ feat: add perceptual hashing`, `🧹 chore: update gitignore`

## Project Structure

```
main.py              # FastAPI app, all endpoints, uvicorn entry point
scanner.py           # Directory scanning, image file discovery
hasher.py            # SHA-256 exact + perceptual hashing, duplicate grouping
templates/
  index.html         # Main page with scan form (HTMX for interactivity)
  partials/
    groups.html      # Duplicate groups container (returned by POST /api/scan)
    group_card.html  # Single group card with thumbnails and keep selection
    group_resolved.html  # Resolved card shown after action
static/
  style.css          # Minimal CSS
```

## Key Dependencies

- **fastapi** + **uvicorn** — web framework and server
- **jinja2** — server-side templates
- **pillow** — image loading and thumbnails
- **imagehash** — perceptual hashing (phash, dhash)
- **ruff** — linter/formatter (dev only)

## Architecture Notes

- No database — all state is in-memory (scan-review-act workflow)
- HTMX handles all interactivity — server returns HTML fragments
- Trash uses `.dedupe_trash/` inside the scanned directory
- Image IDs are base64-encoded file paths
