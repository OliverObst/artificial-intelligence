# artificial-intelligence

Phase 1 reference implementation of the `ai9414` educational AI platform, now with thirteen concrete demos:

- labyrinth DFS search
- spatial graph DFS search
- spatial graph BFS search
- spatial graph greedy best-first search
- spatial graph A* search
- spatial graph uniform-cost search
- spatial graph branch-and-bound search
- propositional logic DPLL
- reasoning with uncertainty belief-state explorer
- foundation models tokenisation explorer
- CSP map colouring
- CSP delivery time-slot assignment
- STRIPS planning

## Available demos

- `labyrinth DFS search`
  Start with `ai9414 demo labyrinth`
- `spatial graph DFS search`
  Start with `ai9414 demo graph-dfs`
- `spatial graph BFS search`
  Start with `ai9414 demo graph-bfs`
- `spatial graph greedy best-first search`
  Start with `ai9414 demo graph-gbfs`
- `spatial graph A* search`
  Start with `ai9414 demo graph-astar`
- `spatial graph uniform-cost search`
  Start with `ai9414 demo graph-ucs`
- `spatial graph branch-and-bound search`
  Start with `ai9414 demo graph-bnb`
- `propositional logic DPLL`
  Start with `ai9414 demo logic-dpll`
- `reasoning with uncertainty belief-state explorer`
  Start with `ai9414 demo uncertainty`
- `foundation models tokenisation explorer`
  Start with `ai9414 demo foundation-models`
- `CSP map colouring`
  Start with `ai9414 demo csp-map`
- `CSP delivery time-slot assignment`
  Start with `ai9414 demo csp-delivery`
- `STRIPS planning`
  Start with `ai9414 demo strips`

## What is included

- shared `ai9414` namespace package
- common FastAPI launcher and route contract
- common JSON schema models
- precomputed trace replay for a generated spatial graph DFS demo
- precomputed trace replay for a generated spatial graph BFS demo
- precomputed trace replay for a generated spatial graph greedy best-first demo
- precomputed trace replay for a generated spatial graph A* demo
- precomputed trace replay for a generated spatial graph uniform-cost demo
- precomputed trace replay for a generated spatial graph branch-and-bound demo
- precomputed trace replay for a visual DPLL propositional logic demo
- precomputed trace replay for a visual belief-state explorer demo
- precomputed trace replay for a visual foundation models tokenisation demo
- precomputed trace replay for a visual CSP map-colouring demo
- precomputed trace replay for a visual CSP delivery scheduling demo
- precomputed trace replay for a visual STRIPS planning demo
- static solution replay export with no backend dependency
- deterministic labyrinth presets plus seeded graph generation
- automated tests and developer documentation

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
ai9414 list
ai9414 demo graph-bnb
```

If your environment does not put console scripts on `PATH`, the module entry point works too:

```bash
python -m ai9414 demo graph-bnb
```

To see the curated example names for a demo:

```bash
ai9414 list --examples graph-dfs
```

## Development workflow

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
ai9414 demo graph-bnb
```

## Repository example scripts

The scripts under `examples/` are still useful for local development, documentation, and teaching materials, but they are no longer the primary installed interface.

To start the labyrinth example directly from a repository checkout:

```bash
python examples/labyrinth_demo.py
```

To start the spatial graph DFS example directly from a repository checkout:

```bash
python examples/graph_dfs_demo.py
```

To start the spatial graph BFS example directly from a repository checkout:

```bash
python examples/graph_bfs_demo.py
```

To start the spatial graph greedy best-first example directly from a repository checkout:

```bash
python examples/graph_gbfs_demo.py
```

To start the spatial graph A* example directly from a repository checkout:

```bash
python examples/graph_astar_demo.py
```

To start the spatial graph uniform-cost example directly from a repository checkout:

```bash
python examples/graph_ucs_demo.py
```

To start the spatial graph branch-and-bound example directly from a repository checkout:

```bash
python examples/graph_branch_and_bound_demo.py
```

To start the DPLL logic example directly from a repository checkout:

```bash
python examples/logic_dpll_demo.py
```

To start the reasoning-with-uncertainty example directly from a repository checkout:

```bash
python examples/uncertainty_demo.py
```

To start the foundation models tokenisation example directly from a repository checkout:

```bash
python examples/foundation_models_demo.py
```

To start the CSP map-colouring example directly from a repository checkout:

```bash
python examples/csp_demo.py
```

To start the CSP delivery scheduling example directly from a repository checkout:

```bash
python examples/delivery_csp_demo.py
```

To start the STRIPS planning example directly from a repository checkout:

```bash
python examples/strips_demo.py
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

Spatial graph A* example:

```python
from ai9414.graph_astar import GraphAStarDemo

app = GraphAStarDemo()
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

Visual DPLL example:

```python
from ai9414.logic import DpllDemo

app = DpllDemo()
app.load_example("unit_chain")
app.show()
```

Reasoning with uncertainty example:

```python
from ai9414.uncertainty import BeliefStateExplorer

app = BeliefStateExplorer()
app.load_example("office_localisation_basic")
app.show()
```

