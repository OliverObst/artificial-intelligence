# ai9414 Architecture Overview

This repository contains the Phase 1 reference infrastructure for the `ai9414` platform together with concrete search, CSP, logic, and planning demo modules.

## Included in Phase 1

- Shared `ai9414` Python namespace
- Common Pydantic schemas for manifest, state, trace, action, and error payloads
- `BaseEducationalApp` for consistent topic-app behaviour
- FastAPI app factory and launcher utilities
- Bundled student and solution replay frontend assets
- Static solution replay export with no backend dependency
- `ai9414.search.SearchDemo` with deterministic weighted geometric graph examples
- `ai9414.labyrinth.LabyrinthDemo` with built-in labyrinth playback examples and live-Python handoff
- `ai9414.logic.DpllDemo` with built-in SAT and entailment playback examples plus live-Python DPLL handoff
- Depth-first branch-and-bound trace generation in Python
- Synchronised two-panel replay UI for the search tree and geometric graph

## Execution Modes

- `precomputed`: Python builds the full trace before frontend replay.
- `incremental`: Python computes one step per `next_step` action and can later export a complete trace for solution replay.

The search demo currently uses `precomputed` mode only, because Phase 1 is validating the replay model rather than incremental execution.

The labyrinth demo also uses `precomputed` mode for built-in examples, then hands off generated mazes to a separate student Python stub in live mode.

The DPLL demo uses the same trace-first precomputed model, but swaps the right-hand geometric view for a clause-state panel and supports both SAT and entailment within the same replay shell.

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

The solution bundle uses static `index.html` plus `trace.json` and performs no backend calls. To support this, the shared `TraceBundle` now carries an `initial_state` snapshot alongside the step patches.

## Packaging Notes

- Frontend assets are shipped inside the Python package.
- File access uses package-relative paths that work in installed environments.
- Students need Python only; Node.js is not required at runtime.

## Search Demo Structure

```text
src/ai9414/search/
  __init__.py
  api.py
  configs.py
  examples.py
  generator.py
  models.py
  solver.py
  trace.py

src/ai9414/labyrinth/
  __init__.py
  api.py
  examples.py
  generator.py
  models.py
  solver.py
  trace.py

src/ai9414/logic/
  __init__.py
  api.py
  examples.py
  models.py
  parser.py
  solver.py
  student.py
  trace.py
```

- `api.py`: public `SearchDemo` entry point
- `examples.py`: deterministic curated examples
- `generator.py`: sparse geometric graph generation with a guaranteed backbone path
- `solver.py`: exhaustive DFS with branch-and-bound pruning
- `trace.py`: fixed tree layout plus trace-bundle construction
- `models.py` and `configs.py`: graph, tree, and configuration validation models

The labyrinth package follows the same shape, but swaps the weighted-graph world for a grid maze, plain DFS reachability, built-in playback examples, and a live-Python `/solve` workflow.

The logic package follows the same overall contract, but its right-hand panel renders CNF clauses and literal states while the left-hand tree shows DPLL partial assignments, forced literals, contradictions, and backtracking.
