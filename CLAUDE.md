# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

simple-image-dedupe is an early-stage Python image deduplication utility. Currently a skeleton project with a placeholder `main.py` entry point.

## Development Setup

- **Python 3.11+** required (pinned in `.python-version`)
- **uv** is the package manager (not pip). Use `uv` for all dependency and environment operations.
- **direnv** manages the virtualenv path via `.envrc` — the venv lives at `~/.virtualenvs/simple-image-dedupe/`, not the default `.venv/`

## Commands

- `uv run main.py` — run the application
- `uv run ruff check .` — lint
- `uv run ruff format .` — format code
- `uv add <package>` — add a dependency
- `uv sync` — install/sync dependencies from lockfile

## Commit Convention

Format: `{emoji} {type}: {message}`

Examples: `🐛 fix: resolve off-by-one error`, `✨ feat: add perceptual hashing`, `🧹 chore: update gitignore`

## Project Structure

Single-file project: `main.py` is the entry point. No tests or module structure yet. Only runtime dependency is ruff (linter/formatter).