Set a custom initial belief:

```python
from ai9414.uncertainty import BeliefStateExplorer

app = BeliefStateExplorer()
app.load_example("office_localisation_basic")
app.set_belief({
    "mail_room": 0.1,
    "office_a": 0.4,
    "corridor": 0.2,
    "office_b": 0.2,
    "lab": 0.1,
})
app.show()
```

Foundation models tokenisation example:

```python
from ai9414.foundation_models import TokenisationExplorer

app = TokenisationExplorer()
app.load_example("simple_sentence")
app.show()
```

Custom tokenisation text:

```python
from ai9414.foundation_models import TokenisationExplorer

app = TokenisationExplorer()
app.load_corpus("office_messages")
app.learn_merges(12)
app.set_text("Deliver parcel to Office A before 10:30.")
app.show()
```

Visual CSP example:

```python
from ai9414.csp import CSPDemo

app = CSPDemo(example="australia")
app.set_algorithm("backtracking_forward_checking")
app.show()
```

Custom CSP map:

```python
from ai9414.csp import CSPDemo

app = CSPDemo()
app.load_map_problem(
    regions=["a", "b", "c", "d"],
    adjacency={
        "a": ["b", "c"],
        "b": ["a", "c", "d"],
        "c": ["a", "b", "d"],
        "d": ["b", "c"],
    },
    colours=["red", "green", "blue"],
)
app.set_variable_ordering("mrv")
app.show()
```

Delivery scheduling CSP example:

```python
from ai9414.delivery_csp import DeliveryCSPDemo

app = DeliveryCSPDemo(example="weekday_schedule")
app.set_algorithm("backtracking_forward_checking")
app.show()
```

Custom delivery scheduling CSP:

```python
from ai9414.delivery_csp import DeliveryCSPDemo

app = DeliveryCSPDemo()
app.load_delivery_problem(
    deliveries=[
        {"id": "a", "label": "Delivery A", "short_label": "A", "colour": "#c75b4a"},
        {"id": "b", "label": "Delivery B", "short_label": "B", "colour": "#4d79ab"},
    ],
    slots=[
        {"id": "slot_1", "label": "09:00", "order": 0},
        {"id": "slot_2", "label": "11:00", "order": 1},
    ],
    rooms=[
        {"id": "dock", "label": "Dock"},
    ],
    values=[
        {"id": "slot_1_dock", "slot": "slot_1", "room": "dock", "label": "09:00 @ Dock"},
        {"id": "slot_2_dock", "slot": "slot_2", "room": "dock", "label": "11:00 @ Dock"},
    ],
    domains={
        "a": ["slot_1_dock", "slot_2_dock"],
        "b": ["slot_2_dock"],
    },
    constraints=[
        {
            "kind": "precedence",
            "left": "a",
            "right": "b",
            "label": "A before B",
            "description": "Delivery A must happen before delivery B.",
        }
    ],
)
app.set_variable_ordering("mrv")
app.show()
```

Visual STRIPS planning example:

```python
from ai9414.strips import StripsDemo

app = StripsDemo()
app.load_example("canonical_delivery")
app.show()
```

Custom STRIPS problem:

```python
from ai9414.strips import StripsDemo, StripsProblem

problem = StripsProblem(
    rooms=["corridor", "mail_room", "office_a", "office_b", "lab"],
    robot_start="corridor",
    parcel_start="mail_room",
    keycard_start="office_a",
    locked_edge=("corridor", "lab"),
    door_locked=True,
    goal=[("at", "parcel", "lab")],
)

app = StripsDemo(problem=problem)
app.solve()
app.show()
```

Suggested STRIPS exercises:

- Move the keycard from office A to office B and predict how the plan changes.
- Start the robot in the mail room and explain why collecting the parcel too early is a bad idea.
- Unlock the lab door at the start and identify which action disappears from the plan.
- Move the locked door to the office B connection and compare the new plan structure.

Custom CNF with DPLL:

```python
from ai9414.logic import DpllDemo

app = DpllDemo()
app.load_cnf([
    ["A", "B"],
    ["~A", "C"],
    ["~B", "C"],
])
app.show()
```

Entailment with DPLL:

```python
from ai9414.logic import DpllDemo

app = DpllDemo(mode="entailment")
app.load_kb(
    formulas=["A -> B", "B -> C", "A"],
    query="C",
)
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

Live graph A* solver wrapper:

```python
from typing import Any
from ai9414.search import run_graph_astar_solver


def solve_astar(graph: dict[str, Any]) -> dict[str, Any]:
    ...


if __name__ == "__main__":
    run_graph_astar_solver(solve_astar)
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

Live DPLL solver wrapper:

```python
from typing import Any
from ai9414.logic import run_dpll_solver


def solve_dpll(problem: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    ...


if __name__ == "__main__":
    run_dpll_solver(solve_dpll)
```

## Repository structure

```text
src/ai9414/
  core/
  demo/
  graph_bfs/
  graph_dfs/
  graph_astar/
  graph_gbfs/
  graph_ucs/
  labyrinth/
  logic/
  search/
  frontend/
examples/
tests/
docs/
```
