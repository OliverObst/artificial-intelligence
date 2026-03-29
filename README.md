# artificial-intelligence

Phase 1 reference implementation of the `ai9414` educational AI platform, now with six concrete search demos:

- labyrinth DFS search
- spatial graph DFS search
- spatial graph BFS search
- spatial graph greedy best-first search
- spatial graph uniform-cost search
- spatial graph branch-and-bound search

## Available demos

- `labyrinth DFS search`
  Start with `python examples/labyrinth_demo.py`
- `spatial graph DFS search`
  Start with `python examples/graph_dfs_demo.py`
- `spatial graph BFS search`
  Start with `python examples/graph_bfs_demo.py`
- `spatial graph greedy best-first search`
  Start with `python examples/graph_gbfs_demo.py`
- `spatial graph uniform-cost search`
  Start with `python examples/graph_ucs_demo.py`
- `spatial graph branch-and-bound search`
  Start with `python examples/graph_branch_and_bound_demo.py`

## What is included

- shared `ai9414` namespace package
- common FastAPI launcher and route contract
- common JSON schema models
- precomputed trace replay for a generated spatial graph DFS demo
- precomputed trace replay for a generated spatial graph BFS demo
- precomputed trace replay for a generated spatial graph greedy best-first demo
- precomputed trace replay for a generated spatial graph uniform-cost demo
- precomputed trace replay for a generated spatial graph branch-and-bound demo
- static solution replay export with no backend dependency
- deterministic labyrinth presets plus seeded graph generation
- automated tests and developer documentation

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
python examples/graph_branch_and_bound_demo.py
```

To start the labyrinth example:

```bash
python examples/labyrinth_demo.py
```

To start the spatial graph DFS example:

```bash
python examples/graph_dfs_demo.py
```

To start the spatial graph BFS example:

```bash
python examples/graph_bfs_demo.py
```

To start the spatial graph greedy best-first example:

```bash
python examples/graph_gbfs_demo.py
```

To start the spatial graph uniform-cost example:

```bash
python examples/graph_ucs_demo.py
```

To start the spatial graph branch-and-bound example:

```bash
python examples/graph_branch_and_bound_demo.py
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

## Student-facing examples

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

Spatial graph BFS example:

```python
from ai9414.graph_bfs import GraphBfsDemo

app = GraphBfsDemo()
app.load_example("small")
app.show()
```

Spatial graph greedy best-first example:

```python
from ai9414.graph_gbfs import GraphGbfsDemo

app = GraphGbfsDemo()
app.load_example("small")
app.show()
```

Spatial graph branch-and-bound example:

```python
from ai9414.search import SearchDemo

app = SearchDemo()
app.load_example("small")
app.set_options(playback_speed=1.0)
app.show()
```

Spatial graph uniform-cost example:

```python
from ai9414.graph_ucs import GraphUcsDemo

app = GraphUcsDemo()
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

Live graph BFS solver wrapper:

```python
from typing import Any
from ai9414.search import run_graph_bfs_solver


def solve_bfs(graph: dict[str, Any]) -> dict[str, Any]:
    ...


if __name__ == "__main__":
    run_graph_bfs_solver(solve_bfs)
```

Live graph UCS solver wrapper:

```python
from typing import Any
from ai9414.search import run_graph_ucs_solver


def solve_ucs(graph: dict[str, Any]) -> dict[str, Any]:
    ...


if __name__ == "__main__":
    run_graph_ucs_solver(solve_ucs)
```

Live graph greedy best-first solver wrapper:

```python
from typing import Any
from ai9414.search import run_graph_gbfs_solver


def solve_gbfs(graph: dict[str, Any]) -> dict[str, Any]:
    ...


if __name__ == "__main__":
    run_graph_gbfs_solver(solve_gbfs)
```

Live spatial graph branch-and-bound solver wrapper:

```python
from typing import Any
from ai9414.search import run_weighted_graph_solver


def solve_dfbb(graph: dict[str, Any]) -> dict[str, Any]:
    ...


if __name__ == "__main__":
    run_weighted_graph_solver(solve_dfbb)
```

## Repository structure

```text
src/ai9414/
  core/
  demo/
  graph_bfs/
  graph_dfs/
  graph_gbfs/
  graph_ucs/
  labyrinth/
  search/
  frontend/
examples/
tests/
docs/
```
