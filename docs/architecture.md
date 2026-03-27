# ai9414 Architecture Overview

This repository contains the Phase 1 reference infrastructure for the `ai9414` platform.

## Included in Phase 1

- Shared `ai9414` Python namespace
- Common Pydantic schemas for manifest, state, trace, action, and error payloads
- `BaseEducationalApp` for consistent topic-app behaviour
- FastAPI app factory and launcher utilities
- Bundled student frontend shell assets
- Static solution replay export with no backend dependency
- Minimal placeholder app proving precomputed and incremental execution modes

## Execution Modes

- `precomputed`: Python builds the full trace before frontend replay.
- `incremental`: Python computes one step per `next_step` action and can later export a complete trace for solution replay.

## Frontend Contract

The student shell uses the standard routes:

- `GET /`
- `GET /api/health`
- `GET /api/manifest`
- `GET /api/state`
- `GET /api/trace`
- `POST /api/action`
- `GET /api/examples`
- `GET /api/errors`

The solution bundle uses static `index.html` plus `trace.json` and performs no backend calls.

## Packaging Notes

- Frontend assets are shipped inside the Python package.
- File access uses package-relative paths that work in installed environments.
- Students need Python only; Node.js is not required at runtime.

