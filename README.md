# artificial-intelligence

Phase 1 reference implementation of the `ai9414` educational AI platform, now with three concrete search demos:

- weighted geometric graph search
- labyrinth DFS search
- spatial graph DFS search

## What is included

- shared `ai9414` namespace package
- common FastAPI launcher and route contract
- common JSON schema models
- precomputed trace replay for a weighted geometric graph search demo
- precomputed trace replay for a generated spatial graph DFS demo
- static solution replay export with no backend dependency
- deterministic labyrinth presets plus seeded graph generation
- automated tests and developer documentation

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
python examples/search_demo.py
```

To start the labyrinth example instead:

```bash
python examples/labyrinth_demo.py
```

To start the spatial graph DFS example instead:

```bash
python examples/graph_dfs_demo.py
```

The same install is enough for the labyrinth live-Python stub as well. The
student download now uses the built-in `ai9414.search.run_labyrinth_solver(...)`
wrapper, so no separate Flask setup is required.

To export a backend-free replay bundle:

```bash
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from ai9414.search import SearchDemo

app = SearchDemo()
output_dir = app.export_solution_bundle(Path("build/search-solution"))
print(output_dir)
PY
```

## Student-facing example

```python
from ai9414.search import SearchDemo

app = SearchDemo(node_count=16, seed=7)
app.load_example("default_sparse_graph")
app.set_options(playback_speed=1.0)
app.show()
```

Labyrinth example:

```python
from ai9414.labyrinth import LabyrinthDemo

app = LabyrinthDemo()
app.load_example("small")
app.show()
```

Spatial graph DFS example:

```python
from ai9414.graph_dfs import GraphDfsDemo

app = GraphDfsDemo()
app.load_example("small")
app.show()
```

Live labyrinth solver wrapper:

```python
from typing import Any
from ai9414.search import run_labyrinth_solver


def solve_dfs(labyrinth: dict[str, Any]) -> dict[str, Any]:
    ...


if __name__ == "__main__":
    run_labyrinth_solver(solve_dfs)
```

Live graph solver wrapper:

```python
from typing import Any
from ai9414.search import run_graph_solver


def solve_dfs(graph: dict[str, Any]) -> dict[str, Any]:
    ...


if __name__ == "__main__":
    run_graph_solver(solve_dfs)
```

## Repository structure

```text
src/ai9414/
  core/
  demo/
  labyrinth/
  search/
  frontend/
examples/
tests/
docs/
```
