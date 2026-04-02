const state = {
  manifest: null,
  session: null,
  serverTrace: null,
  serverSnapshots: [],
  playTimer: null,
  view: {
    playbackSpeed: 1,
    showExploredEdges: true,
    showPrunedBranches: true,
    showPlannerTrace: false,
    showTrueLocation: false,
    showCspDomains: true,
    cspViewMode: "trace",
    planningSelectedAction: "",
  },
  player: {
    stepIndex: 0,
    mode: "playback",
    liveTrace: null,
    liveSnapshots: [],
    size: "small",
    seed: "",
    message: "",
  },
};

const $ = (id) => document.getElementById(id);

const PYTHON_STUB = `from __future__ import annotations

from typing import Any

from ai9414.search import run_labyrinth_solver


Cell = tuple[int, int]


def parse_cell(raw: list[int] | tuple[int, int]) -> Cell:
    """
    Convert a cell from JSON format into a Python tuple.

    Input:
        raw: A row-column pair such as [1, 1] or (1, 1).

    Output:
        A tuple such as (1, 1).

    Example:
        parse_cell([3, 5]) returns (3, 5).
    """
    return (int(raw[0]), int(raw[1]))


def is_open_cell(labyrinth: dict[str, Any], cell: Cell) -> bool:
    """
    Return True if the given cell can be entered by the search.

    Input:
        labyrinth: A dictionary with keys such as 'rows', 'cols', 'grid',
            'start', and 'exit'.
        cell: A (row, col) pair.

    Output:
        True if the cell is inside the grid and is not a wall.
        False otherwise.

    Maze characters:
        '#': wall
        ' ': open cell
        'S': start
        'E': exit
    """
    row, col = cell
    rows = labyrinth["rows"]
    cols = labyrinth["cols"]
    grid = labyrinth["grid"]

    if row < 0 or row >= rows or col < 0 or col >= cols:
        return False

    return grid[row][col] != "#"


def get_neighbours(labyrinth: dict[str, Any], cell: Cell) -> list[Cell]:
    """
    Return all valid neighbouring cells in a fixed deterministic order.

    Movement order:
        up, right, down, left

    Important:
        The order matters. DFS will follow the first unvisited neighbour it sees.
        That means a different neighbour order changes the search trace.
    """
    row, col = cell
    candidates = [
        (row - 1, col),
        (row, col + 1),
        (row + 1, col),
        (row, col - 1),
    ]
    return [candidate for candidate in candidates if is_open_cell(labyrinth, candidate)]


def reconstruct_path(parents: dict[Cell, Cell | None], goal: Cell) -> list[Cell]:
    """
    Reconstruct the final path from the start cell to the goal cell.

    Input:
        parents: A dictionary mapping each visited cell to the cell from
            which it was first reached. The start cell should map to None.
        goal: The exit cell.
    """
    path: list[Cell] = []
    current: Cell | None = goal

    while current is not None:
        path.append(current)
        current = parents[current]

    path.reverse()
    return path


def make_trace_event(
    step: int,
    action: str,
    cell: Cell | None,
    parent: Cell | None,
    depth: int,
    stack: list[Cell],
) -> dict[str, Any]:
    """
    Build one trace event for the replay.

    The browser uses this event format directly.
    """
    return {
        "step": step,
        "action": action,
        "cell": None if cell is None else [cell[0], cell[1]],
        "parent": None if parent is None else [parent[0], parent[1]],
        "depth": depth,
        "stack": [[row, col] for (row, col) in stack],
    }


def solve_dfs(labyrinth: dict[str, Any]) -> dict[str, Any]:
    """
    Solve the labyrinth using depth-first search and return a full result.

    This is the main function you are expected to implement.
    You should replace the TODO section below with a complete iterative DFS.

    Student responsibilities:
        - generate valid neighbours
        - run DFS
        - record visited_order
        - reconstruct the final path
        - build the trace list

    ai9414 responsibilities:
        - start the local web server
        - expose the /solve endpoint
        - pass the labyrinth dictionary into this function
        - validate the result shape
        - send the result back to the browser

    Input format:
        {
            "rows": 6,
            "cols": 7,
            "grid": [
                "#######",
                "#S #  #",
                "#  # ##",
                "##   E#",
                "#     #",
                "#######"
            ],
            "start": [1, 1],
            "exit": [3, 5]
        }

    Required return format:
        {
            "algorithm": "dfs",
            "status": "found" or "not_found",
            "trace": [...],
            "path": [[row, col], ...],
            "visited_order": [[row, col], ...],
        }

    Trace actions:
        - start: emit once at the entrance
        - expand: emit when DFS moves into a new cell
        - backtrack: emit when DFS gives up on a branch and pops a cell
        - found: emit once when the exit is reached
        - fail: emit once if the stack empties and no exit path exists

    Suggested plan:
        1. Parse the start and exit cells.
        2. Initialise stack, visited, parents, trace, visited_order, and step.
        3. Emit the start event.
        4. While the stack is not empty:
           - inspect the top cell
           - if it is the goal, reconstruct the path, emit found, and return
           - otherwise take the first unvisited neighbour
           - if one exists, push it and emit expand
           - otherwise pop the current cell and emit backtrack
        5. If the loop finishes, emit fail and return not_found

    Important:
        Keep the result meaningful even without the browser visualisation.
        The browser should simply replay the DFS result you return here.
    """
    start = parse_cell(labyrinth["start"])
    goal = parse_cell(labyrinth["exit"])

    # TODO:
    # Replace the placeholder result below with a full iterative DFS.
    # You are expected to return a complete dictionary with keys:
    # algorithm, status, trace, path, visited_order.
    # The helper functions above are here to keep the task focused on DFS logic.
    trace = [make_trace_event(0, "start", start, None, 0, [start])]
    return {
        "algorithm": "dfs",
        "status": "error",
        "message": "Replace the placeholder code inside solve_dfs with your full DFS implementation.",
        "trace": trace,
        "path": [],
        "visited_order": [[start[0], start[1]]],
    }


if __name__ == "__main__":
    run_labyrinth_solver(solve_dfs)
`;

const PYTHON_REQUIREMENTS = `ai9414
`;

const PYTHON_README = `# labyrinth dfs solver

This folder runs a tiny local solver for the labyrinth search example.
The web-app connection is handled for you by ai9414.
Your job is to implement the DFS logic.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_labyrinth.py

The solver starts on the local port expected by the browser app.

## what to implement

Open solve_labyrinth.py and look at:

- get_neighbours(...)
- reconstruct_path(...)
- solve_dfs(...)

The main function is solve_dfs(...).
It receives a maze as a Python dictionary and must return a dictionary containing:

- algorithm
- status
- trace
- path
- visited_order
`;

const GRAPH_PYTHON_STUB = `from __future__ import annotations

from typing import Any

from ai9414.search import run_graph_solver


def normalise_node_id(raw: Any) -> str:
    """
    Convert one node id into a Python string.

    Example:
        normalise_node_id("A") returns "A".
    """
    return str(raw)


def build_adjacency(graph: dict[str, Any]) -> dict[str, list[str]]:
    """
    Build an adjacency list from the graph dictionary.

    The graph uses this format:
        {
            "nodes": [{"id": "A", "x": 0.1, "y": 0.2}, ...],
            "edges": [{"u": "A", "v": "B"}, ...],
            "start": "A",
            "goal": "G"
        }
    """
    adjacency = {str(node["id"]): [] for node in graph["nodes"]}
    for edge in graph["edges"]:
        left = str(edge["u"])
        right = str(edge["v"])
        adjacency[left].append(right)
        adjacency[right].append(left)
    for node_id in adjacency:
        adjacency[node_id].sort()
    return adjacency


def get_neighbours(adjacency: dict[str, list[str]], node_id: str) -> list[str]:
    """
    Return neighbouring nodes in deterministic DFS order.

    Important:
        The order matters. DFS follows the first unvisited neighbour it sees.
    """
    return list(adjacency[node_id])


def reconstruct_path(parents: dict[str, str | None], goal: str) -> list[str]:
    """
    Reconstruct the final path from the start node to the goal node.
    """
    path: list[str] = []
    current: str | None = goal
    while current is not None:
        path.append(current)
        current = parents[current]
    path.reverse()
    return path


def make_trace_event(
    step: int,
    action: str,
    node_id: str | None,
    parent: str | None,
    depth: int,
    stack: list[str],
) -> dict[str, Any]:
    """
    Build one trace event for the replay.

    The browser uses this event format directly.
    """
    return {
        "step": step,
        "action": action,
        "node": node_id,
        "parent": parent,
        "depth": depth,
        "stack": list(stack),
    }


def solve_dfs(graph: dict[str, Any]) -> dict[str, Any]:
    """
    Solve the graph using depth-first search and return a full result.

    This is the main function you are expected to implement.
    You should replace the TODO section below with a complete iterative DFS.

    Student responsibilities:
        - build or use an adjacency structure
        - run DFS
        - record visited_order
        - reconstruct the final path
        - build the trace list

    ai9414 responsibilities:
        - start the local web server
        - expose the /solve endpoint
        - pass the graph dictionary into this function
        - validate the result shape
        - send the result back to the browser

    Required return format:
        {
            "algorithm": "dfs",
            "status": "found" or "not_found",
            "trace": [...],
            "path": ["A", "B", "G"],
            "visited_order": ["A", "B", "D", "G"],
        }

    Trace actions:
        - start: emit once at the start node
        - expand: emit when DFS moves into a new node
        - backtrack: emit when DFS gives up on a branch and pops a node
        - found: emit once when the goal is reached
        - fail: emit once if the stack empties and no goal path exists
    """
    start = normalise_node_id(graph["start"])
    goal = normalise_node_id(graph["goal"])
    adjacency = build_adjacency(graph)
    _ = (goal, adjacency)

    # TODO:
    # Replace the placeholder result below with a full iterative DFS.
    trace = [make_trace_event(0, "start", start, None, 0, [start])]
    return {
        "algorithm": "dfs",
        "status": "error",
        "message": "Replace the placeholder code inside solve_dfs with your full DFS implementation.",
        "trace": trace,
        "path": [],
        "visited_order": [start],
    }


if __name__ == "__main__":
    run_graph_solver(solve_dfs)
`;

const GRAPH_PYTHON_REQUIREMENTS = `ai9414
`;

const GRAPH_PYTHON_README = `# graph dfs solver

This folder runs a tiny local solver for the spatial graph search example.
The web-app connection is handled for you by ai9414.
Your job is to implement the DFS logic.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_graph.py

The solver starts on the local port expected by the browser app.

## what to implement

Open solve_graph.py and look at:

- build_adjacency(...)
- get_neighbours(...)
- reconstruct_path(...)
- solve_dfs(...)

The main function is solve_dfs(...).
It receives a graph as a Python dictionary and must return a dictionary containing:

- algorithm
- status
- trace
- path
- visited_order
`;

const GRAPH_BFS_PYTHON_STUB = `from __future__ import annotations

from collections import deque
from typing import Any

from ai9414.search import run_graph_bfs_solver


def normalise_node_id(raw: Any) -> str:
    """
    Convert one node id into a Python string.

    Example:
        normalise_node_id("A") returns "A".
    """
    return str(raw)


def build_adjacency(graph: dict[str, Any]) -> dict[str, list[str]]:
    """
    Build an adjacency list from the graph dictionary.

    The graph uses this format:
        {
            "nodes": [{"id": "A", "x": 0.1, "y": 0.2}, ...],
            "edges": [{"u": "A", "v": "B"}, ...],
            "start": "A",
            "goal": "G"
        }
    """
    adjacency = {str(node["id"]): [] for node in graph["nodes"]}
    for edge in graph["edges"]:
        left = str(edge["u"])
        right = str(edge["v"])
        adjacency[left].append(right)
        adjacency[right].append(left)
    for node_id in adjacency:
        adjacency[node_id].sort()
    return adjacency


def get_neighbours(adjacency: dict[str, list[str]], node_id: str) -> list[str]:
    """
    Return neighbouring nodes in deterministic BFS order.

    Important:
        The order matters. BFS visits each layer in this neighbour order.
    """
    return list(adjacency[node_id])


def reconstruct_path(parents: dict[str, str | None], goal: str) -> list[str]:
    """
    Reconstruct the final path from the start node to the goal node.
    """
    path: list[str] = []
    current: str | None = goal
    while current is not None:
        path.append(current)
        current = parents[current]
    path.reverse()
    return path


def make_trace_event(
    step: int,
    action: str,
    node_id: str | None,
    parent: str | None,
    depth: int,
    route: list[str],
) -> dict[str, Any]:
    """
    Build one trace event for the replay.

    The browser uses this event format directly.
    """
    return {
        "step": step,
        "action": action,
        "node": node_id,
        "parent": parent,
        "depth": depth,
        "route": list(route),
    }


def solve_bfs(graph: dict[str, Any]) -> dict[str, Any]:
    """
    Solve the graph using breadth-first search and return a full result.

    This is the main function you are expected to implement.
    You should replace the TODO section below with a complete iterative BFS.

    Student responsibilities:
        - build or use an adjacency structure
        - run BFS
        - record visited_order
        - reconstruct the final path
        - build the trace list

    ai9414 responsibilities:
        - start the local web server
        - expose the /solve endpoint
        - pass the graph dictionary into this function
        - validate the result shape
        - send the result back to the browser

    Required return format:
        {
            "algorithm": "bfs",
            "status": "found" or "not_found",
            "trace": [...],
            "path": ["A", "B", "G"],
            "visited_order": ["A", "B", "D", "G"],
        }

    Trace actions:
        - start: emit once at the start node
        - expand: emit when BFS discovers a new node
        - found: emit once when the goal is reached
        - fail: emit once if the frontier empties and no goal path exists

    Suggested plan:
        1. Parse the start and goal ids.
        2. Build the adjacency list.
        3. Initialise a queue, visited set, parents, trace, visited_order, and step.
        4. Emit the start event.
        5. While the queue is not empty:
           - pop the next node from the front of the queue
           - visit each unvisited neighbour in deterministic order
           - record its parent, visited_order, and route from the start
           - emit an expand event and push it onto the queue
           - if the neighbour is the goal, emit found and return
        6. If the loop finishes, emit fail and return not_found
    """
    start = normalise_node_id(graph["start"])
    goal = normalise_node_id(graph["goal"])
    adjacency = build_adjacency(graph)
    _ = (goal, adjacency, deque)

    # TODO:
    # Replace the placeholder result below with a full iterative BFS.
    trace = [make_trace_event(0, "start", start, None, 0, [start])]
    return {
        "algorithm": "bfs",
        "status": "error",
        "message": "Replace the placeholder code inside solve_bfs with your full BFS implementation.",
        "trace": trace,
        "path": [],
        "visited_order": [start],
    }


if __name__ == "__main__":
    run_graph_bfs_solver(solve_bfs)
`;

const GRAPH_BFS_PYTHON_REQUIREMENTS = `ai9414
`;

const GRAPH_BFS_PYTHON_README = `# graph bfs solver

This folder runs a tiny local solver for the spatial graph search example.
The web-app connection is handled for you by ai9414.
Your job is to implement the BFS logic.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_graph.py

The solver starts on the local port expected by the browser app.

## what to implement

Open solve_graph.py and look at:

- build_adjacency(...)
- get_neighbours(...)
- reconstruct_path(...)
- solve_bfs(...)

The main function is solve_bfs(...).
It receives a graph as a Python dictionary and must return a dictionary containing:

- algorithm
- status
- trace
- path
- visited_order
`;

const GRAPH_UCS_PYTHON_STUB = `from __future__ import annotations

import heapq
from typing import Any

from ai9414.search import run_graph_ucs_solver


def normalise_node_id(raw: Any) -> str:
    """
    Convert one node id into a Python string.
    """
    return str(raw)


def build_adjacency(graph: dict[str, Any]) -> dict[str, list[tuple[str, float]]]:
    """
    Build an adjacency list from the weighted graph dictionary.

    The graph uses this format:
        {
            "nodes": [{"id": "A", "x": 0.1, "y": 0.2}, ...],
            "edges": [{"u": "A", "v": "B", "cost": 1.7}, ...],
            "start": "A",
            "goal": "G"
        }
    """
    adjacency = {str(node["id"]): [] for node in graph["nodes"]}
    for edge in graph["edges"]:
        left = str(edge["u"])
        right = str(edge["v"])
        cost = float(edge["cost"])
        adjacency[left].append((right, cost))
        adjacency[right].append((left, cost))
    for node_id in adjacency:
        adjacency[node_id].sort(key=lambda item: (item[1], item[0]))
    return adjacency


def get_neighbours(adjacency: dict[str, list[tuple[str, float]]], node_id: str) -> list[tuple[str, float]]:
    """
    Return neighbouring nodes in deterministic UCS order.

    Important:
        The order matters. The demo expects a fixed order for a fixed graph.
    """
    return list(adjacency[node_id])


def reconstruct_path(parents: dict[str, str | None], goal: str) -> list[str]:
    """
    Reconstruct the final path from the start node to the goal node.
    """
    path: list[str] = []
    current: str | None = goal
    while current is not None:
        path.append(current)
        current = parents[current]
    path.reverse()
    return path


def make_trace_event(
    step: int,
    action: str,
    node_id: str | None,
    parent: str | None,
    depth: int,
    path_cost: float,
    current_path: list[str],
    current_cost: float,
    best_path: list[str],
    best_cost: float | None,
    considered_edge: list[str] | None = None,
) -> dict[str, Any]:
    """
    Build one trace event for the replay.

    The browser uses this event format directly.
    """
    return {
        "step": step,
        "action": action,
        "node": node_id,
        "parent": parent,
        "depth": depth,
        "path_cost": float(path_cost),
        "current_path": list(current_path),
        "current_cost": float(current_cost),
        "best_path": list(best_path),
        "best_cost": None if best_cost is None else float(best_cost),
        "considered_edge": None if considered_edge is None else list(considered_edge),
    }


def solve_ucs(graph: dict[str, Any]) -> dict[str, Any]:
    """
    Solve the weighted graph with uniform-cost search.

    This is the main function you are expected to implement.
    You should replace the TODO section below with a complete UCS solver.

    Student responsibilities:
        - build or use an adjacency structure
        - keep a priority queue ordered by total path cost
        - expand the cheapest frontier path first
        - keep the best known cost to each node
        - record visited_order
        - reconstruct the final optimal path
        - build the trace list

    ai9414 responsibilities:
        - start the local web server
        - expose the /solve endpoint
        - pass the graph dictionary into this function
        - validate the result shape
        - send the result back to the browser

    Required return format:
        {
            "algorithm": "ucs",
            "status": "found" or "not_found",
            "trace": [...],
            "path": ["A", "C", "G"],
            "best_cost": 4.7,
            "visited_order": ["A", "B", "C", "G"],
        }

    Trace actions:
        - start
        - expand
        - consider_edge
        - relax
        - found
        - fail

    Important:
        Uniform-cost search is not plain DFS or BFS.
        It must always expand the frontier path with the lowest total cost so far.
    """
    start = normalise_node_id(graph["start"])
    goal = normalise_node_id(graph["goal"])
    adjacency = build_adjacency(graph)
    _ = (goal, adjacency, heapq)

    # TODO:
    # Replace the placeholder result below with a full UCS implementation.
    trace = [
        make_trace_event(
            0,
            "start",
            start,
            None,
            0,
            0.0,
            [start],
            0.0,
            [],
            None,
        )
    ]
    return {
        "algorithm": "ucs",
        "status": "error",
        "message": "Replace the placeholder code inside solve_ucs with your full UCS implementation.",
        "trace": trace,
        "path": [],
        "best_cost": None,
        "visited_order": [start],
    }


if __name__ == "__main__":
    run_graph_ucs_solver(solve_ucs)
`;

const GRAPH_UCS_PYTHON_REQUIREMENTS = `ai9414
`;

const GRAPH_UCS_PYTHON_README = `# graph uniform-cost solver

This folder runs a tiny local solver for the spatial weighted graph search example.
The web-app connection is handled for you by ai9414.
Your job is to implement the uniform-cost search logic.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_graph.py

The solver starts on the local port expected by the browser app.

## what to implement

Open solve_graph.py and look at:

- build_adjacency(...)
- get_neighbours(...)
- reconstruct_path(...)
- make_trace_event(...)
- solve_ucs(...)

The main function is solve_ucs(...).
It receives a weighted graph as a Python dictionary and must return a dictionary containing:

- algorithm
- status
- trace
- path
- best_cost
- visited_order
`;

const GRAPH_GBFS_PYTHON_STUB = `from __future__ import annotations

import heapq
import math
from typing import Any

from ai9414.search import run_graph_gbfs_solver


def normalise_node_id(raw: Any) -> str:
    """
    Convert one node id into a Python string.
    """
    return str(raw)


def build_adjacency(graph: dict[str, Any]) -> dict[str, list[tuple[str, float]]]:
    """
    Build an adjacency list from the weighted graph dictionary.
    """
    adjacency = {str(node["id"]): [] for node in graph["nodes"]}
    for edge in graph["edges"]:
        left = str(edge["u"])
        right = str(edge["v"])
        cost = float(edge["cost"])
        adjacency[left].append((right, cost))
        adjacency[right].append((left, cost))
    for node_id in adjacency:
        adjacency[node_id].sort(key=lambda item: item[0])
    return adjacency


def heuristic_to_goal(graph: dict[str, Any], node_id: str) -> float:
    """
    Return the straight-line distance from node_id to the goal node.
    """
    positions = {str(node["id"]): (float(node["x"]), float(node["y"])) for node in graph["nodes"]}
    goal = normalise_node_id(graph["goal"])
    return math.dist(positions[node_id], positions[goal])


def get_neighbours(adjacency: dict[str, list[tuple[str, float]]], node_id: str) -> list[tuple[str, float]]:
    """
    Return neighbouring nodes in deterministic order.
    """
    return list(adjacency[node_id])


def make_trace_event(
    step: int,
    action: str,
    node_id: str | None,
    parent: str | None,
    depth: int,
    path_cost: float,
    current_path: list[str],
    current_cost: float,
    heuristic: float,
    considered_edge: list[str] | None = None,
) -> dict[str, Any]:
    """
    Build one trace event for the replay.
    """
    return {
        "step": step,
        "action": action,
        "node": node_id,
        "parent": parent,
        "depth": depth,
        "path_cost": float(path_cost),
        "current_path": list(current_path),
        "current_cost": float(current_cost),
        "heuristic": float(heuristic),
        "considered_edge": None if considered_edge is None else list(considered_edge),
    }


def solve_gbfs(graph: dict[str, Any]) -> dict[str, Any]:
    """
    Solve the weighted graph with greedy best-first search.

    This is the main function you are expected to implement.
    You should replace the TODO section below with a complete solver.

    Student responsibilities:
        - build or use an adjacency structure
        - compute the heuristic distance from each node to the goal
        - keep a priority queue ordered by that heuristic
        - expand the node that looks closest to the goal
        - record visited_order
        - return the first path found to the goal
        - build the trace list

    Important:
        Greedy best-first search does not guarantee the cheapest path.
        It chooses what to expand using the heuristic only.
    """
    start = normalise_node_id(graph["start"])
    goal = normalise_node_id(graph["goal"])
    adjacency = build_adjacency(graph)
    _ = (goal, adjacency, heapq)

    # TODO:
    # Replace the placeholder result below with a full greedy best-first solver.
    start_h = heuristic_to_goal(graph, start)
    trace = [
        make_trace_event(
            0,
            "start",
            start,
            None,
            0,
            0.0,
            [start],
            0.0,
            start_h,
        )
    ]
    return {
        "algorithm": "gbfs",
        "status": "error",
        "message": "Replace the placeholder code inside solve_gbfs with your full greedy best-first implementation.",
        "trace": trace,
        "path": [],
        "path_cost": None,
        "visited_order": [start],
    }


if __name__ == "__main__":
    run_graph_gbfs_solver(solve_gbfs)
`;

const GRAPH_GBFS_PYTHON_REQUIREMENTS = `ai9414
`;

const GRAPH_GBFS_PYTHON_README = `# graph greedy best-first solver

This folder runs a tiny local solver for the spatial weighted graph search example.
The web-app connection is handled for you by ai9414.
Your job is to implement the greedy best-first logic.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_graph.py

The solver starts on the local port expected by the browser app.

## what to implement

Open solve_graph.py and look at:

- build_adjacency(...)
- heuristic_to_goal(...)
- get_neighbours(...)
- make_trace_event(...)
- solve_gbfs(...)

The main function is solve_gbfs(...).
It receives a weighted graph as a Python dictionary and must return a dictionary containing:

- algorithm
- status
- trace
- path
- path_cost
- visited_order
`;

const GRAPH_ASTAR_PYTHON_STUB = `from __future__ import annotations

import heapq
import math
from typing import Any

from ai9414.search import run_graph_astar_solver


def normalise_node_id(raw: Any) -> str:
    """
    Convert one node id into a Python string.
    """
    return str(raw)


def build_adjacency(graph: dict[str, Any]) -> dict[str, list[tuple[str, float]]]:
    """
    Build an adjacency list from the weighted graph dictionary.
    """
    adjacency = {str(node["id"]): [] for node in graph["nodes"]}
    for edge in graph["edges"]:
        left = str(edge["u"])
        right = str(edge["v"])
        cost = float(edge["cost"])
        adjacency[left].append((right, cost))
        adjacency[right].append((left, cost))
    for node_id in adjacency:
        adjacency[node_id].sort(key=lambda item: (item[1], item[0]))
    return adjacency


def heuristic_to_goal(graph: dict[str, Any], node_id: str) -> float:
    """
    Return the straight-line distance from node_id to the goal node.
    """
    positions = {str(node["id"]): (float(node["x"]), float(node["y"])) for node in graph["nodes"]}
    goal = normalise_node_id(graph["goal"])
    return math.dist(positions[node_id], positions[goal])


def get_neighbours(adjacency: dict[str, list[tuple[str, float]]], node_id: str) -> list[tuple[str, float]]:
    """
    Return neighbouring nodes in deterministic order.
    """
    return list(adjacency[node_id])


def make_trace_event(
    step: int,
    action: str,
    node_id: str | None,
    parent: str | None,
    depth: int,
    path_cost: float,
    current_path: list[str],
    current_cost: float,
    heuristic: float,
    priority: float,
    best_cost: float | None,
    considered_edge: list[str] | None = None,
) -> dict[str, Any]:
    """
    Build one trace event for the replay.
    """
    return {
        "step": step,
        "action": action,
        "node": node_id,
        "parent": parent,
        "depth": depth,
        "path_cost": float(path_cost),
        "current_path": list(current_path),
        "current_cost": float(current_cost),
        "heuristic": float(heuristic),
        "priority": float(priority),
        "best_cost": None if best_cost is None else float(best_cost),
        "considered_edge": None if considered_edge is None else list(considered_edge),
    }


def solve_astar(graph: dict[str, Any]) -> dict[str, Any]:
    """
    Solve the weighted graph with A* search.

    This is the main function you are expected to implement.
    You should replace the TODO section below with a complete A* solver.

    Student responsibilities:
        - build or use an adjacency structure
        - compute the heuristic distance from each node to the goal
        - keep the best known path cost g(n) to each node
        - order the priority queue by f(n) = g(n) + h(n)
        - record visited_order
        - return the final optimal path and best cost
        - build the trace list

    Important:
        The heuristic here is straight-line distance to the goal.
        Because the edge costs are also geometric distances, this heuristic is admissible.
    """
    start = normalise_node_id(graph["start"])
    goal = normalise_node_id(graph["goal"])
    adjacency = build_adjacency(graph)
    _ = (goal, adjacency, heapq)

    # TODO:
    # Replace the placeholder result below with a full A* implementation.
    start_h = heuristic_to_goal(graph, start)
    trace = [
        make_trace_event(
            0,
            "start",
            start,
            None,
            0,
            0.0,
            [start],
            0.0,
            start_h,
            start_h,
            None,
        )
    ]
    return {
        "algorithm": "astar",
        "status": "error",
        "message": "Replace the placeholder code inside solve_astar with your full A* implementation.",
        "trace": trace,
        "path": [],
        "best_cost": None,
        "visited_order": [start],
    }


if __name__ == "__main__":
    run_graph_astar_solver(solve_astar)
`;

const GRAPH_ASTAR_PYTHON_REQUIREMENTS = `ai9414
`;

const GRAPH_ASTAR_PYTHON_README = `# graph a-star solver

This folder runs a tiny local solver for the spatial weighted graph search example.
The web-app connection is handled for you by ai9414.
Your job is to implement the A* search logic.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_graph.py

The solver starts on the local port expected by the browser app.

## what to implement

Open solve_graph.py and look at:

- build_adjacency(...)
- heuristic_to_goal(...)
- get_neighbours(...)
- make_trace_event(...)
- solve_astar(...)

The main function is solve_astar(...).
It receives a weighted graph as a Python dictionary and must return a dictionary containing:

- algorithm
- status
- trace
- path
- best_cost
- visited_order
`;

const WEIGHTED_GRAPH_PYTHON_STUB = `from __future__ import annotations

from typing import Any

from ai9414.search import run_weighted_graph_solver


def normalise_node_id(raw: Any) -> str:
    """
    Convert one node id into a Python string.
    """
    return str(raw)


def build_adjacency(graph: dict[str, Any]) -> dict[str, list[tuple[str, float]]]:
    """
    Build an adjacency list from the weighted graph dictionary.

    The graph uses this format:
        {
            "nodes": [{"id": "A", "x": 0.1, "y": 0.2}, ...],
            "edges": [{"u": "A", "v": "B", "cost": 1.7}, ...],
            "start": "A",
            "goal": "G"
        }
    """
    adjacency = {str(node["id"]): [] for node in graph["nodes"]}
    for edge in graph["edges"]:
        left = str(edge["u"])
        right = str(edge["v"])
        cost = float(edge["cost"])
        adjacency[left].append((right, cost))
        adjacency[right].append((left, cost))
    for node_id in adjacency:
        adjacency[node_id].sort(key=lambda item: (item[1], item[0]))
    return adjacency


def get_neighbours(adjacency: dict[str, list[tuple[str, float]]], node_id: str) -> list[tuple[str, float]]:
    """
    Return neighbouring nodes in deterministic branch-and-bound order.

    Important:
        The order matters. The demo expects a fixed order for a fixed graph.
    """
    return list(adjacency[node_id])


def make_trace_event(
    step: int,
    action: str,
    node_id: str | None,
    parent: str | None,
    depth: int,
    path_cost: float,
    current_path: list[str],
    current_cost: float,
    best_path: list[str],
    best_cost: float | None,
    considered_edge: list[str] | None = None,
) -> dict[str, Any]:
    """
    Build one trace event for the replay.

    The browser uses this event format directly.
    """
    return {
        "step": step,
        "action": action,
        "node": node_id,
        "parent": parent,
        "depth": depth,
        "path_cost": float(path_cost),
        "current_path": list(current_path),
        "current_cost": float(current_cost),
        "best_path": list(best_path),
        "best_cost": None if best_cost is None else float(best_cost),
        "considered_edge": None if considered_edge is None else list(considered_edge),
    }


def solve_dfbb(graph: dict[str, Any]) -> dict[str, Any]:
    """
    Solve the weighted graph with depth-first branch-and-bound.

    This is the main function you are expected to implement.
    You should replace the TODO section below with a complete solver.

    Student responsibilities:
        - build or use an adjacency structure
        - run exhaustive DFS with backtracking
        - keep the best complete path cost found so far
        - prune any branch whose partial cost is already too large
        - record visited_order
        - return the final optimal path and best cost
        - build the trace list

    ai9414 responsibilities:
        - start the local web server
        - expose the /solve endpoint
        - pass the graph dictionary into this function
        - validate the result shape
        - send the result back to the browser

    Required return format:
        {
            "algorithm": "dfbb",
            "status": "found" or "not_found",
            "trace": [...],
            "path": ["A", "C", "G"],
            "best_cost": 4.7,
            "visited_order": ["A", "B", "D", "C", "G"],
        }

    Trace actions:
        - start
        - expand
        - consider_edge
        - descend
        - prune
        - backtrack
        - solution_found
        - best_updated
        - finished

    Important:
        Plain DFS is not enough here. You are expected to implement
        depth-first branch-and-bound, not ordinary DFS.
    """
    start = normalise_node_id(graph["start"])
    goal = normalise_node_id(graph["goal"])
    adjacency = build_adjacency(graph)
    _ = (goal, adjacency)

    # TODO:
    # Replace the placeholder result below with a full branch-and-bound solver.
    trace = [
        make_trace_event(
            0,
            "start",
            start,
            None,
            0,
            0.0,
            [start],
            0.0,
            [],
            None,
        )
    ]
    return {
        "algorithm": "dfbb",
        "status": "error",
        "message": "Replace the placeholder code inside solve_dfbb with your full branch-and-bound implementation.",
        "trace": trace,
        "path": [],
        "best_cost": None,
        "visited_order": [start],
    }


if __name__ == "__main__":
    run_weighted_graph_solver(solve_dfbb)
`;

const WEIGHTED_GRAPH_PYTHON_REQUIREMENTS = `ai9414
`;

const WEIGHTED_GRAPH_PYTHON_README = `# weighted graph branch-and-bound solver

This folder runs a tiny local solver for the weighted graph search example.
The web-app connection is handled for you by ai9414.
Your job is to implement the branch-and-bound search logic.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_weighted_graph.py

The solver starts on the local port expected by the browser app.

## what to implement

Open solve_weighted_graph.py and look at:

- build_adjacency(...)
- get_neighbours(...)
- make_trace_event(...)
- solve_dfbb(...)

The main function is solve_dfbb(...).
It receives a weighted graph as a Python dictionary and must return a dictionary containing:

- algorithm
- status
- trace
- path
- best_cost
- visited_order
`;

const DPLL_PYTHON_STUB = `from __future__ import annotations

from typing import Any

from ai9414.logic import run_dpll_solver


def make_event(
    step: int,
    action: str,
    *,
    node_id: str | None,
    parent_id: str | None,
    assignment: dict[str, bool],
    variable: str | None = None,
    value: bool | None = None,
    reason: str | None = None,
    clause_index: int | None = None,
) -> dict[str, Any]:
    return {
        "step": step,
        "action": action,
        "node_id": node_id,
        "parent_id": parent_id,
        "assignment": dict(assignment),
        "variable": variable,
        "value": value,
        "reason": reason,
        "clause_index": clause_index,
    }


def solve_dpll(problem: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    """
    Implement your own small DPLL solver here.

    Inputs:
        problem["clauses"] is a CNF clause list such as:
            [["A", "B"], ["~A", "C"], ["~B", "C"]]
        options contains the current UI settings such as:
            - unit_propagation
            - pure_literals
            - variable_order

    Required return shape:
        {
            "algorithm": "dpll",
            "mode": "sat" or "entailment",
            "status": "satisfiable" / "unsatisfiable" / "entailed" / "not_entailed",
            "trace": [...],
            "assignment": {"A": True, "B": False},
        }

    Trace actions:
        - start
        - choose_variable
        - assign
        - contradiction
        - backtrack
        - solution_found
        - finished
    """
    root_event = make_event(
        0,
        "start",
        node_id="t0",
        parent_id=None,
        assignment={},
    )
    return {
        "algorithm": "dpll",
        "mode": problem["mode"],
        "status": "error",
        "message": "Replace the placeholder code inside solve_dpll with your own DPLL implementation.",
        "trace": [root_event],
        "assignment": {},
    }


if __name__ == "__main__":
    run_dpll_solver(solve_dpll)
`;

const DPLL_PYTHON_REQUIREMENTS = `ai9414
`;

const DPLL_PYTHON_README = `# visual DPLL solver

This folder runs a tiny local solver for the DPLL logic demo.
The browser connection and response validation are handled by ai9414.
Your job is to implement the DPLL reasoning and emit a short event trace.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_dpll.py

## what to implement

Open solve_dpll.py and look at:

- make_event(...)
- solve_dpll(...)

The browser sends:

- problem: the current SAT or entailment task in CNF
- options: unit propagation, pure literals, and variable order

Your solver returns:

- algorithm
- mode
- status
- trace
- assignment
`;

const STRIPS_PYTHON_STUB = `from __future__ import annotations

from collections import deque
from typing import Any

from ai9414.strips import (
    apply_action_signature,
    get_applicable_actions,
    get_initial_facts,
    run_strips_solver,
)


def canonical_state_id(facts: list[tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    """
    Turn a fact list into a hashable canonical state identifier.
    """
    return tuple(sorted(tuple(fact) for fact in facts))


def goal_satisfied(facts: list[tuple[str, ...]], goal: list[list[str]]) -> bool:
    """
    Return True when every goal fact already appears in the current state.
    """
    state = {tuple(fact) for fact in facts}
    return all(tuple(goal_fact) in state for goal_fact in goal)


def solve_planner(problem: dict[str, Any]) -> dict[str, Any]:
    """
    Implement a small forward planner here.

    Inputs:
        problem: the current STRIPS office-delivery task.

    Required return shape:
        {
            "algorithm": "strips_bfs",
            "status": "found" / "not_found",
            "plan": [
                "move(robot, corridor, office_a)",
                "pickup_keycard(robot, keycard, office_a)",
            ],
            "stats": {
                "expanded_states": 0,
                "generated_states": 1,
                "frontier_peak": 1,
            },
        }
    """
    start_facts = get_initial_facts(problem)
    start_state = canonical_state_id(start_facts)
    queue: deque[tuple[list[tuple[str, ...]], list[str]]] = deque([(start_facts, [])])
    visited = {start_state}
    stats = {
        "expanded_states": 0,
        "generated_states": 1,
        "frontier_peak": 1,
    }

    while queue:
        stats["frontier_peak"] = max(stats["frontier_peak"], len(queue))
        facts, plan = queue.popleft()
        stats["expanded_states"] += 1

        if goal_satisfied(facts, problem["goal"]):
            return {
                "algorithm": "strips_bfs",
                "status": "found",
                "plan": plan,
                "stats": stats,
            }

        for action in get_applicable_actions(problem, facts):
            next_facts = apply_action_signature(problem, facts, action)
            state_id = canonical_state_id(next_facts)
            if state_id in visited:
                continue
            visited.add(state_id)
            queue.append((next_facts, [*plan, action]))
            stats["generated_states"] += 1

    return {
        "algorithm": "strips_bfs",
        "status": "not_found",
        "plan": [],
        "stats": stats,
    }


if __name__ == "__main__":
    run_strips_solver(solve_planner)
`;

const STRIPS_PYTHON_REQUIREMENTS = `ai9414
`;

const STRIPS_PYTHON_README = `# visual STRIPS planner

This folder runs a tiny local Python planner for the STRIPS planning demo.
The browser connection and replay formatting are handled by ai9414.
Your job is to return a grounded action plan for the current symbolic problem.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local planner with:

    python solve_strips.py

## what to implement

Open solve_strips.py and look at:

- solve_planner(...)
- get_initial_facts(...)
- get_applicable_actions(...)
- apply_action_signature(...)

The browser sends:

- problem: the current STRIPS office-delivery task

Your solver returns:

- algorithm
- status
- plan
- optional stats
`;

const UNCERTAINTY_PYTHON_STUB = `from __future__ import annotations

from ai9414.uncertainty import run_uncertainty_solver


def predict_belief(
    belief: dict[str, float],
    transition_model: dict[str, dict[str, float]],
) -> dict[str, float]:
    """
    Apply the transition model for the chosen action.

    Input:
        belief: the current probability distribution over rooms
        transition_model: for each source room, a distribution over next rooms

    Output:
        A new normalised probability distribution over rooms.
    """
    raise NotImplementedError("Implement predict_belief.")


def update_belief(
    predicted_belief: dict[str, float],
    observation: str,
    observation_model: dict[str, dict[str, float]],
) -> dict[str, float]:
    """
    Apply the observation likelihoods and normalise the posterior.

    Input:
        predicted_belief: the belief after the action step
        observation: the current noisy sensor reading
        observation_model: for each room, likelihoods for each observation

    Output:
        A new normalised posterior belief distribution.
    """
    raise NotImplementedError("Implement update_belief.")


def bayes_filter_step(
    belief: dict[str, float],
    transition_model: dict[str, dict[str, float]],
    observation: str,
    observation_model: dict[str, dict[str, float]],
) -> dict[str, float]:
    """
    Perform one Bayes-filter update.

    This function should call predict_belief(...) and update_belief(...).
    """
    predicted = predict_belief(belief, transition_model)
    return update_belief(predicted, observation, observation_model)


if __name__ == "__main__":
    run_uncertainty_solver(predict_belief, update_belief, bayes_filter_step)
`;

const UNCERTAINTY_PYTHON_REQUIREMENTS = `ai9414
`;

const UNCERTAINTY_PYTHON_README = `# reasoning with uncertainty Bayes filter

This folder runs a tiny local Python backend for the belief-state explorer.
The browser connection and replay formatting are handled by ai9414.
Your job is to implement the Bayes-filter belief update.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local backend with:

    python solve_uncertainty.py

## what to implement

Open solve_uncertainty.py and implement:

- predict_belief(...)
- update_belief(...)
- bayes_filter_step(...)

The browser sends the current office localisation problem, including:

- the room list
- the action-specific transition models
- the observation model
- the scripted action and observation sequence

Your functions should always return a normalised belief distribution.
`;

const CSP_PYTHON_STUB = `from __future__ import annotations

from typing import Any

from ai9414.csp import build_unimplemented_csp_result, run_csp_solver


def solve_csp(problem: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    """
    Solve the map-colouring CSP and return a replayable event trace.

    The browser sends:
        - problem: variables, domains, neighbours, colours, and geometry
        - options: algorithm and ordering choices from the UI

    Your solver should return:
        - algorithm
        - status
        - events
        - optional assignment and stats
    """
    _ = (problem, options)

    # TODO:
    # Replace this placeholder with your own backtracking + forward checking solver.
    return build_unimplemented_csp_result()


if __name__ == "__main__":
    run_csp_solver(solve_csp)
`;

const CSP_PYTHON_REQUIREMENTS = `ai9414
`;

const CSP_PYTHON_README = `# csp map-colouring solver

This folder runs a tiny local solver for the CSP map-colouring demo.
The browser connection and replay formatting are handled by ai9414.
Your job is to return an event trace for backtracking + forward checking.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_csp.py

## what to implement

Open solve_csp.py and implement solve_csp(...).
The browser sends:

- problem
- options

Your solver returns:

- algorithm
- status
- events
- optional assignment and stats
`;

const DELIVERY_CSP_PYTHON_STUB = `from __future__ import annotations

from typing import Any

from ai9414.delivery_csp import (
    build_unimplemented_delivery_csp_result,
    run_delivery_csp_solver,
)


def solve_delivery_csp(problem: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    """
    Solve the delivery time-slot CSP and return a replayable event trace.

    The browser sends:
        - problem: deliveries, slot-room values, domains, and constraints
        - options: algorithm and ordering choices from the UI

    Your solver should return:
        - algorithm
        - status
        - events
        - optional assignment and stats
    """
    _ = (problem, options)

    # TODO:
    # Replace this placeholder with your own backtracking + forward checking solver.
    return build_unimplemented_delivery_csp_result()


if __name__ == "__main__":
    run_delivery_csp_solver(solve_delivery_csp)
`;

const DELIVERY_CSP_PYTHON_REQUIREMENTS = `ai9414
`;

const DELIVERY_CSP_PYTHON_README = `# delivery time-slot CSP solver

This folder runs a tiny local solver for the delivery scheduling CSP demo.
The browser connection and replay formatting are handled by ai9414.
Your job is to return an event trace for backtracking + forward checking.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_delivery_csp.py

## what to implement

Open solve_delivery_csp.py and implement solve_delivery_csp(...).
The browser sends:

- problem
- options

Your solver returns:

- algorithm
- status
- events
- optional assignment and stats
`;

const $svgNode = (name, attributes = {}, text = "") => {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => {
    node.setAttribute(key, String(value));
  });
  if (text) {
    node.textContent = text;
  }
  return node;
};

const clone = (value) => JSON.parse(JSON.stringify(value));

const appType = () => state.manifest?.app_type;
const isStrips = () => appType() === "strips";
const isUncertainty = () => appType() === "uncertainty";
const isLogic = () => appType() === "logic";
const isFoundationModels = () => appType() === "foundation_models";
const isCsp = () => appType() === "csp";
const isDeliveryCsp = () => appType() === "delivery_csp";
const isCspFamily = () => isCsp() || isDeliveryCsp();
const isLabyrinth = () => appType() === "labyrinth";
const isGraphBfs = () => appType() === "graph_bfs";
const isGraphDfs = () => appType() === "graph_dfs";
const isGraphAStar = () => appType() === "graph_astar";
const isGraphGbfs = () => appType() === "graph_gbfs";
const isGraphUcs = () => appType() === "graph_ucs";
const isGraphReachability = () => isGraphDfs() || isGraphBfs();
const isWeightedSearch = () => appType() === "search";
const isWeightedGraphSearch = () => isWeightedSearch() || isGraphUcs() || isGraphGbfs() || isGraphAStar();
const isLivePythonApp = () => Boolean(state.session?.data?.live_python);

const CRC32_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let index = 0; index < 256; index += 1) {
    let value = index;
    for (let bit = 0; bit < 8; bit += 1) {
      value = (value & 1) !== 0 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
    }
    table[index] = value >>> 0;
  }
  return table;
})();

function crc32(bytes) {
  let crc = 0xffffffff;
  bytes.forEach((byte) => {
    crc = CRC32_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  });
  return (crc ^ 0xffffffff) >>> 0;
}

function writeUint16(view, offset, value) {
  view.setUint16(offset, value, true);
}

function writeUint32(view, offset, value) {
  view.setUint32(offset, value >>> 0, true);
}

function concatUint8Arrays(chunks) {
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const output = new Uint8Array(totalLength);
  let offset = 0;
  chunks.forEach((chunk) => {
    output.set(chunk, offset);
    offset += chunk.length;
  });
  return output;
}

function createZipArchive(files) {
  const encoder = new TextEncoder();
  const localParts = [];
  const centralParts = [];
  let localOffset = 0;

  files.forEach((file) => {
    const nameBytes = encoder.encode(file.name);
    const dataBytes = encoder.encode(file.content);
    const checksum = crc32(dataBytes);

    const localHeader = new Uint8Array(30);
    const localView = new DataView(localHeader.buffer);
    writeUint32(localView, 0, 0x04034b50);
    writeUint16(localView, 4, 20);
    writeUint16(localView, 6, 0);
    writeUint16(localView, 8, 0);
    writeUint16(localView, 10, 0);
    writeUint16(localView, 12, 0);
    writeUint32(localView, 14, checksum);
    writeUint32(localView, 18, dataBytes.length);
    writeUint32(localView, 22, dataBytes.length);
    writeUint16(localView, 26, nameBytes.length);
    writeUint16(localView, 28, 0);
    localParts.push(localHeader, nameBytes, dataBytes);

    const centralHeader = new Uint8Array(46);
    const centralView = new DataView(centralHeader.buffer);
    writeUint32(centralView, 0, 0x02014b50);
    writeUint16(centralView, 4, 20);
    writeUint16(centralView, 6, 20);
    writeUint16(centralView, 8, 0);
    writeUint16(centralView, 10, 0);
    writeUint16(centralView, 12, 0);
    writeUint16(centralView, 14, 0);
    writeUint32(centralView, 16, checksum);
    writeUint32(centralView, 20, dataBytes.length);
    writeUint32(centralView, 24, dataBytes.length);
    writeUint16(centralView, 28, nameBytes.length);
    writeUint16(centralView, 30, 0);
    writeUint16(centralView, 32, 0);
    writeUint16(centralView, 34, 0);
    writeUint16(centralView, 36, 0);
    writeUint32(centralView, 38, 0);
    writeUint32(centralView, 42, localOffset);
    centralParts.push(centralHeader, nameBytes);

    localOffset += localHeader.length + nameBytes.length + dataBytes.length;
  });

  const localData = concatUint8Arrays(localParts);
  const centralDirectory = concatUint8Arrays(centralParts);

  const endRecord = new Uint8Array(22);
  const endView = new DataView(endRecord.buffer);
  writeUint32(endView, 0, 0x06054b50);
  writeUint16(endView, 4, 0);
  writeUint16(endView, 6, 0);
  writeUint16(endView, 8, files.length);
  writeUint16(endView, 10, files.length);
  writeUint32(endView, 12, centralDirectory.length);
  writeUint32(endView, 16, localData.length);
  writeUint16(endView, 20, 0);

  return new Blob([localData, centralDirectory, endRecord], {
    type: "application/zip",
  });
}

function deepMerge(base, patch) {
  Object.entries(patch || {}).forEach(([key, value]) => {
    if (
      value &&
      typeof value === "object" &&
      !Array.isArray(value) &&
      base[key] &&
      typeof base[key] === "object" &&
      !Array.isArray(base[key])
    ) {
      deepMerge(base[key], value);
      return;
    }
    base[key] = clone(value);
  });
  return base;
}

function buildSnapshots(trace) {
  const initial = clone(trace.initial_state || {});
  const snapshots = [initial];
  let current = clone(initial);
  (trace.steps || []).forEach((step) => {
    current = deepMerge(clone(current), step.state_patch || {});
    snapshots.push(clone(current));
  });
  return snapshots;
}

function formatNumber(value, digits = 3) {
  return value === null || value === undefined ? "none" : Number(value).toFixed(digits);
}

function cellKey(cell) {
  return `${cell[0]},${cell[1]}`;
}

function edgeId(u, v) {
  return [u, v].sort().join("--");
}

function pathToEdgeIds(path) {
  const ids = new Set();
  for (let index = 0; index < path.length - 1; index += 1) {
    ids.add(edgeId(path[index], path[index + 1]));
  }
  return ids;
}

function routeKey(path) {
  return path.join("->");
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error?.message || "Request failed");
  }
  return payload;
}

async function postAction(action, payload = {}) {
  return requestJson("/api/action", {
    method: "POST",
    body: JSON.stringify({ action, payload }),
  });
}

async function loadApp() {
  const [manifest, session, trace, examplesPayload] = await Promise.all([
    requestJson("/api/manifest"),
    requestJson("/api/state"),
    requestJson("/api/trace"),
    requestJson("/api/examples"),
  ]);

  state.manifest = manifest;
  state.session = session;
  state.serverTrace = trace;
  state.serverSnapshots = buildSnapshots(trace);
  state.view.playbackSpeed = Number(session.options.playback_speed || 1);
  state.player.mode = "playback";
  if (session.data.live_python) {
    state.player.size = session.data.live_python.size;
    state.player.seed = session.data.live_python.seed;
  }
  populateExamples(examplesPayload.examples || []);
  syncControls();
  render();
}

function populateExamples(examples) {
  const select = $("example-select");
  select.innerHTML = "";
  examples.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = isLabyrinth() ? `${name}` : name;
    if (name === state.session.example_name) {
      option.selected = true;
    }
    select.appendChild(option);
  });
}

function populateSizeOptions() {
  const select = $("size-select");
  const availableSizes = state.session?.data?.live_python?.available_sizes || ["small", "medium", "large"];
  select.innerHTML = "";
  availableSizes.forEach((size) => {
    const option = document.createElement("option");
    option.value = size;
    option.textContent = size;
    if (size === state.player.size) {
      option.selected = true;
    }
    select.appendChild(option);
  });
}

function populateFoundationCorpora() {
  const select = $("foundation-corpus-select");
  const corpora = state.session?.data?.foundation_models?.available_corpora || [];
  select.innerHTML = "";
  corpora.forEach((corpus) => {
    const option = document.createElement("option");
    option.value = corpus.value;
    option.textContent = corpus.label;
    if (corpus.value === state.session?.data?.foundation_models?.selected_corpus) {
      option.selected = true;
    }
    select.appendChild(option);
  });
}

function syncControls() {
  populateSizeOptions();
  populateFoundationCorpora();
  $("speed-select").value = String(state.view.playbackSpeed);
  $("show-explored").checked = state.view.showExploredEdges;
  $("show-pruned").checked = state.view.showPrunedBranches;
  $("show-planner-trace").checked = state.view.showPlannerTrace;
  $("show-true-location").checked = state.view.showTrueLocation;
  $("show-csp-domains").checked = state.view.showCspDomains;
  $("csp-view-select").value = state.view.cspViewMode;
  $("mode-select").value = state.player.mode;
  $("size-select").value = state.player.size;
  $("seed-input").value = state.player.seed || "";
  if (isLogic()) {
    const options = state.session?.data?.options || {};
    $("logic-mode-select").value = options.problem_mode || "sat";
    $("logic-unit-propagation").checked = options.unit_propagation !== false;
    $("logic-pure-literals").checked = options.pure_literals === true;
    $("logic-order-select").value = options.variable_order || "alphabetical";
  }
  if (isFoundationModels()) {
    const options = state.session?.data?.options || {};
    $("foundation-mode-select").value = options.tokeniser_mode || "bpe";
    $("foundation-corpus-select").value = options.corpus || "office_messages";
    $("foundation-merges-select").value = String(options.num_merges ?? 12);
    $("foundation-context-select").value = String(options.context_window ?? 64);
  }
  if (isCspFamily()) {
    const options = state.session?.data?.options || {};
    $("csp-algorithm-select").value = options.algorithm || "backtracking_forward_checking";
    $("csp-variable-order-select").value = options.variable_ordering || "fixed";
    $("csp-value-order-select").value = options.value_ordering || "default";
    if (isCsp()) {
      $("csp-colour-select").value = String(options.num_colours || 3);
    }
  }
}

function setMessage(message) {
  state.player.message = message;
}

function stopPlay() {
  if (state.playTimer) {
    window.clearInterval(state.playTimer);
    state.playTimer = null;
  }
}

function playIntervalMs() {
  return Math.round(850 / state.view.playbackSpeed);
}

function evaluateLogicLiteral(literal, assignment) {
  const variable = literal.startsWith("~") ? literal.slice(1) : literal;
  if (!(variable in assignment)) return null;
  return literal.startsWith("~") ? !assignment[variable] : assignment[variable];
}

function formatLogicLiteral(literal) {
  return literal.replace("~", "¬");
}

function formatLogicClause(clause) {
  return `(${clause.map((literal) => formatLogicLiteral(literal)).join(" ∨ ")})`;
}

function evaluateLogicClauses(clauses, assignment) {
  return clauses.map((clause, index) => {
    const literals = [];
    const unassigned = [];
    let hasTrue = false;
    clause.forEach((literal) => {
      const value = evaluateLogicLiteral(literal, assignment);
      if (value === true) {
        hasTrue = true;
      }
      if (value === null) {
        unassigned.push(literal);
      }
      literals.push({
        raw: literal,
        text: formatLogicLiteral(literal),
        state: value === true ? "true" : value === false ? "false" : "unassigned",
      });
    });
    const status = hasTrue ? "satisfied" : unassigned.length === 0 ? "contradicted" : unassigned.length === 1 ? "unit" : "unresolved";
    return {
      index,
      status,
      literals,
      unit_literal: status === "unit" ? unassigned[0] : null,
      text: formatLogicClause(clause),
    };
  });
}

function logicSummary(clauses, assignment, variables) {
  return {
    satisfied: clauses.filter((clause) => clause.status === "satisfied").length,
    unresolved: clauses.filter((clause) => clause.status === "unresolved").length,
    unit: clauses.filter((clause) => clause.status === "unit").length,
    contradicted: clauses.filter((clause) => clause.status === "contradicted").length,
    assigned_variables: Object.keys(assignment || {}).length,
    total_variables: variables.length,
  };
}

function blankLogicTrace(problem) {
  const clauses = evaluateLogicClauses(problem.clauses, {});
  return {
    app_type: "logic",
    initial_state: {
      example_title: state.session?.data?.example_title || problem.title || "Visual DPLL",
      example_subtitle:
        state.session?.data?.example_subtitle ||
        problem.subtitle ||
        "Load a propositional example and step through DPLL.",
      algorithm_label: "DPLL",
      algorithm_note:
        "This view is ready for DPLL. Solve the current CNF in live Python mode to populate the trace.",
      goal_label:
        problem.mode === "sat"
          ? "Find a satisfying assignment"
          : "Check whether KB and not query are unsatisfiable",
      problem_mode: problem.mode,
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: "start",
            assignment_text: "No assignments",
            parent: null,
            depth: 0,
            path_cost: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.12,
            terminal: false,
            reason: "start",
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        best_tree_path: [],
        final_tree_path: [],
        finished: false,
        status: "ready",
        result: null,
      },
      logic: {
        mode: problem.mode,
        variables: clone(problem.variables || []),
        clauses,
        summary: logicSummary(clauses, {}, problem.variables || []),
        assignment: [],
        kb_formulas: clone(problem.kb_formulas || []),
        query: problem.query || null,
        entailment_target: problem.entailment_target || null,
        original_input: clone(problem.original_input || []),
      },
      stats: { decisions: 0, forced_assignments: 0, contradictions: 0, backtracks: 0 },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankCspTrace(problem, snapshot) {
  return {
    app_type: "csp",
    initial_state: clone(snapshot || {
      example_title: problem?.title || "Map-colouring CSP",
      example_subtitle:
        problem?.subtitle || "Load a map-colouring example and step through the CSP search.",
      algorithm_label: "Backtracking + forward checking",
      algorithm_note:
        "This view is ready for CSP search. Solve the current map-colouring problem in live Python mode to populate the replay.",
      goal_label: "Assign colours so every neighbouring pair differs",
      csp_problem: clone(problem || {}),
      csp: {
        variables: (problem?.regions || []).map((region) => ({
          variable: region,
          domain: clone(problem?.domains?.[region] || problem?.colours || []),
          assigned_value: null,
          status: "unchanged",
          changed: false,
          is_focus: false,
          is_failed: false,
          degree: problem?.neighbours?.[region]?.length || 0,
        })),
        assignments: {},
        domains: clone(problem?.domains || {}),
        focus_variable: null,
        failed_variable: null,
        last_changes: [],
        trace_entries: [],
        current_entry_index: null,
      },
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: "start",
            assignment_text: "No assignments",
            parent: null,
            depth: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.16,
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        best_tree_path: [],
        final_tree_path: [],
        finished: false,
        status: "ready",
        result: null,
      },
      stats: {
        assignments: 0,
        prunes: 0,
        backtracks: 0,
        wipeouts: 0,
      },
    }),
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankDeliveryCspTrace(problem, snapshot) {
  const valueMap = new Map((problem?.values || []).map((value) => [value.id, value]));
  const deliveries = problem?.deliveries || [];
  const domains = clone(problem?.domains || {});
  const buildCandidateMap = () => {
    const candidateMap = Object.fromEntries((problem?.values || []).map((value) => [value.id, []]));
    deliveries.forEach((delivery) => {
      (domains[delivery.id] || []).forEach((valueId) => {
        if (candidateMap[valueId]) {
          candidateMap[valueId].push(delivery.id);
        }
      });
    });
    return candidateMap;
  };

  return {
    app_type: "delivery_csp",
    initial_state: clone(snapshot || {
      example_title: problem?.title || "Delivery time-slot CSP",
      example_subtitle:
        problem?.subtitle || "Load a delivery scheduling example and step through the CSP search.",
      algorithm_label: "Backtracking + forward checking",
      algorithm_note:
        "This view is ready for CSP search. Solve the current delivery scheduling problem in live Python mode to populate the replay.",
      goal_label: "Assign every delivery to a legal room and time slot",
      delivery_problem: clone(problem || {}),
      delivery_csp: {
        variables: deliveries.map((delivery) => ({
          variable: delivery.id,
          label: delivery.label,
          short_label: delivery.short_label,
          colour: delivery.colour,
          domain: clone(domains[delivery.id] || []),
          domain_labels: (domains[delivery.id] || []).map((valueId) => valueMap.get(valueId)?.label || valueId),
          assigned_value: null,
          assigned_label: null,
          status: "unchanged",
          changed: false,
          is_focus: false,
          is_failed: false,
        })),
        assignments: {},
        domains,
        focus_variable: null,
        failed_variable: null,
        last_changes: [],
        trace_entries: [],
        current_entry_index: null,
        placements: [],
        candidate_map: buildCandidateMap(),
      },
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: "start",
            assignment_text: "No assignments",
            parent: null,
            depth: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.16,
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        best_tree_path: [],
        final_tree_path: [],
        finished: false,
        status: "ready",
        result: null,
      },
      stats: {
        assignments: 0,
        prunes: 0,
        backtracks: 0,
        wipeouts: 0,
      },
    }),
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankStripsTrace(problem, snapshot) {
  return {
    app_type: "strips",
    initial_state: clone(snapshot || {
      example_title: problem?.title || "Visual STRIPS planning",
      example_subtitle: problem?.subtitle || "Load an office-delivery example and inspect the symbolic state.",
      algorithm_label: "Forward STRIPS planning (BFS)",
      algorithm_note:
        "This view is ready for STRIPS planning. Solve the current office-delivery task in live Python mode to populate the plan replay.",
      goal_label: "Deliver the parcel to the lab",
      strips_problem: clone(problem || {}),
      planning: {
        facts: [],
        goal_facts: [],
        applicable_actions: [],
        selected_action: null,
        plan: [],
        plan_index: 0,
        goal_satisfied: false,
        world: {},
        search_trace: [],
      },
      search: {
        status: "ready",
        expanded_states: 0,
        generated_states: 1,
        frontier_peak: 1,
        current_depth: 0,
      },
      stats: {
        expanded_states: 0,
        generated_states: 1,
        frontier_peak: 1,
      },
    }),
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankLabyrinthTrace(labyrinth) {
  const start = labyrinth.start;
  return {
    app_type: "labyrinth",
    initial_state: {
      example_title: state.session?.data?.example_title || "Generated labyrinth",
      example_subtitle:
        state.session?.data?.example_subtitle ||
        "Generate a labyrinth, then solve it in live Python mode.",
      algorithm_label: "Depth-first search",
      algorithm_note:
        "This view is ready for DFS reachability. Solve the current labyrinth with Python to populate the trace.",
      goal_label: "Find any path from start to exit",
      labyrinth,
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: `(${start[0]},${start[1]})`,
            cell: clone(start),
            parent: null,
            depth: 0,
            path_cost: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.12,
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        current_route: [clone(start)],
        visited_order: [clone(start)],
        dead_end_cells: [],
        final_path: [],
        explored_count: 1,
        current_depth: 0,
        status: "searching",
        found: false,
      },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankSearchTrace(graph) {
  const start = graph.start;
  return {
    app_type: "search",
    initial_state: {
      example_title: state.session?.data?.example_title || "Generated weighted graph",
      example_subtitle:
        state.session?.data?.example_subtitle ||
        "Generate a weighted graph, then solve it in live Python mode.",
      algorithm_label: "Depth-first branch-and-bound",
      algorithm_note:
        "This view is ready for depth-first branch-and-bound. Solve the current weighted graph with Python to populate the trace.",
      goal_label: "Find the optimal path from start to goal",
      graph,
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: start,
            parent: null,
            depth: 0,
            path_cost: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.12,
            terminal: false,
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        best_tree_path: [],
        final_tree_path: [],
        current_graph_path: [start],
        best_graph_path: [],
        final_graph_path: [],
        explored_graph_edges: [],
        considered_edge: null,
        current_cost: 0,
        best_cost: null,
        finished: false,
        status: "searching",
      },
      stats: { expanded: 0, pruned: 0, solutions_found: 0, backtracks: 0 },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankGraphUcsTrace(graph) {
  const start = graph.start;
  return {
    app_type: "graph_ucs",
    initial_state: {
      example_title: state.session?.data?.example_title || "Generated weighted graph",
      example_subtitle:
        state.session?.data?.example_subtitle ||
        "Generate a weighted graph, then solve it in live Python mode.",
      algorithm_label: "Uniform-cost search",
      algorithm_note:
        "This view is ready for uniform-cost search. Solve the current weighted graph with Python to populate the trace.",
      goal_label: "Find the optimal path from start to goal",
      graph,
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: start,
            parent: null,
            depth: 0,
            path_cost: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.12,
            terminal: false,
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        best_tree_path: [],
        final_tree_path: [],
        current_graph_path: [start],
        best_graph_path: [],
        final_graph_path: [],
        visited_order: [start],
        explored_graph_edges: [],
        considered_edge: null,
        current_cost: 0,
        best_cost: null,
        explored_count: 1,
        current_depth: 0,
        status: "searching",
        found: false,
      },
      stats: { expanded: 0, relaxed: 0 },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankGraphGbfsTrace(graph) {
  const start = graph.start;
  const goalNode = graph.nodes.find((node) => node.id === graph.goal);
  const startNode = graph.nodes.find((node) => node.id === start);
  const startHeuristic =
    goalNode && startNode ? Math.hypot(startNode.x - goalNode.x, startNode.y - goalNode.y) : 0;
  return {
    app_type: "graph_gbfs",
    initial_state: {
      example_title: state.session?.data?.example_title || "Generated weighted graph",
      example_subtitle:
        state.session?.data?.example_subtitle ||
        "Generate a weighted graph, then solve it in live Python mode.",
      algorithm_label: "Greedy best-first search",
      algorithm_note:
        "This view is ready for greedy best-first search. Solve the current weighted graph with Python to populate the trace.",
      goal_label: "Find any path from start to goal",
      graph,
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: start,
            parent: null,
            depth: 0,
            path_cost: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.12,
            terminal: false,
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        best_tree_path: [],
        final_tree_path: [],
        current_graph_path: [start],
        best_graph_path: [],
        final_graph_path: [],
        visited_order: [start],
        explored_graph_edges: [],
        considered_edge: null,
        current_cost: 0,
        current_heuristic: startHeuristic,
        best_cost: null,
        explored_count: 1,
        current_depth: 0,
        status: "searching",
        found: false,
      },
      stats: { expanded: 0, enqueued: 1 },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankGraphAStarTrace(graph) {
  const start = graph.start;
  const goalNode = graph.nodes.find((node) => node.id === graph.goal);
  const startNode = graph.nodes.find((node) => node.id === start);
  const startHeuristic =
    goalNode && startNode ? Math.hypot(startNode.x - goalNode.x, startNode.y - goalNode.y) : 0;
  return {
    app_type: "graph_astar",
    initial_state: {
      example_title: state.session?.data?.example_title || "Generated weighted graph",
      example_subtitle:
        state.session?.data?.example_subtitle ||
        "Generate a weighted graph, then solve it in live Python mode.",
      algorithm_label: "A* search",
      algorithm_note:
        "This view is ready for A* search. Solve the current weighted graph with Python to populate the trace.",
      goal_label: "Find the optimal path from start to goal",
      graph,
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: start,
            parent: null,
            depth: 0,
            path_cost: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.12,
            terminal: false,
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        best_tree_path: [],
        final_tree_path: [],
        current_graph_path: [start],
        best_graph_path: [],
        final_graph_path: [],
        visited_order: [start],
        explored_graph_edges: [],
        considered_edge: null,
        current_cost: 0,
        current_heuristic: startHeuristic,
        current_priority: startHeuristic,
        best_cost: null,
        explored_count: 1,
        current_depth: 0,
        status: "searching",
        found: false,
      },
      stats: { expanded: 0, relaxed: 1 },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankGraphDfsTrace(graph) {
  const start = graph.start;
  return {
    app_type: "graph_dfs",
    initial_state: {
      example_title: state.session?.data?.example_title || "Generated graph",
      example_subtitle:
        state.session?.data?.example_subtitle ||
        "Generate a graph, then solve it in live Python mode.",
      algorithm_label: "Depth-first search",
      algorithm_note:
        "This view is ready for DFS reachability. Solve the current graph with Python to populate the trace.",
      goal_label: "Find any path from start to goal",
      graph,
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: start,
            parent: null,
            depth: 0,
            path_cost: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.12,
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        current_graph_path: [start],
        visited_order: [start],
        dead_end_nodes: [],
        final_graph_path: [],
        explored_graph_edges: [],
        explored_count: 1,
        current_depth: 0,
        status: "searching",
        found: false,
      },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankGraphBfsTrace(graph) {
  const start = graph.start;
  return {
    app_type: "graph_bfs",
    initial_state: {
      example_title: state.session?.data?.example_title || "Generated graph",
      example_subtitle:
        state.session?.data?.example_subtitle ||
        "Generate a graph, then solve it in live Python mode.",
      algorithm_label: "Breadth-first search",
      algorithm_note:
        "This view is ready for BFS reachability. Solve the current graph with Python to populate the trace.",
      goal_label: "Find any path from start to goal",
      graph,
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: start,
            parent: null,
            depth: 0,
            path_cost: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.12,
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        current_graph_path: [start],
        visited_order: [start],
        dead_end_nodes: [],
        final_graph_path: [],
        explored_graph_edges: [],
        explored_count: 1,
        current_depth: 0,
        status: "searching",
        found: false,
      },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function layoutTreeNodes(nodes) {
  const children = new Map();
  const depthMap = new Map();
  const orderMap = new Map();
  nodes.forEach((node) => {
    const parentKey = node.parent || "__root__";
    if (!children.has(parentKey)) {
      children.set(parentKey, []);
    }
    children.get(parentKey).push(node.tree_id);
    depthMap.set(node.tree_id, Number(node.depth));
    orderMap.set(node.tree_id, Number(node.order));
  });
  Array.from(children.values()).forEach((siblings) => {
    siblings.sort((left, right) => orderMap.get(left) - orderMap.get(right));
  });

  const xPositions = new Map();
  let cursor = 0;

  function assign(treeId) {
    const branch = children.get(treeId) || [];
    if (!branch.length) {
      cursor += 1;
      xPositions.set(treeId, cursor);
      return cursor;
    }
    const positions = branch.map(assign);
    const average = positions.reduce((sum, value) => sum + value, 0) / positions.length;
    xPositions.set(treeId, average);
    return average;
  }

  (children.get("__root__") || []).forEach(assign);
  const maxX = Math.max(...xPositions.values(), 1);
  const maxDepth = Math.max(...depthMap.values(), 0);

  return nodes.map((node) => ({
    ...node,
    x: 0.08 + ((xPositions.get(node.tree_id) - 1) / Math.max(maxX - 1, 1)) * 0.84,
    y: 0.12 + (depthMap.get(node.tree_id) / Math.max(maxDepth, 1)) * 0.76,
  }));
}

function buildLabyrinthTraceFromBackend(labyrinth, result) {
  if (!Array.isArray(result.trace) || !Array.isArray(result.path) || !Array.isArray(result.visited_order)) {
    throw new Error("Solver returned invalid data.");
  }

  const rawSnapshots = [];
  const treeNodes = new Map();
  const visibleTreeIds = [];
  const treeIdByCell = new Map();
  const deadEndCells = [];
  const deadEndSet = new Set();
  const visitedOrder = [];
  const activeTreePath = [];
  let currentRoute = [clone(labyrinth.start)];
  let currentTreeId = "t0";
  let counter = 1;
  let finalPath = [];
  let searchStatus = "searching";

  const root = {
    tree_id: "t0",
    graph_node: `(${labyrinth.start[0]},${labyrinth.start[1]})`,
    cell: clone(labyrinth.start),
    parent: null,
    depth: 0,
    path_cost: 0,
    status: "active",
    order: 0,
    x: 0.5,
    y: 0.12,
  };
  treeNodes.set("t0", root);
  visibleTreeIds.push("t0");
  treeIdByCell.set(cellKey(labyrinth.start), "t0");
  visitedOrder.push(clone(labyrinth.start));
  activeTreePath.push("t0");

  function snapshot() {
    return {
      tree: {
        nodes: visibleTreeIds.map((treeId) => clone(treeNodes.get(treeId))),
      },
      search: {
        active_tree_node: currentTreeId,
        active_tree_path: clone(activeTreePath),
        current_route: clone(currentRoute),
        visited_order: clone(visitedOrder),
        dead_end_cells: clone(deadEndCells),
        final_path: clone(finalPath),
        explored_count: visitedOrder.length,
        current_depth: Math.max(currentRoute.length - 1, 0),
        status: searchStatus,
        found: finalPath.length > 0,
      },
    };
  }

  result.trace.forEach((step, index) => {
    const action = step.action;
    const cell = Array.isArray(step.cell) ? clone(step.cell) : null;
    const parent = Array.isArray(step.parent) ? clone(step.parent) : null;

    if (action === "start") {
      currentRoute = clone(step.stack || [labyrinth.start]);
      searchStatus = "searching";
    } else if (action === "expand") {
      const parentId = treeIdByCell.get(cellKey(parent));
      const treeId = `t${counter}`;
      counter += 1;
      treeNodes.set(treeId, {
        tree_id: treeId,
        graph_node: `(${cell[0]},${cell[1]})`,
        cell,
        parent: parentId,
        depth: Number(step.depth || 0),
        path_cost: Number(step.depth || 0),
        status: "active",
        order: visibleTreeIds.length,
      });
      visibleTreeIds.push(treeId);
      treeIdByCell.set(cellKey(cell), treeId);
      currentRoute = clone(step.stack || []);
      if (!visitedOrder.some((item) => cellKey(item) === cellKey(cell))) {
        visitedOrder.push(cell);
      }
      activeTreePath.length = 0;
      currentRoute.forEach((routeCell) => {
        const routeTreeId = treeIdByCell.get(cellKey(routeCell));
        if (routeTreeId) activeTreePath.push(routeTreeId);
      });
      currentTreeId = treeId;
      if (parentId && treeNodes.get(parentId)) {
        treeNodes.get(parentId).status = "expanded";
      }
      searchStatus = "searching";
    } else if (action === "backtrack") {
      currentRoute = clone(step.stack || []);
      activeTreePath.length = 0;
      currentRoute.forEach((routeCell) => {
        const routeTreeId = treeIdByCell.get(cellKey(routeCell));
        if (routeTreeId) activeTreePath.push(routeTreeId);
      });
      const backtrackedTreeId = treeIdByCell.get(cellKey(cell));
      if (backtrackedTreeId && treeNodes.get(backtrackedTreeId)) {
        treeNodes.get(backtrackedTreeId).status = "backtracked";
      }
      if (cell && !deadEndSet.has(cellKey(cell))) {
        deadEndSet.add(cellKey(cell));
        deadEndCells.push(cell);
      }
      currentTreeId = activeTreePath[activeTreePath.length - 1] || "t0";
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "active";
      }
      searchStatus = "backtracking";
    } else if (action === "found") {
      if (cell && !treeIdByCell.has(cellKey(cell))) {
        const parentId = treeIdByCell.get(cellKey(parent));
        const treeId = `t${counter}`;
        counter += 1;
        treeNodes.set(treeId, {
          tree_id: treeId,
          graph_node: `(${cell[0]},${cell[1]})`,
          cell,
          parent: parentId,
          depth: Number(step.depth || 0),
          path_cost: Number(step.depth || 0),
          status: "final",
          order: visibleTreeIds.length,
        });
        visibleTreeIds.push(treeId);
        treeIdByCell.set(cellKey(cell), treeId);
      }
      currentRoute = clone(step.stack || []);
      finalPath = clone(step.stack || []);
      activeTreePath.length = 0;
      currentRoute.forEach((routeCell) => {
        const routeTreeId = treeIdByCell.get(cellKey(routeCell));
        if (routeTreeId) {
          activeTreePath.push(routeTreeId);
          treeNodes.get(routeTreeId).status = "final";
        }
      });
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      searchStatus = "exit found";
    } else if (action === "fail") {
      currentRoute = [];
      activeTreePath.length = 0;
      currentTreeId = null;
      searchStatus = "no path";
    }

    rawSnapshots.push({
      event_type: action,
      label:
        action === "start"
          ? "Start DFS"
          : action === "expand"
            ? `Expand (${cell[0]},${cell[1]})`
            : action === "backtrack"
              ? `Backtrack from (${cell[0]},${cell[1]})`
              : action === "found"
                ? "Exit found"
                : "No path found",
      annotation:
        action === "start"
          ? "The maze is ready. DFS starts at the entrance."
          : action === "expand"
            ? `DFS steps into (${cell[0]},${cell[1]}) and keeps exploring.`
            : action === "backtrack"
              ? `DFS retreats from (${cell[0]},${cell[1]}) after reaching a dead end.`
              : action === "found"
                ? "DFS has reached the exit and the successful path is now highlighted."
                : "DFS has exhausted the reachable maze without finding an exit.",
      teaching_note:
        action === "found"
          ? "Plain DFS stops as soon as it finds any exit path."
          : "The tree shows search history, while the maze view shows spatial movement.",
      snapshot: snapshot(),
    });
  });

  const laidOutNodes = layoutTreeNodes(visibleTreeIds.map((treeId) => treeNodes.get(treeId)));
  const layoutById = new Map(laidOutNodes.map((node) => [node.tree_id, node]));

  const initialState = blankLabyrinthTrace(labyrinth).initial_state;
  initialState.example_title = "Live Python labyrinth";
  initialState.example_subtitle = "Trace returned by your local Python DFS backend.";
  initialState.tree.nodes = initialState.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);

  const steps = rawSnapshots.map((entry, index) => {
    const snapshot = clone(entry.snapshot);
    snapshot.tree.nodes = snapshot.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);
    return {
      index,
      event_type: entry.event_type,
      label: entry.label,
      annotation: entry.annotation,
      teaching_note: entry.teaching_note,
      state_patch: snapshot,
    };
  });

  return {
    app_type: "labyrinth",
    initial_state: initialState,
    steps,
    summary: { step_count: steps.length, result: result.status || "found" },
  };
}

function buildGraphDfsTraceFromBackend(graph, result) {
  if (!Array.isArray(result.trace) || !Array.isArray(result.path) || !Array.isArray(result.visited_order)) {
    throw new Error("Solver returned invalid data.");
  }

  const rawSnapshots = [];
  const treeNodes = new Map();
  const visibleTreeIds = [];
  const treeIdByNode = new Map();
  const deadEndNodes = [];
  const deadEndSet = new Set();
  const visitedOrder = [];
  const activeTreePath = [];
  const exploredEdgeIds = new Set();
  let currentGraphPath = [graph.start];
  let currentTreeId = "t0";
  let counter = 1;
  let finalGraphPath = [];
  let searchStatus = "searching";

  const root = {
    tree_id: "t0",
    graph_node: graph.start,
    parent: null,
    depth: 0,
    path_cost: 0,
    status: "active",
    order: 0,
    x: 0.5,
    y: 0.12,
  };
  treeNodes.set("t0", root);
  visibleTreeIds.push("t0");
  treeIdByNode.set(graph.start, "t0");
  visitedOrder.push(graph.start);
  activeTreePath.push("t0");

  function snapshot() {
    return {
      tree: {
        nodes: visibleTreeIds.map((treeId) => clone(treeNodes.get(treeId))),
      },
      search: {
        active_tree_node: currentTreeId,
        active_tree_path: clone(activeTreePath),
        current_graph_path: clone(currentGraphPath),
        visited_order: clone(visitedOrder),
        dead_end_nodes: clone(deadEndNodes),
        final_graph_path: clone(finalGraphPath),
        explored_graph_edges: Array.from(exploredEdgeIds).map((id) => id.split("--")),
        explored_count: visitedOrder.length,
        current_depth: Math.max(currentGraphPath.length - 1, 0),
        status: searchStatus,
        found: finalGraphPath.length > 0,
      },
    };
  }

  result.trace.forEach((step) => {
    const action = step.action;
    const nodeId = typeof step.node === "string" ? step.node : null;
    const parent = typeof step.parent === "string" ? step.parent : null;

    if (action === "start") {
      currentGraphPath = clone(step.stack || [graph.start]);
      searchStatus = "searching";
    } else if (action === "expand") {
      const parentId = treeIdByNode.get(parent);
      const treeId = `t${counter}`;
      counter += 1;
      treeNodes.set(treeId, {
        tree_id: treeId,
        graph_node: nodeId,
        parent: parentId,
        depth: Number(step.depth || 0),
        path_cost: Number(step.depth || 0),
        status: "active",
        order: visibleTreeIds.length,
      });
      visibleTreeIds.push(treeId);
      treeIdByNode.set(nodeId, treeId);
      if (parent && nodeId) exploredEdgeIds.add(edgeId(parent, nodeId));
      currentGraphPath = clone(step.stack || []);
      if (!visitedOrder.includes(nodeId)) {
        visitedOrder.push(nodeId);
      }
      activeTreePath.length = 0;
      currentGraphPath.forEach((routeNode) => {
        const routeTreeId = treeIdByNode.get(routeNode);
        if (routeTreeId) activeTreePath.push(routeTreeId);
      });
      currentTreeId = treeId;
      if (parentId && treeNodes.get(parentId)) {
        treeNodes.get(parentId).status = "expanded";
      }
      searchStatus = "searching";
    } else if (action === "backtrack") {
      currentGraphPath = clone(step.stack || []);
      activeTreePath.length = 0;
      currentGraphPath.forEach((routeNode) => {
        const routeTreeId = treeIdByNode.get(routeNode);
        if (routeTreeId) activeTreePath.push(routeTreeId);
      });
      const backtrackedTreeId = treeIdByNode.get(nodeId);
      if (backtrackedTreeId && treeNodes.get(backtrackedTreeId)) {
        treeNodes.get(backtrackedTreeId).status = "backtracked";
      }
      if (nodeId && !deadEndSet.has(nodeId)) {
        deadEndSet.add(nodeId);
        deadEndNodes.push(nodeId);
      }
      currentTreeId = activeTreePath[activeTreePath.length - 1] || "t0";
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "active";
      }
      searchStatus = "backtracking";
    } else if (action === "found") {
      if (nodeId && !treeIdByNode.has(nodeId)) {
        const parentId = treeIdByNode.get(parent);
        const treeId = `t${counter}`;
        counter += 1;
        treeNodes.set(treeId, {
          tree_id: treeId,
          graph_node: nodeId,
          parent: parentId,
          depth: Number(step.depth || 0),
          path_cost: Number(step.depth || 0),
          status: "final",
          order: visibleTreeIds.length,
        });
        visibleTreeIds.push(treeId);
        treeIdByNode.set(nodeId, treeId);
      }
      currentGraphPath = clone(step.stack || []);
      finalGraphPath = clone(step.stack || []);
      activeTreePath.length = 0;
      currentGraphPath.forEach((routeNode) => {
        const routeTreeId = treeIdByNode.get(routeNode);
        if (routeTreeId) {
          activeTreePath.push(routeTreeId);
          treeNodes.get(routeTreeId).status = "final";
        }
      });
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      searchStatus = "goal found";
    } else if (action === "fail") {
      currentGraphPath = [];
      activeTreePath.length = 0;
      currentTreeId = null;
      searchStatus = "no path";
    }

    rawSnapshots.push({
      event_type: action,
      label:
        action === "start"
          ? "Start DFS"
          : action === "expand"
            ? `Expand ${nodeId}`
            : action === "backtrack"
              ? `Backtrack from ${nodeId}`
              : action === "found"
                ? "Goal found"
                : "No path found",
      annotation:
        action === "start"
          ? "The graph is ready. DFS starts at the start node."
          : action === "expand"
            ? `DFS steps into ${nodeId} and keeps exploring.`
            : action === "backtrack"
              ? `DFS retreats from ${nodeId} after exhausting that branch.`
              : action === "found"
                ? "DFS has reached the goal and the successful path is now highlighted."
                : "DFS has exhausted the reachable graph without finding the goal.",
      teaching_note:
        action === "found"
          ? "Plain DFS stops as soon as it finds any goal path."
          : "The tree shows search history, while the graph view shows movement through the original problem.",
      snapshot: snapshot(),
    });
  });

  const laidOutNodes = layoutTreeNodes(visibleTreeIds.map((treeId) => treeNodes.get(treeId)));
  const layoutById = new Map(laidOutNodes.map((node) => [node.tree_id, node]));

  const initialState = blankGraphDfsTrace(graph).initial_state;
  initialState.example_title = "Live Python graph";
  initialState.example_subtitle = "Trace returned by your local Python DFS backend.";
  initialState.tree.nodes = initialState.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);

  const steps = rawSnapshots.map((entry, index) => {
    const snapshot = clone(entry.snapshot);
    snapshot.tree.nodes = snapshot.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);
    return {
      index,
      event_type: entry.event_type,
      label: entry.label,
      annotation: entry.annotation,
      teaching_note: entry.teaching_note,
      state_patch: snapshot,
    };
  });

  return {
    app_type: "graph_dfs",
    initial_state: initialState,
    steps,
    summary: { step_count: steps.length, result: result.status || "found" },
  };
}

function buildGraphBfsTraceFromBackend(graph, result) {
  if (!Array.isArray(result.trace) || !Array.isArray(result.path) || !Array.isArray(result.visited_order)) {
    throw new Error("Solver returned invalid data.");
  }

  const rawSnapshots = [];
  const treeNodes = new Map();
  const visibleTreeIds = [];
  const treeIdByNode = new Map();
  const visitedOrder = [];
  const activeTreePath = [];
  const exploredEdgeIds = new Set();
  let currentGraphPath = [graph.start];
  let currentTreeId = "t0";
  let counter = 1;
  let finalGraphPath = [];
  let searchStatus = "searching";

  const root = {
    tree_id: "t0",
    graph_node: graph.start,
    parent: null,
    depth: 0,
    path_cost: 0,
    status: "active",
    order: 0,
    x: 0.5,
    y: 0.12,
  };
  treeNodes.set("t0", root);
  visibleTreeIds.push("t0");
  treeIdByNode.set(graph.start, "t0");
  visitedOrder.push(graph.start);
  activeTreePath.push("t0");

  function snapshot() {
    return {
      tree: {
        nodes: visibleTreeIds.map((treeId) => clone(treeNodes.get(treeId))),
      },
      search: {
        active_tree_node: currentTreeId,
        active_tree_path: clone(activeTreePath),
        current_graph_path: clone(currentGraphPath),
        visited_order: clone(visitedOrder),
        dead_end_nodes: [],
        final_graph_path: clone(finalGraphPath),
        explored_graph_edges: Array.from(exploredEdgeIds).map((id) => id.split("--")),
        explored_count: visitedOrder.length,
        current_depth: Math.max(currentGraphPath.length - 1, 0),
        status: searchStatus,
        found: finalGraphPath.length > 0,
      },
    };
  }

  result.trace.forEach((step) => {
    const action = step.action;
    const nodeId = typeof step.node === "string" ? step.node : null;
    const parent = typeof step.parent === "string" ? step.parent : null;
    const route = Array.isArray(step.route) ? clone(step.route) : [];

    if (action === "start") {
      currentGraphPath = route.length ? route : [graph.start];
      searchStatus = "searching";
    } else if (action === "expand") {
      const parentId = treeIdByNode.get(parent);
      const treeId = `t${counter}`;
      counter += 1;
      treeNodes.set(treeId, {
        tree_id: treeId,
        graph_node: nodeId,
        parent: parentId,
        depth: Number(step.depth || 0),
        path_cost: Number(step.depth || 0),
        status: "active",
        order: visibleTreeIds.length,
      });
      visibleTreeIds.push(treeId);
      treeIdByNode.set(nodeId, treeId);
      if (parent && nodeId) exploredEdgeIds.add(edgeId(parent, nodeId));
      currentGraphPath = route;
      if (!visitedOrder.includes(nodeId)) {
        visitedOrder.push(nodeId);
      }
      activeTreePath.length = 0;
      currentGraphPath.forEach((routeNode) => {
        const routeTreeId = treeIdByNode.get(routeNode);
        if (routeTreeId) activeTreePath.push(routeTreeId);
      });
      currentTreeId = treeId;
      if (parentId && treeNodes.get(parentId)) {
        treeNodes.get(parentId).status = "expanded";
      }
      searchStatus = "searching";
    } else if (action === "found") {
      if (nodeId && !treeIdByNode.has(nodeId)) {
        const parentId = treeIdByNode.get(parent);
        const treeId = `t${counter}`;
        counter += 1;
        treeNodes.set(treeId, {
          tree_id: treeId,
          graph_node: nodeId,
          parent: parentId,
          depth: Number(step.depth || 0),
          path_cost: Number(step.depth || 0),
          status: "final",
          order: visibleTreeIds.length,
        });
        visibleTreeIds.push(treeId);
        treeIdByNode.set(nodeId, treeId);
      }
      currentGraphPath = route.length ? route : clone(result.path || []);
      finalGraphPath = clone(result.path || currentGraphPath);
      activeTreePath.length = 0;
      currentGraphPath.forEach((routeNode) => {
        const routeTreeId = treeIdByNode.get(routeNode);
        if (routeTreeId) {
          activeTreePath.push(routeTreeId);
          treeNodes.get(routeTreeId).status = "final";
        }
      });
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      searchStatus = "goal found";
    } else if (action === "fail") {
      currentGraphPath = [];
      activeTreePath.length = 0;
      currentTreeId = null;
      searchStatus = "no path";
    }

    rawSnapshots.push({
      event_type: action,
      label:
        action === "start"
          ? "Start BFS"
          : action === "expand"
            ? `Expand ${nodeId}`
            : action === "found"
              ? "Goal found"
              : "No path found",
      annotation:
        action === "start"
          ? "The graph is ready. BFS starts at the start node."
          : action === "expand"
            ? `BFS discovers ${nodeId} and adds it to the next frontier layer.`
            : action === "found"
              ? "BFS has reached the goal and the successful path is now highlighted."
              : "BFS has exhausted the reachable graph without finding the goal.",
      teaching_note:
        action === "found"
          ? "In an unweighted graph, BFS reaches the goal on a shallowest path."
          : "The tree shows discovery order, while the graph view shows the route to the highlighted node.",
      snapshot: snapshot(),
    });
  });

  const laidOutNodes = layoutTreeNodes(visibleTreeIds.map((treeId) => treeNodes.get(treeId)));
  const layoutById = new Map(laidOutNodes.map((node) => [node.tree_id, node]));

  const initialState = blankGraphBfsTrace(graph).initial_state;
  initialState.example_title = "Live Python graph";
  initialState.example_subtitle = "Trace returned by your local Python BFS backend.";
  initialState.tree.nodes = initialState.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);

  const steps = rawSnapshots.map((entry, index) => {
    const snapshot = clone(entry.snapshot);
    snapshot.tree.nodes = snapshot.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);
    return {
      index,
      event_type: entry.event_type,
      label: entry.label,
      annotation: entry.annotation,
      teaching_note: entry.teaching_note,
      state_patch: snapshot,
    };
  });

  return {
    app_type: "graph_bfs",
    initial_state: initialState,
    steps,
    summary: { step_count: steps.length, result: result.status || "found" },
  };
}

function buildGraphUcsTraceFromBackend(graph, result) {
  if (
    !Array.isArray(result.trace) ||
    !Array.isArray(result.path) ||
    !Array.isArray(result.visited_order)
  ) {
    throw new Error("Solver returned invalid data.");
  }

  const rawSnapshots = [];
  const treeNodes = new Map();
  const visibleTreeIds = [];
  const treeIdByRoute = new Map();
  const exploredEdgeIds = new Set();
  const visitedOrder = [graph.start];
  let currentTreeId = "t0";
  let currentPath = [graph.start];
  let activeTreePath = ["t0"];
  let bestPath = [];
  let finalPath = [];
  let bestTreePath = [];
  let finalTreePath = [];
  let currentCost = 0;
  let bestCost = null;
  let consideredEdge = null;
  let searchStatus = "searching";
  const stats = { expanded: 0, relaxed: 0 };

  const root = {
    tree_id: "t0",
    graph_node: graph.start,
    parent: null,
    depth: 0,
    path_cost: 0,
    status: "active",
    order: 0,
    x: 0.5,
    y: 0.12,
    terminal: false,
  };
  treeNodes.set("t0", root);
  visibleTreeIds.push("t0");
  treeIdByRoute.set(routeKey([graph.start]), "t0");

  function ensureTreePath(route, terminal = false, pathCost = null) {
    const ids = [];
    route.forEach((nodeId, index) => {
      const prefix = route.slice(0, index + 1);
      const key = routeKey(prefix);
      let treeId = treeIdByRoute.get(key);
      if (!treeId) {
        const parentRoute = prefix.slice(0, -1);
        const parentId = treeIdByRoute.get(routeKey(parentRoute)) || null;
        const parentCost =
          parentId && treeNodes.get(parentId) ? Number(treeNodes.get(parentId).path_cost || 0) : 0;
        const nodeCost = index === route.length - 1 && pathCost !== null ? pathCost : parentCost;
        treeId = `t${visibleTreeIds.length}`;
        treeNodes.set(treeId, {
          tree_id: treeId,
          graph_node: nodeId,
          parent: parentId,
          depth: index,
          path_cost: nodeCost,
          status: "expanded",
          order: visibleTreeIds.length,
          terminal: terminal && index === route.length - 1,
        });
        visibleTreeIds.push(treeId);
        treeIdByRoute.set(key, treeId);
      } else if (index === route.length - 1 && pathCost !== null && treeNodes.get(treeId)) {
        treeNodes.get(treeId).path_cost = pathCost;
        treeNodes.get(treeId).terminal = terminal;
      }
      ids.push(treeId);
    });
    return ids;
  }

  function snapshot() {
    return {
      tree: {
        nodes: visibleTreeIds.map((treeId) => clone(treeNodes.get(treeId))),
      },
      search: {
        active_tree_node: currentTreeId,
        active_tree_path: clone(activeTreePath),
        best_tree_path: clone(bestTreePath),
        final_tree_path: clone(finalTreePath),
        current_graph_path: clone(currentPath),
        best_graph_path: clone(bestPath),
        final_graph_path: clone(finalPath),
        visited_order: clone(visitedOrder),
        explored_graph_edges: Array.from(exploredEdgeIds).map((id) => id.split("--")),
        considered_edge: consideredEdge ? clone(consideredEdge) : null,
        current_cost: currentCost,
        best_cost: bestCost,
        explored_count: visitedOrder.length,
        current_depth: Math.max(currentPath.length - 1, 0),
        status: searchStatus,
        found: finalPath.length > 0,
      },
      stats: clone(stats),
    };
  }

  result.trace.forEach((step) => {
    const action = step.action;
    const nodeId = typeof step.node === "string" ? step.node : null;
    const parent = typeof step.parent === "string" ? step.parent : null;
    currentPath = Array.isArray(step.current_path) && step.current_path.length ? clone(step.current_path) : [];
    currentCost = Number(step.current_cost || 0);
    bestPath = Array.isArray(step.best_path) ? clone(step.best_path) : [];
    bestCost = step.best_cost === null || step.best_cost === undefined ? null : Number(step.best_cost);
    consideredEdge = Array.isArray(step.considered_edge) ? clone(step.considered_edge) : null;

    if (action === "start") {
      currentPath = currentPath.length ? currentPath : [graph.start];
      activeTreePath = ensureTreePath(currentPath, false, 0);
      currentTreeId = activeTreePath[activeTreePath.length - 1] || "t0";
      searchStatus = "searching";
    } else if (action === "expand") {
      stats.expanded += 1;
      activeTreePath = ensureTreePath(currentPath, nodeId === graph.goal, Number(step.path_cost || currentCost));
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "active";
      }
      searchStatus = "searching";
    } else if (action === "consider_edge") {
      activeTreePath = ensureTreePath(currentPath, false, Number(step.path_cost || currentCost));
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      if (consideredEdge) {
        exploredEdgeIds.add(edgeId(consideredEdge[0], consideredEdge[1]));
      }
      searchStatus = "considering";
    } else if (action === "relax") {
      stats.relaxed += 1;
      activeTreePath = ensureTreePath(currentPath, nodeId === graph.goal, Number(step.path_cost || currentCost));
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      if (parent && nodeId) {
        exploredEdgeIds.add(edgeId(parent, nodeId));
      }
      if (nodeId && !visitedOrder.includes(nodeId)) {
        visitedOrder.push(nodeId);
      }
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "active";
      }
      searchStatus = "searching";
    } else if (action === "found") {
      finalPath = clone(result.path || bestPath || currentPath);
      bestPath = clone(finalPath);
      bestCost = result.best_cost === null || result.best_cost === undefined ? bestCost : Number(result.best_cost);
      activeTreePath = ensureTreePath(finalPath, true, bestCost ?? currentCost);
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      bestTreePath = clone(activeTreePath);
      finalTreePath = clone(activeTreePath);
      finalTreePath.forEach((treeId) => {
        if (treeNodes.get(treeId)) {
          treeNodes.get(treeId).status = "final";
        }
      });
      searchStatus = "goal found";
    } else if (action === "fail") {
      currentPath = [];
      activeTreePath = [];
      currentTreeId = null;
      consideredEdge = null;
      searchStatus = "no path";
    }

    rawSnapshots.push({
      event_type: action,
      label:
        action === "start"
          ? "Start UCS"
          : action === "expand"
            ? `Expand ${nodeId}`
            : action === "consider_edge"
              ? `Consider ${consideredEdge ? `${consideredEdge[0]} -> ${consideredEdge[1]}` : "edge"}`
              : action === "relax"
                ? `Relax ${nodeId}`
                : action === "found"
                  ? "Goal found"
                  : "No path found",
      annotation:
        action === "start"
          ? "The weighted graph is ready. UCS starts at the start node."
          : action === "expand"
            ? `UCS expands ${nodeId} because it is the cheapest route on the frontier.`
            : action === "consider_edge"
              ? "UCS checks whether this edge produces a cheaper route to its neighbour."
              : action === "relax"
                ? `The route to ${nodeId} improves, so UCS updates the frontier with the new path cost.`
                : action === "found"
                  ? "UCS has removed the goal from the frontier, so the highlighted path is optimal."
                  : "UCS has exhausted the frontier without reaching the goal.",
      teaching_note:
        action === "found"
          ? "With positive edge costs, the first goal removed from the frontier is optimal."
          : "The tree can contain repeated graph nodes when UCS later finds a cheaper route to the same graph state.",
      snapshot: snapshot(),
    });
  });

  const laidOutNodes = layoutTreeNodes(visibleTreeIds.map((treeId) => treeNodes.get(treeId)));
  const layoutById = new Map(laidOutNodes.map((node) => [node.tree_id, node]));

  const initialState = blankGraphUcsTrace(graph).initial_state;
  initialState.example_title = "Live Python weighted graph";
  initialState.example_subtitle = "Trace returned by your local Python UCS backend.";
  initialState.tree.nodes = initialState.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);

  const steps = rawSnapshots.map((entry, index) => {
    const snapshot = clone(entry.snapshot);
    snapshot.tree.nodes = snapshot.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);
    return {
      index,
      event_type: entry.event_type,
      label: entry.label,
      annotation: entry.annotation,
      teaching_note: entry.teaching_note,
      state_patch: snapshot,
    };
  });

  return {
    app_type: "graph_ucs",
    initial_state: initialState,
    steps,
    summary: { step_count: steps.length, result: result.status || "found" },
  };
}

function buildGraphGbfsTraceFromBackend(graph, result) {
  if (
    !Array.isArray(result.trace) ||
    !Array.isArray(result.path) ||
    !Array.isArray(result.visited_order)
  ) {
    throw new Error("Solver returned invalid data.");
  }

  const rawSnapshots = [];
  const treeNodes = new Map();
  const visibleTreeIds = [];
  const treeIdByRoute = new Map();
  const exploredEdgeIds = new Set();
  const visitedOrder = [graph.start];
  let currentTreeId = "t0";
  let currentPath = [graph.start];
  let activeTreePath = ["t0"];
  let finalPath = [];
  let finalTreePath = [];
  let currentCost = 0;
  let currentHeuristic = 0;
  let consideredEdge = null;
  let searchStatus = "searching";
  const stats = { expanded: 0, enqueued: 1 };

  const root = {
    tree_id: "t0",
    graph_node: graph.start,
    parent: null,
    depth: 0,
    path_cost: 0,
    status: "active",
    order: 0,
    x: 0.5,
    y: 0.12,
    terminal: false,
  };
  treeNodes.set("t0", root);
  visibleTreeIds.push("t0");
  treeIdByRoute.set(routeKey([graph.start]), "t0");

  function ensureTreePath(route, terminal = false, pathCost = null) {
    const ids = [];
    route.forEach((nodeId, index) => {
      const prefix = route.slice(0, index + 1);
      const key = routeKey(prefix);
      let treeId = treeIdByRoute.get(key);
      if (!treeId) {
        const parentRoute = prefix.slice(0, -1);
        const parentId = treeIdByRoute.get(routeKey(parentRoute)) || null;
        const parentCost =
          parentId && treeNodes.get(parentId) ? Number(treeNodes.get(parentId).path_cost || 0) : 0;
        const nodeCost = index === route.length - 1 && pathCost !== null ? pathCost : parentCost;
        treeId = `t${visibleTreeIds.length}`;
        treeNodes.set(treeId, {
          tree_id: treeId,
          graph_node: nodeId,
          parent: parentId,
          depth: index,
          path_cost: nodeCost,
          status: "queued",
          order: visibleTreeIds.length,
          terminal: terminal && index === route.length - 1,
        });
        visibleTreeIds.push(treeId);
        treeIdByRoute.set(key, treeId);
      } else if (index === route.length - 1 && pathCost !== null && treeNodes.get(treeId)) {
        treeNodes.get(treeId).path_cost = pathCost;
        treeNodes.get(treeId).terminal = terminal;
      }
      ids.push(treeId);
    });
    return ids;
  }

  function snapshot() {
    return {
      tree: {
        nodes: visibleTreeIds.map((treeId) => clone(treeNodes.get(treeId))),
      },
      search: {
        active_tree_node: currentTreeId,
        active_tree_path: clone(activeTreePath),
        best_tree_path: [],
        final_tree_path: clone(finalTreePath),
        current_graph_path: clone(currentPath),
        best_graph_path: [],
        final_graph_path: clone(finalPath),
        visited_order: clone(visitedOrder),
        explored_graph_edges: Array.from(exploredEdgeIds).map((id) => id.split("--")),
        considered_edge: consideredEdge ? clone(consideredEdge) : null,
        current_cost: currentCost,
        current_heuristic: currentHeuristic,
        best_cost: null,
        explored_count: visitedOrder.length,
        current_depth: Math.max(currentPath.length - 1, 0),
        status: searchStatus,
        found: finalPath.length > 0,
      },
      stats: clone(stats),
    };
  }

  result.trace.forEach((step) => {
    const action = step.action;
    const nodeId = typeof step.node === "string" ? step.node : null;
    const parent = typeof step.parent === "string" ? step.parent : null;
    currentPath = Array.isArray(step.current_path) && step.current_path.length ? clone(step.current_path) : [];
    currentCost = Number(step.current_cost || 0);
    currentHeuristic = Number(step.heuristic || 0);
    consideredEdge = Array.isArray(step.considered_edge) ? clone(step.considered_edge) : null;

    if (action === "start") {
      currentPath = currentPath.length ? currentPath : [graph.start];
      activeTreePath = ensureTreePath(currentPath, false, 0);
      currentTreeId = activeTreePath[activeTreePath.length - 1] || "t0";
      searchStatus = "searching";
    } else if (action === "expand") {
      stats.expanded += 1;
      activeTreePath = ensureTreePath(currentPath, nodeId === graph.goal, Number(step.path_cost || currentCost));
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "active";
      }
      searchStatus = "searching";
    } else if (action === "consider_edge") {
      activeTreePath = ensureTreePath(currentPath, false, Number(step.path_cost || currentCost));
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      if (consideredEdge) {
        exploredEdgeIds.add(edgeId(consideredEdge[0], consideredEdge[1]));
      }
      searchStatus = "considering";
    } else if (action === "enqueue") {
      stats.enqueued += 1;
      activeTreePath = ensureTreePath(currentPath, nodeId === graph.goal, Number(step.path_cost || currentCost));
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      if (parent && nodeId) {
        exploredEdgeIds.add(edgeId(parent, nodeId));
      }
      if (nodeId && !visitedOrder.includes(nodeId)) {
        visitedOrder.push(nodeId);
      }
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "queued";
      }
      searchStatus = "searching";
    } else if (action === "found") {
      finalPath = clone(result.path || currentPath);
      activeTreePath = ensureTreePath(finalPath, true, Number(result.path_cost || currentCost));
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      finalTreePath = clone(activeTreePath);
      finalTreePath.forEach((treeId) => {
        if (treeNodes.get(treeId)) {
          treeNodes.get(treeId).status = "final";
        }
      });
      searchStatus = "goal found";
    } else if (action === "fail") {
      currentPath = [];
      activeTreePath = [];
      currentTreeId = null;
      consideredEdge = null;
      searchStatus = "no path";
    }

    rawSnapshots.push({
      event_type: action,
      label:
        action === "start"
          ? "Start greedy best-first"
          : action === "expand"
            ? `Expand ${nodeId}`
            : action === "consider_edge"
              ? `Consider ${consideredEdge ? `${consideredEdge[0]} -> ${consideredEdge[1]}` : "edge"}`
              : action === "enqueue"
                ? `Queue ${nodeId}`
                : action === "found"
                  ? "Goal found"
                  : "No path found",
      annotation:
        action === "start"
          ? "The weighted graph is ready. Greedy best-first search starts at the start node."
          : action === "expand"
            ? `Greedy best-first search expands ${nodeId} because it currently looks closest to the goal.`
            : action === "consider_edge"
              ? "Check whether this neighbour has already been discovered before adding it to the heuristic frontier."
              : action === "enqueue"
                ? `${nodeId} is added to the frontier using only its heuristic estimate to the goal.`
                : action === "found"
                  ? "Greedy best-first search has reached the goal and the first discovered path is now highlighted."
                  : "Greedy best-first search has exhausted the frontier without reaching the goal.",
      teaching_note:
        action === "found"
          ? "Greedy best-first search can find a path quickly, but this path is not guaranteed to be optimal."
          : "The heuristic uses straight-line distance to the goal, so the search follows what looks geometrically promising.",
      snapshot: snapshot(),
    });
  });

  const laidOutNodes = layoutTreeNodes(visibleTreeIds.map((treeId) => treeNodes.get(treeId)));
  const layoutById = new Map(laidOutNodes.map((node) => [node.tree_id, node]));

  const initialState = blankGraphGbfsTrace(graph).initial_state;
  initialState.example_title = "Live Python weighted graph";
  initialState.example_subtitle = "Trace returned by your local Python greedy best-first backend.";
  initialState.tree.nodes = initialState.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);

  const steps = rawSnapshots.map((entry, index) => {
    const snapshot = clone(entry.snapshot);
    snapshot.tree.nodes = snapshot.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);
    return {
      index,
      event_type: entry.event_type,
      label: entry.label,
      annotation: entry.annotation,
      teaching_note: entry.teaching_note,
      state_patch: snapshot,
    };
  });

  return {
    app_type: "graph_gbfs",
    initial_state: initialState,
    steps,
    summary: { step_count: steps.length, result: result.status || "found" },
  };
}

function buildGraphAStarTraceFromBackend(graph, result) {
  if (
    !Array.isArray(result.trace) ||
    !Array.isArray(result.path) ||
    !Array.isArray(result.visited_order)
  ) {
    throw new Error("Solver returned invalid data.");
  }

  const rawSnapshots = [];
  const treeNodes = new Map();
  const visibleTreeIds = [];
  const treeIdByRoute = new Map();
  const exploredEdgeIds = new Set();
  const visitedOrder = [graph.start];
  let currentTreeId = "t0";
  let currentPath = [graph.start];
  let activeTreePath = ["t0"];
  let bestPath = [];
  let finalPath = [];
  let bestTreePath = [];
  let finalTreePath = [];
  let currentCost = 0;
  let currentHeuristic = 0;
  let currentPriority = 0;
  let bestCost = null;
  let consideredEdge = null;
  let searchStatus = "searching";
  const stats = { expanded: 0, relaxed: 1 };

  const root = {
    tree_id: "t0",
    graph_node: graph.start,
    parent: null,
    depth: 0,
    path_cost: 0,
    status: "active",
    order: 0,
    x: 0.5,
    y: 0.12,
    terminal: false,
  };
  treeNodes.set("t0", root);
  visibleTreeIds.push("t0");
  treeIdByRoute.set(routeKey([graph.start]), "t0");

  function ensureTreePath(route, terminal = false, pathCost = null) {
    const ids = [];
    route.forEach((nodeId, index) => {
      const prefix = route.slice(0, index + 1);
      const key = routeKey(prefix);
      let treeId = treeIdByRoute.get(key);
      if (!treeId) {
        const parentRoute = prefix.slice(0, -1);
        const parentId = treeIdByRoute.get(routeKey(parentRoute)) || null;
        const parentCost =
          parentId && treeNodes.get(parentId) ? Number(treeNodes.get(parentId).path_cost || 0) : 0;
        const nodeCost = index === route.length - 1 && pathCost !== null ? pathCost : parentCost;
        treeId = `t${visibleTreeIds.length}`;
        treeNodes.set(treeId, {
          tree_id: treeId,
          graph_node: nodeId,
          parent: parentId,
          depth: index,
          path_cost: nodeCost,
          status: "queued",
          order: visibleTreeIds.length,
          terminal: terminal && index === route.length - 1,
        });
        visibleTreeIds.push(treeId);
        treeIdByRoute.set(key, treeId);
      } else if (index === route.length - 1 && pathCost !== null && treeNodes.get(treeId)) {
        treeNodes.get(treeId).path_cost = pathCost;
        treeNodes.get(treeId).terminal = terminal;
      }
      ids.push(treeId);
    });
    return ids;
  }

  function snapshot() {
    return {
      tree: {
        nodes: visibleTreeIds.map((treeId) => clone(treeNodes.get(treeId))),
      },
      search: {
        active_tree_node: currentTreeId,
        active_tree_path: clone(activeTreePath),
        best_tree_path: clone(bestTreePath),
        final_tree_path: clone(finalTreePath),
        current_graph_path: clone(currentPath),
        best_graph_path: clone(bestPath),
        final_graph_path: clone(finalPath),
        visited_order: clone(visitedOrder),
        explored_graph_edges: Array.from(exploredEdgeIds).map((id) => id.split("--")),
        considered_edge: consideredEdge ? clone(consideredEdge) : null,
        current_cost: currentCost,
        current_heuristic: currentHeuristic,
        current_priority: currentPriority,
        best_cost: bestCost,
        explored_count: visitedOrder.length,
        current_depth: Math.max(currentPath.length - 1, 0),
        status: searchStatus,
        found: finalPath.length > 0,
      },
      stats: clone(stats),
    };
  }

  result.trace.forEach((step) => {
    const action = step.action;
    const nodeId = typeof step.node === "string" ? step.node : null;
    const parent = typeof step.parent === "string" ? step.parent : null;
    currentPath = Array.isArray(step.current_path) && step.current_path.length ? clone(step.current_path) : [];
    currentCost = Number(step.current_cost || 0);
    currentHeuristic = Number(step.heuristic || 0);
    currentPriority = Number(step.priority || 0);
    bestCost = step.best_cost === null || step.best_cost === undefined ? null : Number(step.best_cost);
    consideredEdge = Array.isArray(step.considered_edge) ? clone(step.considered_edge) : null;

    if (action === "start") {
      currentPath = currentPath.length ? currentPath : [graph.start];
      activeTreePath = ensureTreePath(currentPath, false, 0);
      currentTreeId = activeTreePath[activeTreePath.length - 1] || "t0";
      searchStatus = "searching";
    } else if (action === "expand") {
      stats.expanded += 1;
      activeTreePath = ensureTreePath(currentPath, nodeId === graph.goal, Number(step.path_cost || currentCost));
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "active";
      }
      searchStatus = "searching";
    } else if (action === "consider_edge") {
      activeTreePath = ensureTreePath(currentPath, false, Number(step.path_cost || currentCost));
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      if (consideredEdge) {
        exploredEdgeIds.add(edgeId(consideredEdge[0], consideredEdge[1]));
      }
      searchStatus = "considering";
    } else if (action === "relax") {
      stats.relaxed += 1;
      activeTreePath = ensureTreePath(currentPath, nodeId === graph.goal, Number(step.path_cost || currentCost));
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      if (parent && nodeId) {
        exploredEdgeIds.add(edgeId(parent, nodeId));
      }
      if (nodeId && !visitedOrder.includes(nodeId)) {
        visitedOrder.push(nodeId);
      }
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "queued";
      }
      searchStatus = "searching";
    } else if (action === "found") {
      finalPath = clone(result.path || currentPath);
      bestPath = clone(finalPath);
      activeTreePath = ensureTreePath(finalPath, true, Number(result.best_cost || currentCost));
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      bestTreePath = clone(activeTreePath);
      finalTreePath = clone(activeTreePath);
      finalTreePath.forEach((treeId) => {
        if (treeNodes.get(treeId)) {
          treeNodes.get(treeId).status = "final";
        }
      });
      searchStatus = "goal found";
    } else if (action === "fail") {
      currentPath = [];
      activeTreePath = [];
      currentTreeId = null;
      consideredEdge = null;
      searchStatus = "no path";
    }

    rawSnapshots.push({
      event_type: action,
      label:
        action === "start"
          ? "Start A*"
          : action === "expand"
            ? `Expand ${nodeId}`
            : action === "consider_edge"
              ? `Consider ${consideredEdge ? `${consideredEdge[0]} -> ${consideredEdge[1]}` : "edge"}`
              : action === "relax"
                ? `Relax ${nodeId}`
                : action === "found"
                  ? "Goal found"
                  : "No path found",
      annotation:
        action === "start"
          ? "The weighted graph is ready. A* starts at the start node."
          : action === "expand"
            ? `A* expands ${nodeId} because it has the lowest f-score on the frontier.`
            : action === "consider_edge"
              ? "A* checks whether this edge improves the best known path cost to its neighbour."
              : action === "relax"
                ? `The route to ${nodeId} improves, so A* updates its frontier priority using g + h.`
                : action === "found"
                  ? "A* has removed the goal from the frontier, so the highlighted path is optimal."
                  : "A* has exhausted the frontier without reaching the goal.",
      teaching_note:
        action === "found"
          ? "With this straight-line heuristic, A* still guarantees an optimal path."
          : "A* balances path cost so far with the geometric heuristic distance to the goal.",
      snapshot: snapshot(),
    });
  });

  const laidOutNodes = layoutTreeNodes(visibleTreeIds.map((treeId) => treeNodes.get(treeId)));
  const layoutById = new Map(laidOutNodes.map((node) => [node.tree_id, node]));

  const initialState = blankGraphAStarTrace(graph).initial_state;
  initialState.example_title = "Live Python weighted graph";
  initialState.example_subtitle = "Trace returned by your local Python A* backend.";
  initialState.tree.nodes = initialState.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);

  const steps = rawSnapshots.map((entry, index) => {
    const snapshot = clone(entry.snapshot);
    snapshot.tree.nodes = snapshot.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);
    return {
      index,
      event_type: entry.event_type,
      label: entry.label,
      annotation: entry.annotation,
      teaching_note: entry.teaching_note,
      state_patch: snapshot,
    };
  });

  return {
    app_type: "graph_astar",
    initial_state: initialState,
    steps,
    summary: { step_count: steps.length, result: result.status || "found" },
  };
}

function buildSearchTraceFromBackend(graph, result) {
  if (
    !Array.isArray(result.trace) ||
    !Array.isArray(result.path) ||
    !Array.isArray(result.visited_order)
  ) {
    throw new Error("Solver returned invalid data.");
  }

  const rawSnapshots = [];
  const treeNodes = new Map();
  const visibleTreeIds = [];
  const treeIdByRoute = new Map();
  const exploredEdgeIds = new Set();
  let currentTreeId = "t0";
  let currentPath = [graph.start];
  let bestPath = [];
  let finalPath = [];
  let activeTreePath = ["t0"];
  let bestTreePath = [];
  let finalTreePath = [];
  let currentCost = 0;
  let bestCost = null;
  let consideredEdge = null;
  let finished = false;
  const stats = { expanded: 0, pruned: 0, solutions_found: 0, backtracks: 0 };

  const root = {
    tree_id: "t0",
    graph_node: graph.start,
    parent: null,
    depth: 0,
    path_cost: 0,
    status: "active",
    order: 0,
    x: 0.5,
    y: 0.12,
    terminal: false,
  };
  treeNodes.set("t0", root);
  visibleTreeIds.push("t0");
  treeIdByRoute.set(routeKey([graph.start]), "t0");

  function ensureTreePath(route) {
    const ids = [];
    route.forEach((_, index) => {
      const treeId = treeIdByRoute.get(routeKey(route.slice(0, index + 1)));
      if (treeId) ids.push(treeId);
    });
    return ids;
  }

  function snapshot() {
    return {
      tree: {
        nodes: visibleTreeIds.map((treeId) => clone(treeNodes.get(treeId))),
      },
      search: {
        active_tree_node: currentTreeId,
        active_tree_path: clone(activeTreePath),
        best_tree_path: clone(bestTreePath),
        final_tree_path: clone(finalTreePath),
        current_graph_path: clone(currentPath),
        best_graph_path: clone(bestPath),
        final_graph_path: clone(finalPath),
        explored_graph_edges: Array.from(exploredEdgeIds).map((id) => id.split("--")),
        considered_edge: consideredEdge ? clone(consideredEdge) : null,
        current_cost: currentCost,
        best_cost: bestCost,
        finished,
        status: finished ? "finished" : "searching",
      },
      stats: clone(stats),
    };
  }

  result.trace.forEach((step) => {
    const action = step.action;
    const nodeId = typeof step.node === "string" ? step.node : null;
    const parent = typeof step.parent === "string" ? step.parent : null;
    const depth = Number(step.depth || 0);
    const pathCost = Number(step.path_cost || 0);
    currentPath = clone(step.current_path || []);
    currentCost = Number(step.current_cost || 0);
    bestPath = clone(step.best_path || []);
    bestCost = step.best_cost === null || step.best_cost === undefined ? null : Number(step.best_cost);
    consideredEdge = Array.isArray(step.considered_edge) ? clone(step.considered_edge) : null;

    if (action === "start") {
      activeTreePath = ["t0"];
      currentTreeId = "t0";
      treeNodes.get("t0").status = "active";
    } else if (action === "expand") {
      stats.expanded += 1;
      const treeId = treeIdByRoute.get(routeKey(currentPath)) || currentTreeId;
      if (treeNodes.get(treeId)) {
        treeNodes.get(treeId).status = "active";
      }
      currentTreeId = treeId;
      activeTreePath = ensureTreePath(currentPath);
    } else if (action === "consider_edge") {
      activeTreePath = ensureTreePath(currentPath);
      currentTreeId = activeTreePath[activeTreePath.length - 1] || "t0";
    } else if (action === "descend") {
      const parentRoute = currentPath.slice(0, -1);
      const parentId = treeIdByRoute.get(routeKey(parentRoute)) || currentTreeId;
      const treeId = `t${visibleTreeIds.length}`;
      treeNodes.set(treeId, {
        tree_id: treeId,
        graph_node: nodeId,
        parent: parentId,
        depth,
        path_cost: pathCost,
        status: "active",
        order: visibleTreeIds.length,
        terminal: nodeId === graph.goal,
      });
      visibleTreeIds.push(treeId);
      treeIdByRoute.set(routeKey(currentPath), treeId);
      if (parent && nodeId) exploredEdgeIds.add(edgeId(parent, nodeId));
      if (treeNodes.get(parentId)) {
        treeNodes.get(parentId).status = "expanded";
      }
      activeTreePath = ensureTreePath(currentPath);
      currentTreeId = treeId;
    } else if (action === "prune") {
      stats.pruned += 1;
      const parentId = treeIdByRoute.get(routeKey(currentPath)) || currentTreeId;
      const treeId = `t${visibleTreeIds.length}`;
      const prunedRoute = currentPath.concat(nodeId ? [nodeId] : []);
      treeNodes.set(treeId, {
        tree_id: treeId,
        graph_node: nodeId,
        parent: parentId,
        depth,
        path_cost: pathCost,
        status: "pruned",
        order: visibleTreeIds.length,
        terminal: nodeId === graph.goal,
      });
      visibleTreeIds.push(treeId);
      treeIdByRoute.set(routeKey(prunedRoute), treeId);
      activeTreePath = ensureTreePath(currentPath);
      currentTreeId = activeTreePath[activeTreePath.length - 1] || parentId || "t0";
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "active";
      }
    } else if (action === "solution_found") {
      stats.solutions_found += 1;
      const treeId = treeIdByRoute.get(routeKey(currentPath)) || currentTreeId;
      if (treeNodes.get(treeId)) {
        treeNodes.get(treeId).status = "goal";
      }
      activeTreePath = ensureTreePath(currentPath);
      currentTreeId = treeId;
    } else if (action === "best_updated") {
      bestTreePath = ensureTreePath(bestPath);
      bestTreePath.forEach((treeId) => {
        if (treeNodes.get(treeId)) {
          treeNodes.get(treeId).status = "best";
        }
      });
      activeTreePath = ensureTreePath(currentPath);
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
    } else if (action === "backtrack") {
      stats.backtracks += 1;
      const backtrackedTreeId = currentTreeIdByPath.get(nodeId);
      if (backtrackedTreeId && treeNodes.get(backtrackedTreeId)) {
        treeNodes.get(backtrackedTreeId).status = "backtracked";
      }
      activeTreePath = ensureTreePath(currentPath);
      currentTreeId = activeTreePath[activeTreePath.length - 1] || "t0";
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "active";
      }
    } else if (action === "finished") {
      finished = true;
      finalPath = clone(result.path || bestPath);
      finalTreePath = ensureTreePath(finalPath);
      finalTreePath.forEach((treeId) => {
        if (treeNodes.get(treeId)) {
          treeNodes.get(treeId).status = "final";
        }
      });
      activeTreePath = [];
      currentTreeId = null;
      currentPath = [];
      currentCost = 0;
      consideredEdge = null;
    }

    rawSnapshots.push({
      event_type: action,
      label:
        action === "start"
          ? "Start branch-and-bound"
          : action === "expand"
            ? `Expand ${nodeId}`
            : action === "consider_edge"
              ? `Consider ${consideredEdge ? `${consideredEdge[0]} -> ${consideredEdge[1]}` : "edge"}`
              : action === "descend"
                ? `Descend to ${nodeId}`
                : action === "prune"
                  ? `Prune ${nodeId}`
                  : action === "backtrack"
                    ? `Backtrack from ${nodeId}`
                    : action === "solution_found"
                      ? "Found complete path"
                      : action === "best_updated"
                        ? "Update best solution"
                        : "Search finished",
      annotation:
        action === "start"
          ? "The weighted graph is ready. Branch-and-bound starts at the start node."
          : action === "expand"
            ? `Expand ${nodeId} in deterministic neighbour order.`
            : action === "consider_edge"
              ? `Check whether the next edge can still improve the current best solution.`
              : action === "descend"
                ? `DFS commits to ${nodeId} and continues deeper into the weighted graph.`
                : action === "prune"
                  ? `This branch cannot improve the current best solution, so it is pruned.`
                  : action === "backtrack"
                    ? `The branch below ${nodeId} is complete, so DFS returns to its parent.`
                    : action === "solution_found"
                      ? "A complete path to the goal has been found."
                      : action === "best_updated"
                        ? "This complete path is the best solution seen so far."
                        : "The optimal path is now highlighted.",
      teaching_note:
        action === "finished"
          ? "Optimality comes from exhaustive DFS plus safe best-cost pruning."
          : "The tree shows search history, while the graph view shows the original weighted problem.",
      snapshot: snapshot(),
    });
  });

  const laidOutNodes = layoutTreeNodes(visibleTreeIds.map((treeId) => treeNodes.get(treeId)));
  const layoutById = new Map(laidOutNodes.map((node) => [node.tree_id, node]));

  const initialState = blankSearchTrace(graph).initial_state;
  initialState.example_title = "Live Python weighted graph";
  initialState.example_subtitle = "Trace returned by your local Python branch-and-bound solver.";
  initialState.tree.nodes = initialState.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);

  const steps = rawSnapshots.map((entry, index) => {
    const snapshot = clone(entry.snapshot);
    snapshot.tree.nodes = snapshot.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);
    return {
      index,
      event_type: entry.event_type,
      label: entry.label,
      annotation: entry.annotation,
      teaching_note: entry.teaching_note,
      state_patch: snapshot,
    };
  });

  return {
    app_type: "search",
    initial_state: initialState,
    steps,
    summary: { step_count: steps.length, result: result.status || "found" },
  };
}

function buildLogicTraceFromBackend(problem, result) {
  if (!Array.isArray(result.trace)) {
    throw new Error("Solver returned invalid logic trace data.");
  }

  const treeNodes = new Map();
  const treeIds = [];
  const pathById = new Map();
  const nodeStateById = new Map();
  const stats = { decisions: 0, forced_assignments: 0, contradictions: 0, backtracks: 0 };
  let activeTreeNode = "t0";
  let activeTreePath = ["t0"];
  let finalTreePath = [];
  let assignment = {};
  let assignmentItems = [];
  let status = "ready";
  let finalResult = result.status || null;

  treeNodes.set("t0", {
    tree_id: "t0",
    graph_node: "start",
    assignment_text: "No assignments",
    parent: null,
    depth: 0,
    path_cost: 0,
    status: "active",
    order: 0,
    x: 0.5,
    y: 0.12,
    terminal: false,
    reason: "start",
  });
  treeIds.push("t0");
  pathById.set("t0", ["t0"]);

  function clauseSnapshot(currentAssignment) {
    const clauses = evaluateLogicClauses(problem.clauses, currentAssignment);
    return {
      clauses,
      summary: logicSummary(clauses, currentAssignment, problem.variables || []),
    };
  }

  function syncAssignmentItems(currentAssignment, treePath) {
    const items = [];
    treePath.slice(1).forEach((treeId) => {
      const node = treeNodes.get(treeId);
      if (!node || !node.graph_node.includes("=")) return;
      const [variable, rawValue] = node.graph_node.split("=").map((part) => part.trim());
      items.push({
        variable,
        value: rawValue === "T",
        reason: node.reason,
        clause_index: node.clause_index ?? null,
        text: `${variable} = ${rawValue}`,
      });
    });
    assignmentItems = items;
    assignment = clone(currentAssignment);
  }

  function snapshot() {
    const logic = clauseSnapshot(assignment);
    return {
      tree: {
        nodes: treeIds.map((treeId) => clone(treeNodes.get(treeId))),
      },
      search: {
        active_tree_node: activeTreeNode,
        active_tree_path: clone(activeTreePath),
        best_tree_path: [],
        final_tree_path: clone(finalTreePath),
        finished: status === "finished" || status === "satisfiable" || status === "unsatisfiable" || status === "entailed" || status === "not entailed",
        status,
        result: finalResult,
      },
      logic: {
        mode: problem.mode,
        variables: clone(problem.variables || []),
        clauses: logic.clauses,
        summary: logic.summary,
        assignment: clone(assignmentItems),
        kb_formulas: clone(problem.kb_formulas || []),
        query: problem.query || null,
        entailment_target: problem.entailment_target || null,
        original_input: clone(problem.original_input || []),
      },
      stats: clone(stats),
    };
  }

  const rawSnapshots = [];
  result.trace.forEach((step) => {
    const nodeId = step.node_id;
    const parentId = step.parent_id;
    const variable = step.variable;
    const reason = step.reason;
    const value = step.value;
    const currentAssignment = clone(step.assignment || {});

    if (step.action === "start") {
      activeTreeNode = "t0";
      activeTreePath = ["t0"];
      syncAssignmentItems({}, activeTreePath);
      status = "searching";
      treeNodes.get("t0").status = "active";
    } else if (step.action === "choose_variable") {
      activeTreeNode = nodeId || activeTreeNode;
      activeTreePath = pathById.get(activeTreeNode) || activeTreePath;
      syncAssignmentItems(currentAssignment, activeTreePath);
      status = "branching";
    } else if (step.action === "assign") {
      if (!nodeId || !parentId || !variable || typeof value !== "boolean") {
        throw new Error("Assign events must include node_id, parent_id, variable, and value.");
      }
      const valueText = value ? "T" : "F";
      treeNodes.set(nodeId, {
        tree_id: nodeId,
        graph_node: `${variable} = ${valueText}`,
        assignment_text: Object.entries(currentAssignment)
          .map(([name, assignmentValue]) => `${name} = ${assignmentValue ? "T" : "F"}`)
          .join(", "),
        parent: parentId,
        depth: Object.keys(currentAssignment).length,
        path_cost: 0,
        status: reason === "decision" ? "active" : "forced",
        order: treeIds.length,
        x: 0.5,
        y: 0.12,
        terminal: false,
        reason: reason || "decision",
        clause_index: step.clause_index ?? null,
      });
      treeIds.push(nodeId);
      const parentPath = pathById.get(parentId) || ["t0"];
      pathById.set(nodeId, parentPath.concat(nodeId));
      activeTreeNode = nodeId;
      activeTreePath = pathById.get(nodeId);
      syncAssignmentItems(currentAssignment, activeTreePath);
      if (reason === "decision") {
        stats.decisions += 1;
        if (treeNodes.get(parentId)) treeNodes.get(parentId).status = "branched";
        status = "branching";
      } else {
        stats.forced_assignments += 1;
        status = "propagating";
      }
    } else if (step.action === "contradiction") {
      if (nodeId && treeNodes.get(nodeId)) {
        treeNodes.get(nodeId).status = "contradiction";
        activeTreeNode = nodeId;
        activeTreePath = pathById.get(nodeId) || activeTreePath;
      }
      syncAssignmentItems(currentAssignment, activeTreePath);
      stats.contradictions += 1;
      status = "contradiction";
    } else if (step.action === "backtrack") {
      if (nodeId) {
        activeTreeNode = nodeId;
        activeTreePath = pathById.get(nodeId) || ["t0"];
      }
      syncAssignmentItems(currentAssignment, activeTreePath);
      if (activeTreeNode && treeNodes.get(activeTreeNode)) {
        treeNodes.get(activeTreeNode).status = "active";
      }
      stats.backtracks += 1;
      status = "backtracking";
    } else if (step.action === "solution_found") {
      if (nodeId && treeNodes.get(nodeId)) {
        treeNodes.get(nodeId).status = "solution";
        activeTreeNode = nodeId;
        activeTreePath = pathById.get(nodeId) || activeTreePath;
      }
      syncAssignmentItems(currentAssignment, activeTreePath);
      finalTreePath = clone(activeTreePath);
      status = result.mode === "sat" ? "satisfiable" : "not entailed";
    } else if (step.action === "finished") {
      syncAssignmentItems(currentAssignment, activeTreePath);
      if (result.status === "satisfiable" || result.status === "not_entailed") {
        finalTreePath = clone(activeTreePath);
      }
      status =
        result.status === "not_entailed"
          ? "not entailed"
          : result.status === "unsatisfiable"
            ? "unsatisfiable"
            : result.status === "entailed"
              ? "entailed"
              : result.status;
    }

    rawSnapshots.push({
      event_type: step.action,
      label:
        step.action === "start"
          ? "Start DPLL"
          : step.action === "choose_variable"
            ? `Choose ${variable}`
            : step.action === "assign"
              ? `${reason === "decision" ? "Assign" : "Force"} ${variable} = ${value ? "T" : "F"}`
              : step.action === "contradiction"
                ? "Contradiction"
                : step.action === "backtrack"
                  ? "Backtrack"
                  : step.action === "solution_found"
                    ? "Solution found"
                    : "Finished",
      annotation:
        step.action === "start"
          ? "The clause list is ready for a DPLL replay."
          : step.action === "choose_variable"
            ? `No forced move remains, so DPLL branches on ${variable}.`
            : step.action === "assign"
              ? reason === "decision"
                ? `Choose ${variable} = ${value ? "true" : "false"} as the next branch.`
                : reason === "unit"
                  ? `A unit clause forces ${variable} = ${value ? "true" : "false"}.`
                  : `A pure literal lets DPLL set ${variable} = ${value ? "true" : "false"}.`
              : step.action === "contradiction"
                ? "One clause is now false, so the current branch fails."
                : step.action === "backtrack"
                  ? "DPLL returns to the previous decision point and tries a different branch."
                  : step.action === "solution_found"
                    ? "All clauses are satisfied under the current assignment."
                    : result.status === "entailed"
                      ? "KB and not query is unsatisfiable, so the query is entailed."
                      : result.status === "not_entailed"
                        ? "KB and not query still has a model, so the query is not entailed."
                        : result.status === "satisfiable"
                          ? "A satisfying assignment has been found."
                          : "Every branch fails, so the CNF is unsatisfiable.",
      teaching_note:
        step.action === "backtrack"
          ? "A failed branch does not end the whole search until every remaining alternative has also failed."
          : "The tree on the left shows the partial assignments; the clauses on the right show why each step happened.",
      snapshot: snapshot(),
    });
  });

  const laidOutNodes = layoutTreeNodes(treeIds.map((treeId) => treeNodes.get(treeId)));
  const layoutById = new Map(laidOutNodes.map((node) => [node.tree_id, node]));
  const initialState = blankLogicTrace(problem).initial_state;
  initialState.example_title = "Live Python DPLL";
  initialState.example_subtitle = "Trace returned by your local Python DPLL solver.";
  initialState.tree.nodes = initialState.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);

  const steps = rawSnapshots.map((entry, index) => {
    const snapshot = clone(entry.snapshot);
    snapshot.tree.nodes = snapshot.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);
    return {
      index,
      event_type: entry.event_type,
      label: entry.label,
      annotation: entry.annotation,
      teaching_note: entry.teaching_note,
      state_patch: snapshot,
    };
  });

  return {
    app_type: "logic",
    initial_state: initialState,
    steps,
    summary: { step_count: steps.length, result: result.status || "ready" },
  };
}

function blankFoundationTrace(data = {}) {
  return {
    app_type: "foundation_models",
    initial_state: {
      example_title: data.example_title || "Foundation Models Demo - Tokenisation Explorer",
      example_subtitle: data.example_subtitle || "Tokenisation replay is ready.",
      algorithm_label: data.algorithm_label || "Foundation Models Demo - Tokenisation Explorer",
      algorithm_note:
        data.algorithm_note ||
        "Tokenisation replay is ready. Load an example or step through learned BPE merges.",
      foundation_models: data.foundation_models || {
        mode: "bpe",
        status: "ready",
        text: "",
        overlay_segments: [],
        tokens: [],
        stats: {
          character_count: 0,
          token_count: 0,
          average_token_length: 0,
          context_window: 64,
          context_used: 0,
          context_remaining: 64,
          context_usage: "0 / 64",
        },
        comparison: [],
        bpe: {
          merge_step: 0,
          requested_merges: 0,
          learned_merges: [],
          pair_counts: [],
          segmented_corpus: [],
        },
      },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankUncertaintyTrace(problem = {}, data = {}) {
  return {
    app_type: "uncertainty",
    initial_state: {
      example_title: data.example_title || problem.title || "Reasoning with Uncertainty - Belief-State Explorer",
      example_subtitle: data.example_subtitle || problem.subtitle || "Bayes-filter replay is ready.",
      algorithm_label: data.algorithm_label || "Bayes filter",
      algorithm_note:
        data.algorithm_note ||
        "A Bayes filter predicts with the transition model, then corrects with the observation model.",
      uncertainty_problem: clone(problem || {}),
      uncertainty: data.uncertainty || {
        step_index: 0,
        total_steps: 0,
        rooms: problem.rooms || [],
        connections: problem.connections || [],
        current_action: null,
        current_observation: null,
        current_true_location: problem.initial_true_location || null,
        prior_belief: clone(problem.initial_belief || {}),
        predicted_belief: clone(problem.initial_belief || {}),
        observation_likelihoods: Object.fromEntries(
          Object.keys(problem.initial_belief || {}).map((key) => [key, 1])
        ),
        unnormalised_posterior: clone(problem.initial_belief || {}),
        posterior_belief: clone(problem.initial_belief || {}),
        belief_rows: [],
        transition_rows: [],
        history: [],
        most_likely_location: null,
        most_likely_label: "",
        most_likely_probability: 0,
        normalisation_constant: 1,
      },
      search: data.search || {
        status: "ready",
        result: "ready",
        finished: false,
      },
      stats: data.stats || {
        step_index: 0,
        max_belief: 0,
        entropy: 0,
        normalisation_constant: 1,
      },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function activeTraceContext() {
  const blankTrace = isCsp()
    ? blankCspTrace(state.session.data.csp_problem, state.session.data)
    : isDeliveryCsp()
    ? blankDeliveryCspTrace(state.session.data.delivery_problem, state.session.data)
    : isUncertainty()
    ? blankUncertaintyTrace(state.session.data.uncertainty_problem, state.session.data)
    : isStrips()
    ? blankStripsTrace(state.session.data.strips_problem, state.session.data)
    : isLogic()
    ? blankLogicTrace(state.session.data.logic_problem || state.session.data.problem || {
        mode: state.session.data.problem_mode || "sat",
        variables: state.session.data.logic?.variables || [],
        clauses: (state.session.data.logic?.clauses || []).map((clause) =>
          clause.literals ? clause.literals.map((literal) => literal.raw) : []
        ),
        kb_formulas: state.session.data.logic?.kb_formulas || [],
        query: state.session.data.logic?.query || null,
        entailment_target: state.session.data.logic?.entailment_target || null,
        original_input: state.session.data.logic?.original_input || [],
        title: state.session.data.example_title || "Visual DPLL",
        subtitle: state.session.data.example_subtitle || "",
      })
    : isFoundationModels()
    ? blankFoundationTrace(state.session.data)
    : isLabyrinth()
    ? blankLabyrinthTrace(state.session.data.labyrinth)
    : isWeightedSearch()
      ? blankSearchTrace(state.session.data.graph)
      : isGraphAStar()
        ? blankGraphAStarTrace(state.session.data.graph)
      : isGraphGbfs()
        ? blankGraphGbfsTrace(state.session.data.graph)
      : isGraphUcs()
        ? blankGraphUcsTrace(state.session.data.graph)
      : isGraphBfs()
        ? blankGraphBfsTrace(state.session.data.graph)
        : blankGraphDfsTrace(state.session.data.graph);
  const blankSnapshots = buildSnapshots(blankTrace);

  if (state.player.mode === "live") {
    if (state.player.liveTrace) {
      return { trace: state.player.liveTrace, snapshots: state.player.liveSnapshots };
    }
    return { trace: blankTrace, snapshots: blankSnapshots };
  }

  if (state.serverTrace) {
    return { trace: state.serverTrace, snapshots: state.serverSnapshots };
  }
  return { trace: blankTrace, snapshots: blankSnapshots };
}

function currentTrace() {
  return activeTraceContext().trace;
}

function currentData() {
  const { snapshots } = activeTraceContext();
  const index = Math.max(0, Math.min(state.player.stepIndex, snapshots.length - 1));
  return snapshots[index] || {};
}

function currentStep() {
  const trace = currentTrace();
  if (!trace.steps?.length || state.player.stepIndex === 0) {
    const data = currentData();
    return {
      event_type: "initialise",
      label: "Initial state",
      annotation: data.algorithm_note || "The replay is ready.",
      teaching_note: "Step forward or press play to start the replay.",
    };
  }
  return trace.steps[state.player.stepIndex - 1];
}

function maxStepCount() {
  return currentTrace().steps?.length || 0;
}

function statusLabel(data, step) {
  if (isFoundationModels()) {
    return data.foundation_models?.status || "ready";
  }
  if (isUncertainty()) {
    return data.search?.status || "ready";
  }
  if (isCspFamily()) {
    return data.search?.status || "ready";
  }
  if (isStrips()) {
    return data.search?.status || "ready";
  }
  if (isLogic()) {
    return data.search?.status || data.search?.result || "ready";
  }
  if (isLabyrinth() || isGraphReachability()) {
    return data.search?.status || "ready";
  }
  if (isWeightedGraphSearch() && data.search?.status) {
    return data.search.status;
  }
  if (data.search?.finished) return "finished";
  if (step.event_type === "backtrack") return "backtracking";
  return "running";
}

function renderPanelCopy(data) {
  if (isFoundationModels()) {
    $("left-panel-title").textContent = "Tokenisation State";
    $("left-panel-subtitle").textContent =
      "Token lists, token counts, comparisons, and the BPE learning trace stay aligned with the visible text on the right.";
    $("right-panel-title").textContent = "Text View";
    $("right-panel-subtitle").textContent =
      "Edit or load a text, then inspect the same string with token boundaries drawn directly onto the visible input.";
  } else if (isCsp()) {
    $("left-panel-title").textContent = "CSP State";
    $("left-panel-subtitle").textContent =
      "Variables, domains, and the decision trace stay aligned with the map colouring on the right.";
    $("right-panel-title").textContent = "Map View";
    $("right-panel-subtitle").textContent =
      "The map shows assigned colours directly and keeps the remaining candidate colours visible for every unassigned region.";
  } else if (isDeliveryCsp()) {
    $("left-panel-title").textContent = "CSP State";
    $("left-panel-subtitle").textContent =
      "Deliveries, remaining slot-room options, and the decision trace stay aligned with the schedule board on the right.";
    $("right-panel-title").textContent = "Schedule Board";
    $("right-panel-subtitle").textContent =
      "Each cell is a room and time slot. Assigned deliveries fill a cell, while candidate badges show which unassigned deliveries can still use it.";
  } else if (isUncertainty()) {
    $("left-panel-title").textContent = "Belief State";
    $("left-panel-subtitle").textContent =
      "Prior, prediction, likelihoods, and posterior stay aligned so students can see the full Bayes-filter update.";
    $("right-panel-title").textContent = "Office World";
    $("right-panel-subtitle").textContent =
      "The office map stays fixed while the belief heat and current sensor reading show the difference between hidden truth and internal belief.";
  } else if (isStrips()) {
    $("left-panel-title").textContent = "Planning State";
    $("left-panel-subtitle").textContent =
      "Predicates, applicable actions, and the grounded plan stay aligned with the rendered office world.";
    $("right-panel-title").textContent = "Office World";
    $("right-panel-subtitle").textContent =
      "The robot, parcel, keycard, and lab door are drawn directly from the symbolic state rather than controlled separately.";
  } else if (isLogic()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Each node is a partial assignment, so the tree shows where DPLL branched and where literals were forced.";
    $("right-panel-title").textContent = data.problem_mode === "entailment" ? "Knowledge Base and CNF" : "Clause State";
    $("right-panel-subtitle").textContent =
      data.problem_mode === "entailment"
        ? "The original knowledge base stays visible while the CNF clause list shows why KB and not query succeed or fail."
        : "The clause list shows which clauses are satisfied, unresolved, unit, or contradicted under the current assignment.";
  } else if (isLabyrinth()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "The tree grows in DFS order and keeps backtracked branches visible.";
    $("right-panel-title").textContent = "Labyrinth";
    $("right-panel-subtitle").textContent = "The maze view shows the current route, dead ends, and the final discovered path.";
  } else if (isGraphAStar()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Search states appear here as A* balances the path cost so far with the straight-line heuristic to the goal.";
    $("right-panel-title").textContent = "Weighted Spatial Graph";
    $("right-panel-subtitle").textContent = "The weighted graph stays fixed while the replay highlights the current frontier route and the final optimal path.";
  } else if (isGraphGbfs()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Search states appear here as greedy best-first search follows the most promising-looking frontier node.";
    $("right-panel-title").textContent = "Weighted Spatial Graph";
    $("right-panel-subtitle").textContent = "The weighted graph stays fixed while the replay highlights the heuristic-driven route and the final path found.";
  } else if (isGraphUcs()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Search states appear here as uniform-cost search expands the cheapest frontier path first.";
    $("right-panel-title").textContent = "Weighted Spatial Graph";
    $("right-panel-subtitle").textContent = "The weighted graph stays fixed while the replay highlights the active frontier route and the final optimal path.";
  } else if (isGraphBfs()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "The tree grows in BFS order and shows how the frontier expands level by level.";
    $("right-panel-title").textContent = "Spatial Graph";
    $("right-panel-subtitle").textContent = "The graph view shows the highlighted route, explored edges, visited nodes, and the final discovered path.";
  } else if (isGraphDfs()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "The tree grows in DFS order and keeps backtracked branches visible.";
    $("right-panel-title").textContent = "Spatial Graph";
    $("right-panel-subtitle").textContent = "The graph view shows the current route, explored edges, dead ends, and the final discovered path.";
  } else {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Search states appear here as depth-first branch-and-bound explores and prunes branches.";
    $("right-panel-title").textContent = "Geometric Graph";
    $("right-panel-subtitle").textContent = "The weighted graph stays fixed while the replay highlights the active branch, best path, and final optimal path.";
  }
}

function renderMetrics(data) {
  if (isFoundationModels()) {
    const stats = data.foundation_models?.stats || {};
    $("metric-1-label").textContent = "Characters";
    $("metric-1-value").textContent = String(stats.character_count || 0);
    $("metric-2-label").textContent = "Tokens";
    $("metric-2-value").textContent = String(stats.token_count || 0);
    $("metric-3-label").textContent = "Avg token length";
    $("metric-3-value").textContent = String(stats.average_token_length ?? 0);
    $("metric-4-label").textContent = "Context usage";
    $("metric-4-value").textContent = stats.context_usage || "0 / 64";
    return;
  }
  if (isCsp()) {
    const assigned = Object.keys(data.csp?.assignments || {}).length;
    const total = data.csp?.variables?.length || 0;
    $("metric-1-label").textContent = "Assigned variables";
    $("metric-1-value").textContent = `${assigned} / ${total}`;
    $("metric-2-label").textContent = "Pruned values";
    $("metric-2-value").textContent = String(data.stats?.prunes || 0);
    $("metric-3-label").textContent = "Backtracks";
    $("metric-3-value").textContent = String(data.stats?.backtracks || 0);
    $("metric-4-label").textContent = "Wipe-outs";
    $("metric-4-value").textContent = String(data.stats?.wipeouts || 0);
    return;
  }
  if (isDeliveryCsp()) {
    const assigned = Object.keys(data.delivery_csp?.assignments || {}).length;
    const total = data.delivery_csp?.variables?.length || 0;
    $("metric-1-label").textContent = "Assigned deliveries";
    $("metric-1-value").textContent = `${assigned} / ${total}`;
    $("metric-2-label").textContent = "Pruned values";
    $("metric-2-value").textContent = String(data.stats?.prunes || 0);
    $("metric-3-label").textContent = "Backtracks";
    $("metric-3-value").textContent = String(data.stats?.backtracks || 0);
    $("metric-4-label").textContent = "Wipe-outs";
    $("metric-4-value").textContent = String(data.stats?.wipeouts || 0);
    return;
  }
  if (isUncertainty()) {
    const uncertainty = data.uncertainty || {};
    $("metric-1-label").textContent = "Most likely room";
    $("metric-1-value").textContent = uncertainty.most_likely_label || "none";
    $("metric-2-label").textContent = "Confidence";
    $("metric-2-value").textContent = `${Math.round((uncertainty.most_likely_probability || 0) * 100)}%`;
    $("metric-3-label").textContent = "Entropy";
    $("metric-3-value").textContent = formatNumber(data.stats?.entropy, 2);
    $("metric-4-label").textContent = "Normaliser";
    $("metric-4-value").textContent = formatNumber(data.stats?.normalisation_constant, 3);
    return;
  }
  if (isStrips()) {
    const planLength = data.planning?.plan?.length || 0;
    $("metric-1-label").textContent = "Plan step";
    $("metric-1-value").textContent = `${data.planning?.plan_index || 0} / ${planLength}`;
    $("metric-2-label").textContent = "Applicable actions";
    $("metric-2-value").textContent = String(data.planning?.applicable_actions?.length || 0);
    $("metric-3-label").textContent = "Expanded states";
    $("metric-3-value").textContent = String(data.stats?.expanded_states || 0);
    $("metric-4-label").textContent = "Frontier peak";
    $("metric-4-value").textContent = String(data.stats?.frontier_peak || 0);
    return;
  }
  if (isLogic()) {
    $("metric-1-label").textContent = "Assigned variables";
    $("metric-1-value").textContent = `${data.logic?.summary?.assigned_variables || 0} / ${data.logic?.summary?.total_variables || 0}`;
    $("metric-2-label").textContent = "Unit clauses";
    $("metric-2-value").textContent = String(data.logic?.summary?.unit || 0);
    $("metric-3-label").textContent = "Forced assignments";
    $("metric-3-value").textContent = String(data.stats?.forced_assignments || 0);
    $("metric-4-label").textContent = "Backtracks";
    $("metric-4-value").textContent = String(data.stats?.backtracks || 0);
    return;
  }
  if (isLabyrinth()) {
    $("metric-1-label").textContent = "Explored cells";
    $("metric-1-value").textContent = String(data.search?.explored_count || 0);
    $("metric-2-label").textContent = "Current depth";
    $("metric-2-value").textContent = String(data.search?.current_depth || 0);
    $("metric-3-label").textContent = "Status";
    $("metric-3-value").textContent = data.search?.status || "searching";
    $("metric-4-label").textContent = "Seed";
    $("metric-4-value").textContent = String(data.labyrinth?.seed ?? "none");
    return;
  }

  if (isGraphReachability()) {
    $("metric-1-label").textContent = "Explored nodes";
    $("metric-1-value").textContent = String(data.search?.explored_count || 0);
    $("metric-2-label").textContent = "Current depth";
    $("metric-2-value").textContent = String(data.search?.current_depth || 0);
    $("metric-3-label").textContent = "Status";
    $("metric-3-value").textContent = data.search?.status || "searching";
    $("metric-4-label").textContent = "Seed";
    $("metric-4-value").textContent = String(data.graph?.seed ?? "none");
    return;
  }

  if (isGraphAStar()) {
    $("metric-1-label").textContent = "Current heuristic";
    $("metric-1-value").textContent = formatNumber(data.search?.current_heuristic);
    $("metric-2-label").textContent = "Current priority";
    $("metric-2-value").textContent = formatNumber(data.search?.current_priority);
    $("metric-3-label").textContent = "Expanded nodes";
    $("metric-3-value").textContent = String(data.stats?.expanded || 0);
    $("metric-4-label").textContent = "Best cost";
    $("metric-4-value").textContent = formatNumber(data.search?.best_cost);
    return;
  }

  if (isGraphGbfs()) {
    $("metric-1-label").textContent = "Current heuristic";
    $("metric-1-value").textContent = formatNumber(data.search?.current_heuristic);
    $("metric-2-label").textContent = "Current path cost";
    $("metric-2-value").textContent = formatNumber(data.search?.current_cost);
    $("metric-3-label").textContent = "Expanded nodes";
    $("metric-3-value").textContent = String(data.stats?.expanded || 0);
    $("metric-4-label").textContent = "Queued nodes";
    $("metric-4-value").textContent = String(data.stats?.enqueued || 0);
    return;
  }

  if (isGraphUcs()) {
    $("metric-1-label").textContent = "Current path cost";
    $("metric-1-value").textContent = formatNumber(data.search?.current_cost);
    $("metric-2-label").textContent = "Best cost";
    $("metric-2-value").textContent = formatNumber(data.search?.best_cost);
    $("metric-3-label").textContent = "Expanded nodes";
    $("metric-3-value").textContent = String(data.stats?.expanded || 0);
    $("metric-4-label").textContent = "Relaxations";
    $("metric-4-value").textContent = String(data.stats?.relaxed || 0);
    return;
  }

  $("metric-1-label").textContent = "Current path cost";
  $("metric-1-value").textContent = formatNumber(data.search?.current_cost);
  $("metric-2-label").textContent = "Best cost";
  $("metric-2-value").textContent = formatNumber(data.search?.best_cost);
  $("metric-3-label").textContent = "Solutions found";
  $("metric-3-value").textContent = String(data.stats?.solutions_found || 0);
  $("metric-4-label").textContent = "Pruned branches";
  $("metric-4-value").textContent = String(data.stats?.pruned || 0);
}

function cspColourValue(problem, colour) {
  return problem?.colour_values?.[colour] || "#d1c6b8";
}

function renderCspTree(container, data) {
  const nodes = data.tree?.nodes || [];
  if (!nodes.length) {
    container.textContent = "The search tree will appear here as assignments are tried.";
    return;
  }

  const svg = $svgNode("svg", {
    class: "csp-tree-svg",
    viewBox: "0 0 1000 320",
    role: "img",
    "aria-label": "CSP search tree",
  });
  const nodeMap = new Map(nodes.map((node) => [node.tree_id, node]));
  const activePath = new Set(data.search?.active_tree_path || []);
  const finalPath = new Set(data.search?.final_tree_path || []);

  const links = $svgNode("g");
  const cards = $svgNode("g");

  nodes.forEach((node) => {
    if (!node.parent || !nodeMap.has(node.parent)) return;
    const parent = nodeMap.get(node.parent);
    const classes = ["csp-tree-link"];
    if (activePath.has(node.tree_id) && activePath.has(node.parent)) classes.push("active");
    if (finalPath.has(node.tree_id) && finalPath.has(node.parent)) classes.push("final");
    links.appendChild(
      $svgNode("line", {
        class: classes.join(" "),
        x1: parent.x * 1000,
        y1: parent.y * 320,
        x2: node.x * 1000,
        y2: node.y * 320,
      })
    );
  });

  nodes.forEach((node) => {
    const group = $svgNode("g", {
      class: `csp-tree-node ${node.status || ""}`,
      transform: `translate(${node.x * 1000}, ${node.y * 320})`,
    });
    group.appendChild(
      $svgNode("rect", {
        class: "csp-tree-card",
        x: -78,
        y: -30,
        width: 156,
        height: 60,
        rx: 18,
      })
    );
    group.appendChild($svgNode("text", { class: "csp-tree-heading", y: -4 }, node.graph_node));
    group.appendChild(
      $svgNode("text", { class: "csp-tree-subtext", y: 16 }, node.assignment_text || "No assignments")
    );
    cards.appendChild(group);
  });

  svg.append(links, cards);
  container.appendChild(svg);
}

function renderCspPanel(data) {
  const panel = $("csp-panel");
  panel.innerHTML = "";
  const csp = data.csp;
  const problem = data.csp_problem;
  if (!csp || !problem) return;

  const shell = document.createElement("div");
  shell.className = "csp-shell";

  const stateSection = document.createElement("section");
  stateSection.className = "csp-section";
  const stateHeading = document.createElement("h3");
  stateHeading.className = "csp-section-title";
  stateHeading.textContent = "Current CSP state";
  const stateCopy = document.createElement("p");
  stateCopy.className = "csp-copy";
  stateCopy.textContent = `Variables are the regions, domains are the remaining colours, and every edge says neighbouring regions must differ. Current focus: ${csp.focus_variable || "none"}.`;
  stateSection.append(stateHeading, stateCopy);

  const table = document.createElement("table");
  table.className = "csp-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>Variable</th>
        <th>Current domain</th>
        <th>Assigned</th>
        <th>Status</th>
      </tr>
    </thead>
  `;
  const body = document.createElement("tbody");
  (csp.variables || []).forEach((row) => {
    const tr = document.createElement("tr");
    tr.className = row.status || "unchanged";

    const variable = document.createElement("td");
    variable.textContent = row.variable;

    const domain = document.createElement("td");
    const domainList = document.createElement("div");
    domainList.className = "csp-domain-list";
    if ((row.domain || []).length) {
      row.domain.forEach((colour) => {
        const chip = document.createElement("span");
        chip.className = "csp-domain-chip";
        const dot = document.createElement("span");
        dot.className = "csp-colour-dot";
        dot.style.background = cspColourValue(problem, colour);
        chip.append(dot, document.createTextNode(colour));
        domainList.appendChild(chip);
      });
    } else {
      const chip = document.createElement("span");
      chip.className = "csp-domain-chip empty";
      chip.textContent = "empty";
      domainList.appendChild(chip);
    }
    domain.appendChild(domainList);

    const assigned = document.createElement("td");
    assigned.textContent = row.assigned_value || "—";

    const status = document.createElement("td");
    const pill = document.createElement("span");
    pill.className = `csp-status-pill ${row.status || "unchanged"}`;
    pill.textContent = row.status || "unchanged";
    status.appendChild(pill);

    tr.append(variable, domain, assigned, status);
    body.appendChild(tr);
  });
  table.appendChild(body);
  stateSection.appendChild(table);
  shell.appendChild(stateSection);

  const lowerSection = document.createElement("section");
  lowerSection.className = "csp-section";
  const lowerHeading = document.createElement("h3");
  lowerHeading.className = "csp-section-title";
  lowerHeading.textContent = state.view.cspViewMode === "tree" ? "Search tree" : "Decision trace";
  lowerSection.appendChild(lowerHeading);

  if (state.view.cspViewMode === "tree") {
    renderCspTree(lowerSection, data);
  } else {
    const traceList = document.createElement("div");
    traceList.className = "csp-trace-list";
    (csp.trace_entries || []).forEach((entry, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `csp-trace-row${index === csp.current_entry_index ? " current" : ""}`;
      button.dataset.stepIndex = String(index + 1);
      const meta = document.createElement("span");
      meta.className = "csp-trace-meta";
      meta.textContent = entry.action.replaceAll("_", " ");
      const text = document.createElement("span");
      text.className = "csp-trace-text";
      text.textContent = entry.text;
      button.append(meta, text);
      traceList.appendChild(button);
    });
    if (!(csp.trace_entries || []).length) {
      const empty = document.createElement("p");
      empty.className = "csp-copy";
      empty.textContent = "The decision trace will appear here once the search starts.";
      lowerSection.appendChild(empty);
    } else {
      lowerSection.appendChild(traceList);
    }
  }

  shell.appendChild(lowerSection);
  panel.appendChild(shell);
}

function renderDeliveryCspPanel(data) {
  const panel = $("csp-panel");
  panel.innerHTML = "";
  const csp = data.delivery_csp;
  const problem = data.delivery_problem;
  if (!csp || !problem) return;

  const valueLookup = new Map((problem.values || []).map((value) => [value.id, value]));
  const shell = document.createElement("div");
  shell.className = "csp-shell";

  const stateSection = document.createElement("section");
  stateSection.className = "csp-section";
  const stateHeading = document.createElement("h3");
  stateHeading.className = "csp-section-title";
  stateHeading.textContent = "Current CSP state";
  const stateCopy = document.createElement("p");
  stateCopy.className = "csp-copy";
  stateCopy.textContent = `Variables are deliveries, domains are the remaining slot-room options, and the constraints cover precedence, incompatibility, and room availability. Current focus: ${csp.focus_variable || "none"}.`;
  stateSection.append(stateHeading, stateCopy);

  const table = document.createElement("table");
  table.className = "csp-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>Delivery</th>
        <th>Current domain</th>
        <th>Assigned</th>
        <th>Status</th>
      </tr>
    </thead>
  `;
  const body = document.createElement("tbody");
  (csp.variables || []).forEach((row) => {
    const tr = document.createElement("tr");
    tr.className = row.status || "unchanged";

    const variable = document.createElement("td");
    const label = document.createElement("div");
    label.className = "delivery-variable-label";
    label.textContent = row.label || row.variable;
    const meta = document.createElement("div");
    meta.className = "delivery-variable-meta";
    meta.textContent = `${row.short_label || row.variable.toUpperCase()} · ${row.variable}`;
    variable.append(label, meta);

    const domain = document.createElement("td");
    const domainList = document.createElement("div");
    domainList.className = "csp-domain-list";
    if ((row.domain || []).length) {
      row.domain.forEach((valueId) => {
        const value = valueLookup.get(valueId);
        const chip = document.createElement("span");
        chip.className = "csp-domain-chip delivery-domain-chip";
        chip.textContent = value?.label || valueId;
        domainList.appendChild(chip);
      });
    } else {
      const chip = document.createElement("span");
      chip.className = "csp-domain-chip empty";
      chip.textContent = "empty";
      domainList.appendChild(chip);
    }
    domain.appendChild(domainList);

    const assigned = document.createElement("td");
    assigned.textContent = row.assigned_label || "—";

    const status = document.createElement("td");
    const pill = document.createElement("span");
    pill.className = `csp-status-pill ${row.status || "unchanged"}`;
    pill.textContent = row.status || "unchanged";
    status.appendChild(pill);

    tr.append(variable, domain, assigned, status);
    body.appendChild(tr);
  });
  table.appendChild(body);
  stateSection.appendChild(table);
  shell.appendChild(stateSection);

  const lowerSection = document.createElement("section");
  lowerSection.className = "csp-section";
  const lowerHeading = document.createElement("h3");
  lowerHeading.className = "csp-section-title";
  lowerHeading.textContent = state.view.cspViewMode === "tree" ? "Search tree" : "Decision trace";
  lowerSection.appendChild(lowerHeading);

  if (state.view.cspViewMode === "tree") {
    renderCspTree(lowerSection, data);
  } else {
    const traceList = document.createElement("div");
    traceList.className = "csp-trace-list";
    (csp.trace_entries || []).forEach((entry, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `csp-trace-row${index === csp.current_entry_index ? " current" : ""}`;
      button.dataset.stepIndex = String(index + 1);
      const meta = document.createElement("span");
      meta.className = "csp-trace-meta";
      meta.textContent = entry.action.replaceAll("_", " ");
      const text = document.createElement("span");
      text.className = "csp-trace-text";
      text.textContent = entry.text;
      button.append(meta, text);
      traceList.appendChild(button);
    });
    if (!(csp.trace_entries || []).length) {
      const empty = document.createElement("p");
      empty.className = "csp-copy";
      empty.textContent = "The decision trace will appear here once the search starts.";
      lowerSection.appendChild(empty);
    } else {
      lowerSection.appendChild(traceList);
    }
  }

  shell.appendChild(lowerSection);
  panel.appendChild(shell);
}

function renderCspMap(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  const problem = data.csp_problem;
  const csp = data.csp;
  if (!problem || !csp) return;

  const assignments = csp.assignments || {};
  const domains = csp.domains || {};
  const changed = new Set((csp.last_changes || []).map((change) => change.variable));
  const focus = csp.focus_variable;
  const failed = csp.failed_variable;

  const polygons = $svgNode("g");
  const labels = $svgNode("g");
  const markers = $svgNode("g");

  (problem.regions || []).forEach((region) => {
    const geometry = problem.geometry?.[region];
    if (!geometry) return;
    const fill = assignments[region] ? cspColourValue(problem, assignments[region]) : "rgba(255, 252, 246, 0.92)";
    const classes = ["csp-region"];
    if (region === focus) classes.push("focus");
    if (changed.has(region)) classes.push("reduced");
    if (region === failed || !(domains[region] || []).length) classes.push("failed");
    polygons.appendChild(
      $svgNode("polygon", {
        class: classes.join(" "),
        points: geometry.points.map(([x, y]) => `${x},${y}`).join(" "),
        style: `fill: ${fill};`,
      })
    );
    labels.appendChild(
      $svgNode("text", { class: "csp-region-label", x: geometry.label[0], y: geometry.label[1] }, region.toUpperCase())
    );

    if (!state.view.showCspDomains || assignments[region]) return;
    const remaining = domains[region] || [];
    if (!remaining.length) {
      const anchor = geometry.domain_anchor || [geometry.label[0], geometry.label[1] + 30];
      markers.appendChild($svgNode("circle", { class: "csp-domain-empty", cx: anchor[0], cy: anchor[1], r: 12 }));
      markers.appendChild($svgNode("line", { class: "csp-domain-cross", x1: anchor[0] - 5, y1: anchor[1] - 5, x2: anchor[0] + 5, y2: anchor[1] + 5 }));
      markers.appendChild($svgNode("line", { class: "csp-domain-cross", x1: anchor[0] + 5, y1: anchor[1] - 5, x2: anchor[0] - 5, y2: anchor[1] + 5 }));
      return;
    }
    const anchor = geometry.domain_anchor || [geometry.label[0], geometry.label[1] + 30];
    const width = (remaining.length - 1) * 22;
    remaining.forEach((colour, index) => {
      markers.appendChild(
        $svgNode("circle", {
          class: "csp-domain-marker",
          cx: anchor[0] - width / 2 + index * 22,
          cy: anchor[1],
          r: 8,
          fill: cspColourValue(problem, colour),
        })
      );
    });
  });

  svg.append(polygons, labels, markers);
}

function renderDeliverySchedule(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  svg.setAttribute("viewBox", "0 0 1000 860");
  const problem = data.delivery_problem;
  const csp = data.delivery_csp;
  if (!problem || !csp) return;

  const valueMap = new Map((problem.values || []).map((value) => [value.id, value]));
  const deliveryMap = new Map((problem.deliveries || []).map((delivery) => [delivery.id, delivery]));
  const changed = new Set((csp.last_changes || []).map((change) => change.variable));
  const focus = csp.focus_variable;
  const failed = csp.failed_variable;
  const placementsByValue = new Map((csp.placements || []).map((placement) => [placement.value, placement]));
  const candidateMap = csp.candidate_map || {};

  const left = 118;
  const top = 92;
  const width = 808;
  const height = 538;
  const footerTop = top + height + 54;
  const rooms = problem.rooms || [];
  const slots = problem.slots || [];
  const cellWidth = width / Math.max(slots.length, 1);
  const cellHeight = height / Math.max(rooms.length, 1);

  const backdrop = $svgNode("g");
  const labels = $svgNode("g");
  const cells = $svgNode("g");
  const overlays = $svgNode("g");
  const footer = $svgNode("g");

  backdrop.appendChild(
    $svgNode("rect", {
      class: "delivery-board",
      x: left - 28,
      y: top - 42,
      width: width + 56,
      height: height + 84,
      rx: 32,
    })
  );

  slots.forEach((slot, slotIndex) => {
    const x = left + slotIndex * cellWidth;
    labels.appendChild(
      $svgNode(
        "text",
        { class: "delivery-slot-label", x: x + cellWidth / 2, y: top - 18 },
        slot.label
      )
    );
  });

  rooms.forEach((room, roomIndex) => {
    const y = top + roomIndex * cellHeight;
    labels.appendChild(
      $svgNode(
        "text",
        { class: "delivery-room-label", x: left - 24, y: y + cellHeight / 2 },
        room.label
      )
    );
  });

  rooms.forEach((room, roomIndex) => {
    slots.forEach((slot, slotIndex) => {
      const x = left + slotIndex * cellWidth;
      const y = top + roomIndex * cellHeight;
      const value = (problem.values || []).find((candidate) => candidate.slot === slot.id && candidate.room === room.id);
      if (!value) return;
      const placement = placementsByValue.get(value.id);
      const candidateDeliveries = (candidateMap[value.id] || []).map((deliveryId) => deliveryMap.get(deliveryId)).filter(Boolean);
      const cellFocus = placement?.delivery === focus || candidateDeliveries.some((delivery) => delivery.id === focus);
      const cellChanged = candidateDeliveries.some((delivery) => changed.has(delivery.id));
      const classes = ["delivery-slot-cell"];
      if (cellFocus) classes.push("focus");
      if (cellChanged) classes.push("reduced");
      cells.appendChild(
        $svgNode("rect", {
          class: classes.join(" "),
          x,
          y,
          width: cellWidth - 14,
          height: cellHeight - 14,
          rx: 24,
        })
      );
      labels.appendChild(
        $svgNode(
          "text",
          {
            class: "delivery-cell-label",
            x: x + 26,
            y: y + 32,
          },
          `${slot.label} · ${room.label}`
        )
      );

      if (placement) {
        const fillColour = placement.colour || deliveryMap.get(placement.delivery)?.colour || "#d8c9b6";
        overlays.appendChild(
          $svgNode("rect", {
            class: `delivery-placement-card${placement.delivery === focus ? " focus" : ""}`,
            x: x + 22,
            y: y + 52,
            width: cellWidth - 58,
            height: cellHeight - 84,
            rx: 22,
            style: `fill: ${fillColour};`,
          })
        );
        overlays.appendChild(
          $svgNode(
            "text",
            {
              class: "delivery-placement-short",
              x: x + cellWidth / 2 - 7,
              y: y + cellHeight / 2 + 2,
            },
            placement.short_label
          )
        );
        overlays.appendChild(
          $svgNode(
            "text",
            {
              class: "delivery-placement-name",
              x: x + cellWidth / 2 - 7,
              y: y + cellHeight / 2 + 34,
            },
            placement.label
          )
        );
      } else if (state.view.showCspDomains) {
        candidateDeliveries.slice(0, 4).forEach((delivery, index) => {
          overlays.appendChild(
            $svgNode("rect", {
              class: `delivery-candidate-badge${delivery.id === focus ? " focus" : ""}${changed.has(delivery.id) ? " reduced" : ""}`,
              x: x + 22,
              y: y + 54 + index * 34,
              width: Math.min(cellWidth - 58, 176),
              height: 26,
              rx: 13,
              style: `fill: ${delivery.colour}22; stroke: ${delivery.colour};`,
            })
          );
          overlays.appendChild(
            $svgNode(
              "text",
              {
                class: "delivery-candidate-text",
                x: x + 36,
                y: y + 71 + index * 34,
              },
              `${delivery.short_label}  ${delivery.label}`
            )
          );
        });
        if (!candidateDeliveries.length) {
          overlays.appendChild(
            $svgNode("text", { class: "delivery-empty-text", x: x + cellWidth / 2 - 7, y: y + cellHeight / 2 + 10 }, "No candidate")
          );
        }
      }
    });
  });

  const constraintHeading = $svgNode("text", { class: "delivery-footer-heading", x: left - 28, y: footerTop }, "Active constraints");
  footer.appendChild(constraintHeading);
  (problem.constraints || []).slice(0, 4).forEach((constraint, index) => {
    footer.appendChild(
      $svgNode("rect", {
        class: "delivery-constraint-pill",
        x: left - 28 + index * 188,
        y: footerTop + 18,
        width: 180,
        height: 38,
        rx: 19,
      })
    );
    footer.appendChild(
      $svgNode(
        "text",
        {
          class: "delivery-constraint-text",
          x: left - 10 + index * 188,
          y: footerTop + 42,
        },
        constraint.label
      )
    );
  });

  if (failed) {
    const failedLabel = deliveryMap.get(failed)?.label || failed;
    footer.appendChild(
      $svgNode("rect", {
        class: "delivery-failure-banner",
        x: left - 28,
        y: footerTop + 68,
        width: 480,
        height: 44,
        rx: 22,
      })
    );
    footer.appendChild(
      $svgNode(
        "text",
        {
          class: "delivery-failure-text",
          x: left - 2,
          y: footerTop + 96,
        },
        `${failedLabel} has no legal slot-room values left.`
      )
    );
  }

  svg.append(backdrop, labels, cells, overlays, footer);
}

function renderTree(data) {
  const svg = $("search-tree-svg");
  svg.innerHTML = "";
  const nodes = (data.tree?.nodes || []).filter(
    (node) => !state.view.showPrunedBranches || node.status !== "pruned"
  );
  if (!nodes.length) return;

  const nodeMap = new Map(nodes.map((node) => [node.tree_id, node]));
  const activePath = new Set(data.search.active_tree_path || []);
  const bestPath = new Set(data.search.best_tree_path || []);
  const finalPath = new Set((data.search.final_tree_path || []).concat(data.search.active_tree_path || []));
  const links = $svgNode("g");
  const circles = $svgNode("g");

  nodes.forEach((node) => {
    if (!node.parent || !nodeMap.has(node.parent)) return;
    const parent = nodeMap.get(node.parent);
    const classes = ["tree-link"];
    if (activePath.has(node.tree_id) && activePath.has(node.parent)) classes.push("active");
    if (bestPath.has(node.tree_id) && bestPath.has(node.parent)) classes.push("best");
    if (finalPath.has(node.tree_id) && finalPath.has(node.parent)) classes.push("final");
    if (node.status === "pruned") classes.push("pruned");
    links.appendChild(
      $svgNode("line", {
        class: classes.join(" "),
        x1: parent.x * 1000,
        y1: parent.y * 700,
        x2: node.x * 1000,
        y2: node.y * 700,
      })
    );
  });

  nodes.forEach((node) => {
    const classes = ["tree-node", node.status];
    if (data.search.active_tree_node === node.tree_id) classes.push("active");
    if (activePath.has(node.tree_id)) classes.push("branch");
    if (bestPath.has(node.tree_id)) classes.push("best");
    if (finalPath.has(node.tree_id)) classes.push("final");
    const group = $svgNode("g", {
      class: classes.join(" "),
      transform: `translate(${node.x * 1000}, ${node.y * 700})`,
    });
    if (isLogic()) {
      group.appendChild(
        $svgNode("rect", {
          class: "tree-node-card",
          x: -76,
          y: -30,
          width: 152,
          height: 60,
          rx: 18,
        })
      );
      group.appendChild($svgNode("text", { class: "tree-node-heading", y: -5 }, node.graph_node));
      group.appendChild(
        $svgNode(
          "text",
          { class: "tree-node-subtext", y: 14 },
          node.assignment_text || "No assignments"
        )
      );
      group.appendChild(
        $svgNode("text", { class: "tree-node-reason", y: 28 }, node.reason || "")
      );
    } else {
      group.appendChild($svgNode("circle", { class: "tree-node-circle", r: isLabyrinth() ? 38 : 34 }));
      const label = isLabyrinth() ? String(node.graph_node).replace(", ", ",") : node.graph_node;
      group.appendChild(
        $svgNode(
          "text",
          { class: isLabyrinth() ? "tree-node-label tree-node-label-labyrinth" : "tree-node-label", y: isLabyrinth() ? 4 : -6 },
          label
        )
      );
      if (isWeightedGraphSearch()) {
        group.appendChild($svgNode("text", { class: "tree-node-cost", y: 24 }, formatNumber(node.path_cost)));
      }
    }
    circles.appendChild(group);
  });

  svg.appendChild(links);
  svg.appendChild(circles);
}

function renderWeightedGraph(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  const graph = data.graph;
  if (!graph) return;

  const nodeMap = new Map(graph.nodes.map((node) => [node.id, node]));
  const currentPath = new Set(data.search.current_graph_path || []);
  const bestPath = new Set(data.search.best_graph_path || []);
  const finalPath = new Set(data.search.final_graph_path || []);
  const exploredEdgeIds = new Set(
    (data.search.explored_graph_edges || []).map(([u, v]) => edgeId(u, v))
  );
  const currentEdgeIds = pathToEdgeIds(data.search.current_graph_path || []);
  const bestEdgeIds = pathToEdgeIds(data.search.best_graph_path || []);
  const finalEdgeIds = pathToEdgeIds(data.search.final_graph_path || []);
  const consideredEdgeId = data.search.considered_edge
    ? edgeId(data.search.considered_edge[0], data.search.considered_edge[1])
    : null;

  const baselines = $svgNode("g");
  const costs = $svgNode("g");
  const overlays = $svgNode("g");
  const nodes = $svgNode("g");

  graph.edges.forEach((edge) => {
    const left = nodeMap.get(edge.u);
    const right = nodeMap.get(edge.v);
    const lineProps = {
      x1: left.x * 1000,
      y1: left.y * 700,
      x2: right.x * 1000,
      y2: right.y * 700,
    };
    baselines.appendChild($svgNode("line", { class: "graph-edge", ...lineProps }));
    costs.appendChild(
      $svgNode(
        "text",
        {
          class: "graph-cost",
          x: ((left.x + right.x) / 2) * 1000,
          y: ((left.y + right.y) / 2) * 700 - 8,
        },
        Number(edge.cost).toFixed(2)
      )
    );

    const id = edge.id || edgeId(edge.u, edge.v);
    if (state.view.showExploredEdges && exploredEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay explored", ...lineProps }));
    }
    if (bestEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay best", ...lineProps }));
    }
    if (currentEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay current", ...lineProps }));
    }
    if (consideredEdgeId === id) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay considered", ...lineProps }));
    }
    if (finalEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay final", ...lineProps }));
    }
  });

  graph.nodes.forEach((node) => {
    const classes = ["graph-node"];
    if (node.id === graph.start) classes.push("start");
    if (node.id === graph.goal) classes.push("goal");
    if (currentPath.has(node.id)) classes.push("current");
    if (bestPath.has(node.id)) classes.push("best");
    if (finalPath.has(node.id)) classes.push("final");
    const activeNode = (data.search.current_graph_path || []).slice(-1)[0];
    if (activeNode === node.id) classes.push("active");
    const group = $svgNode("g", {
      class: classes.join(" "),
      transform: `translate(${node.x * 1000}, ${node.y * 700})`,
    });
    group.appendChild($svgNode("circle", { class: "graph-node-circle", r: 30 }));
    group.appendChild($svgNode("text", { class: "graph-node-label" }, node.id));
    nodes.appendChild(group);
  });

  svg.appendChild(baselines);
  svg.appendChild(costs);
  svg.appendChild(overlays);
  svg.appendChild(nodes);
}

function renderGraphReachability(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  const graph = data.graph;
  if (!graph) return;

  const nodeMap = new Map(graph.nodes.map((node) => [node.id, node]));
  const currentPath = new Set(data.search.current_graph_path || []);
  const visitedNodes = new Set(data.search.visited_order || []);
  const deadEndNodes = new Set(data.search.dead_end_nodes || []);
  const finalPath = new Set(data.search.final_graph_path || []);
  const exploredEdgeIds = new Set(
    (data.search.explored_graph_edges || []).map(([u, v]) => edgeId(u, v))
  );
  const currentEdgeIds = pathToEdgeIds(data.search.current_graph_path || []);
  const finalEdgeIds = pathToEdgeIds(data.search.final_graph_path || []);

  const baselines = $svgNode("g");
  const overlays = $svgNode("g");
  const nodes = $svgNode("g");

  graph.edges.forEach((edge) => {
    const left = nodeMap.get(edge.u);
    const right = nodeMap.get(edge.v);
    const lineProps = {
      x1: left.x * 1000,
      y1: left.y * 700,
      x2: right.x * 1000,
      y2: right.y * 700,
    };
    baselines.appendChild($svgNode("line", { class: "graph-edge", ...lineProps }));

    const id = edge.id || edgeId(edge.u, edge.v);
    if (exploredEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay explored", ...lineProps }));
    }
    if (currentEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay current", ...lineProps }));
    }
    if (finalEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay final", ...lineProps }));
    }
  });

  graph.nodes.forEach((node) => {
    const classes = ["graph-node"];
    if (node.id === graph.start) classes.push("start");
    if (node.id === graph.goal) classes.push("goal");
    if (visitedNodes.has(node.id)) classes.push("visited");
    if (deadEndNodes.has(node.id)) classes.push("dead-end");
    if (currentPath.has(node.id)) classes.push("current");
    if (finalPath.has(node.id)) classes.push("final");
    const activeNode = (data.search.current_graph_path || []).slice(-1)[0];
    if (activeNode === node.id) classes.push("active");
    const group = $svgNode("g", {
      class: classes.join(" "),
      transform: `translate(${node.x * 1000}, ${node.y * 700})`,
    });
    group.appendChild($svgNode("circle", { class: "graph-node-circle", r: 28 }));
    group.appendChild($svgNode("text", { class: "graph-node-label" }, node.id));
    nodes.appendChild(group);
  });

  svg.appendChild(baselines);
  svg.appendChild(overlays);
  svg.appendChild(nodes);
}

function renderLabyrinth(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  const labyrinth = data.labyrinth;
  if (!labyrinth) return;

  const rows = labyrinth.rows;
  const cols = labyrinth.cols;
  const cellSize = Math.min(880 / cols, 620 / rows);
  const offsetX = (1000 - cols * cellSize) / 2;
  const offsetY = (700 - rows * cellSize) / 2;
  const currentRoute = new Set((data.search.current_route || []).map(cellKey));
  const visited = new Set((data.search.visited_order || []).map(cellKey));
  const deadEnds = new Set((data.search.dead_end_cells || []).map(cellKey));
  const finalPath = new Set((data.search.final_path || []).map(cellKey));

  const gridGroup = $svgNode("g");
  const textGroup = $svgNode("g");

  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const cell = [row, col];
      const key = cellKey(cell);
      const value = labyrinth.grid[row][col];
      const classes = ["maze-cell"];
      if (value === "#") {
        classes.push("wall");
      } else {
        classes.push("open");
        if (visited.has(key)) classes.push("visited");
        if (deadEnds.has(key)) classes.push("dead-end");
        if (currentRoute.has(key)) classes.push("current");
        if (finalPath.has(key)) classes.push("final");
        if (row === labyrinth.start[0] && col === labyrinth.start[1]) classes.push("start");
        if (row === labyrinth.exit[0] && col === labyrinth.exit[1]) classes.push("exit");
      }

      gridGroup.appendChild(
        $svgNode("rect", {
          class: classes.join(" "),
          x: offsetX + col * cellSize,
          y: offsetY + row * cellSize,
          width: cellSize,
          height: cellSize,
          rx: Math.max(1, cellSize * 0.14),
        })
      );

      if (value === "S" || value === "E") {
        textGroup.appendChild(
          $svgNode(
            "text",
            {
              class: "maze-cell-label",
              x: offsetX + col * cellSize + cellSize / 2,
              y: offsetY + row * cellSize + cellSize / 2 + Math.min(cellSize * 0.18, 6),
            },
            value
          )
        );
      }
    }
  }

  svg.appendChild(gridGroup);
  svg.appendChild(textGroup);
}

function renderLogicProblem(data) {
  const panel = $("logic-problem-panel");
  panel.innerHTML = "";
  const logic = data.logic;
  if (!logic) return;

  const shell = document.createElement("div");
  shell.className = "logic-shell";

  if (logic.mode === "entailment") {
    const callout = document.createElement("div");
    callout.className = "logic-callout";
    callout.textContent =
      "To test entailment, the app checks whether the knowledge base together with not query is unsatisfiable.";
    shell.appendChild(callout);
  }

  const summaryGrid = document.createElement("div");
  summaryGrid.className = "logic-summary-grid";
  [
    ["Satisfied", logic.summary?.satisfied ?? 0],
    ["Unresolved", logic.summary?.unresolved ?? 0],
    ["Unit", logic.summary?.unit ?? 0],
    ["Contradicted", logic.summary?.contradicted ?? 0],
    ["Assigned", `${logic.summary?.assigned_variables ?? 0} / ${logic.summary?.total_variables ?? 0}`],
  ].forEach(([label, value]) => {
    const card = document.createElement("div");
    card.className = "logic-summary-card";
    const title = document.createElement("span");
    title.className = "logic-summary-label";
    title.textContent = label;
    const body = document.createElement("strong");
    body.className = "logic-summary-value";
    body.textContent = String(value);
    card.append(title, body);
    summaryGrid.appendChild(card);
  });
  shell.appendChild(summaryGrid);

  if (logic.mode === "entailment") {
    const inputPanel = document.createElement("div");
    inputPanel.className = "logic-input-panel";
    const heading = document.createElement("h3");
    heading.className = "logic-section-title";
    heading.textContent = "Knowledge base";
    inputPanel.appendChild(heading);
    const list = document.createElement("div");
    list.className = "logic-input-list";
    (logic.kb_formulas || []).forEach((formula) => {
      const item = document.createElement("div");
      item.className = "logic-input-item";
      item.textContent = formula;
      list.appendChild(item);
    });
    const query = document.createElement("div");
    query.className = "logic-input-item";
    query.textContent = `query: ${logic.query || ""}`;
    list.appendChild(query);
    const target = document.createElement("div");
    target.className = "logic-callout";
    target.textContent = logic.entailment_target || "";
    inputPanel.append(list, target);
    shell.appendChild(inputPanel);
  }

  const assignmentPanel = document.createElement("div");
  assignmentPanel.className = "logic-assignment-panel";
  const assignmentHeading = document.createElement("h3");
  assignmentHeading.className = "logic-section-title";
  assignmentHeading.textContent = "Current assignment";
  assignmentPanel.appendChild(assignmentHeading);
  if (!logic.assignment?.length) {
    const empty = document.createElement("div");
    empty.className = "logic-assignment-empty";
    empty.textContent = "No variables have been assigned yet.";
    assignmentPanel.appendChild(empty);
  } else {
    const assignmentList = document.createElement("div");
    assignmentList.className = "logic-assignment-list";
    logic.assignment.forEach((entry) => {
      const row = document.createElement("div");
      row.className = "logic-assignment-item";
      const text = document.createElement("span");
      text.className = "logic-assignment-text";
      text.textContent = entry.text;
      const reason = document.createElement("span");
      reason.className = "logic-assignment-reason";
      reason.textContent =
        entry.reason === "decision"
          ? "decision"
          : entry.reason === "unit"
            ? `unit from C${(entry.clause_index ?? 0) + 1}`
            : "pure literal";
      row.append(text, reason);
      assignmentList.appendChild(row);
    });
    assignmentPanel.appendChild(assignmentList);
  }
  shell.appendChild(assignmentPanel);

  const clausePanel = document.createElement("div");
  const clauseHeading = document.createElement("h3");
  clauseHeading.className = "logic-section-title";
  clauseHeading.textContent = "CNF clauses";
  clausePanel.appendChild(clauseHeading);
  const clauseList = document.createElement("div");
  clauseList.className = "logic-clause-list";
  (logic.clauses || []).forEach((clause) => {
    const row = document.createElement("div");
    row.className = `logic-clause-row ${clause.status}`;
    const header = document.createElement("div");
    header.className = "logic-clause-header";
    const label = document.createElement("span");
    label.className = "logic-clause-label";
    label.textContent = `C${clause.index + 1} ${clause.text}`;
    const state = document.createElement("span");
    state.className = "logic-clause-state";
    state.textContent = clause.status;
    header.append(label, state);

    const literalRow = document.createElement("div");
    literalRow.className = "logic-literal-row";
    (clause.literals || []).forEach((literal) => {
      const chip = document.createElement("span");
      chip.className = `logic-literal-chip ${literal.state}`;
      chip.textContent = literal.text;
      literalRow.appendChild(chip);
    });

    row.append(header, literalRow);
    if (clause.status === "unit" && clause.unit_literal) {
      const footnote = document.createElement("div");
      footnote.className = "logic-clause-footnote";
      footnote.textContent = `Forced literal: ${formatLogicLiteral(clause.unit_literal)}`;
      row.appendChild(footnote);
    }
    clauseList.appendChild(row);
  });
  clausePanel.appendChild(clauseList);
  shell.appendChild(clausePanel);

  panel.appendChild(shell);
}

function planningActionBySignature(data, signature) {
  if (!signature) return null;
  const allActions = [
    ...(data.planning?.applicable_actions || []),
    ...(data.planning?.plan || []),
  ];
  return allActions.find((action) => action.signature === signature) || null;
}

function selectedPlanningAction(data) {
  const selectedFromView = planningActionBySignature(data, state.view.planningSelectedAction);
  if (selectedFromView) return selectedFromView;
  if (data.planning?.selected_action) return data.planning.selected_action;
  if (data.planning?.applicable_actions?.length) return data.planning.applicable_actions[0];
  if (data.planning?.plan?.length) return data.planning.plan[Math.min(data.planning.plan_index || 0, data.planning.plan.length - 1)];
  return null;
}

function planRowState(planIndex, actionIndex) {
  if (planIndex === 0) {
    return actionIndex === 0 ? "current" : "future";
  }
  if (actionIndex < planIndex - 1) return "completed";
  if (actionIndex === planIndex - 1) return "current";
  return "future";
}

function renderPlanningInternal(data) {
  const panel = $("planning-panel");
  panel.innerHTML = "";
  const planning = data.planning;
  if (!planning) return;

  const shell = document.createElement("div");
  shell.className = "planning-shell";

  const factsSection = document.createElement("section");
  factsSection.className = "planning-section";
  const factsHeading = document.createElement("h3");
  factsHeading.className = "planning-section-title";
  factsHeading.textContent = "Current state";
  factsSection.appendChild(factsHeading);
  const factGroups = new Map();
  (planning.facts || []).forEach((fact) => {
    if (!factGroups.has(fact.predicate)) factGroups.set(fact.predicate, []);
    factGroups.get(fact.predicate).push(fact);
  });
  const factGrid = document.createElement("div");
  factGrid.className = "planning-group-grid";
  Array.from(factGroups.entries()).forEach(([predicate, facts]) => {
    const group = document.createElement("div");
    group.className = "planning-group-card";
    const label = document.createElement("span");
    label.className = "planning-group-label";
    label.textContent = predicate;
    const chips = document.createElement("div");
    chips.className = "planning-chip-list";
    facts.forEach((fact) => {
      const chip = document.createElement("span");
      chip.className = "planning-chip";
      chip.textContent = fact.text;
      chips.appendChild(chip);
    });
    group.append(label, chips);
    factGrid.appendChild(group);
  });
  if (!factGroups.size) {
    const empty = document.createElement("div");
    empty.className = "planning-empty";
    empty.textContent = "No facts are available for this state.";
    factGrid.appendChild(empty);
  }
  factsSection.appendChild(factGrid);
  shell.appendChild(factsSection);
  const chosenAction = selectedPlanningAction(data);

  const inspectorSection = document.createElement("section");
  inspectorSection.className = "planning-section";
  const inspectorHeading = document.createElement("h3");
  inspectorHeading.className = "planning-section-title";
  inspectorHeading.textContent = "Action schema inspector";
  inspectorSection.appendChild(inspectorHeading);
  const inspector = document.createElement("div");
  inspector.className = "planning-inspector-shell";
  if (chosenAction) {
    const heading = document.createElement("div");
    heading.className = "planning-inspector-heading";
    const signature = document.createElement("span");
    signature.className = "planning-inspector-signature";
    signature.textContent = chosenAction.signature;
    const args = document.createElement("span");
    args.className = "planning-inspector-args";
    args.textContent = chosenAction.args.join(", ");
    heading.append(signature, args);
    inspector.appendChild(heading);

    const effectGrid = document.createElement("div");
    effectGrid.className = "planning-effect-grid";
    [
      ["Preconditions", chosenAction.preconditions || []],
      ["Add effects", chosenAction.add_effects || []],
      ["Delete effects", chosenAction.delete_effects || []],
    ].forEach(([labelText, facts]) => {
      const card = document.createElement("div");
      card.className = "planning-effect-card";
      const label = document.createElement("span");
      label.className = "planning-effect-label";
      label.textContent = labelText;
      const chips = document.createElement("div");
      chips.className = "planning-chip-list";
      if (!facts.length) {
        const empty = document.createElement("span");
        empty.className = "planning-empty";
        empty.textContent = "none";
        chips.appendChild(empty);
      } else {
        facts.forEach((fact) => {
          const chip = document.createElement("span");
          chip.className = "planning-chip";
          chip.textContent = fact.text;
          chips.appendChild(chip);
        });
      }
      card.append(label, chips);
      effectGrid.appendChild(card);
    });
    inspector.appendChild(effectGrid);
  } else {
    const empty = document.createElement("div");
    empty.className = "planning-empty";
    empty.textContent = "Select an action to inspect its preconditions and effects.";
    inspector.appendChild(empty);
  }
  inspectorSection.appendChild(inspector);
  shell.appendChild(inspectorSection);

  const planSection = document.createElement("section");
  planSection.className = "planning-section";
  const planHeading = document.createElement("h3");
  planHeading.className = "planning-section-title";
  planHeading.textContent = "Plan trace";
  planSection.appendChild(planHeading);
  const planList = document.createElement("div");
  planList.className = "planning-plan-list";
  (planning.plan || []).forEach((action, index) => {
    const rowState = planRowState(planning.plan_index || 0, index);
    const button = document.createElement("button");
    button.type = "button";
    button.className = `planning-plan-button ${rowState}`;
    button.dataset.stepIndex = String(index + 2);
    button.dataset.actionSignature = action.signature;
    const signature = document.createElement("span");
    signature.className = "planning-plan-signature";
    signature.textContent = action.signature;
    const meta = document.createElement("span");
    meta.className = "planning-plan-step";
    meta.textContent = `Step ${index + 1}`;
    button.append(signature, meta);
    planList.appendChild(button);
  });
  if (!(planning.plan || []).length) {
    const empty = document.createElement("div");
    empty.className = "planning-empty";
    empty.textContent = "The plan will appear here once the planner has solved the problem.";
    planList.appendChild(empty);
  }
  planSection.appendChild(planList);
  shell.appendChild(planSection);

  if (state.view.showPlannerTrace && (planning.search_trace || []).length) {
    const searchSection = document.createElement("section");
    searchSection.className = "planning-section";
    const searchHeading = document.createElement("h3");
    searchHeading.className = "planning-section-title";
    searchHeading.textContent = "Planner trace";
    searchSection.appendChild(searchHeading);
    const searchList = document.createElement("div");
    searchList.className = "planning-search-trace";
    (planning.search_trace || []).forEach((entry) => {
      const row = document.createElement("div");
      row.className = `planning-search-row${entry.goal_reached ? " goal" : ""}`;
      const meta = document.createElement("div");
      meta.className = "planning-search-meta";
      meta.textContent = `Expand S${entry.index} | depth ${entry.depth} | frontier ${entry.frontier_size}`;
      const plan = document.createElement("div");
      plan.className = "planning-search-plan";
      plan.textContent = entry.plan_prefix.length ? entry.plan_prefix.join(" -> ") : "initial state";
      const facts = document.createElement("div");
      facts.className = "planning-search-facts";
      facts.textContent = entry.state_facts.slice(0, 3).join(" • ");
      row.append(meta, plan, facts);
      searchList.appendChild(row);
    });
    searchSection.appendChild(searchList);
    shell.appendChild(searchSection);
  }

  panel.appendChild(shell);
}

function renderPlanningWorldPanel(data) {
  const panel = $("planning-world-panel");
  panel.innerHTML = "";
  const planning = data.planning;
  if (!planning) return;

  const shell = document.createElement("div");
  shell.className = "planning-world-shell";

  const summarySection = document.createElement("section");
  summarySection.className = "planning-section";
  const summaryHeading = document.createElement("h3");
  summaryHeading.className = "planning-section-title";
  summaryHeading.textContent = "Situation";
  summarySection.appendChild(summaryHeading);

  const world = planning.world || {};
  const summaryCopy = document.createElement("p");
  summaryCopy.className = "planning-world-copy";
  summaryCopy.textContent = [
    `Robot: ${world.robot_room || "unknown"}.`,
    world.parcel_carried
      ? "Parcel: carried by the robot."
      : `Parcel: ${world.parcel_room || "unknown"}.`,
    world.robot_has_keycard
      ? "Keycard: held by the robot."
      : `Keycard: ${world.keycard_room || "unknown"}.`,
    `Door: ${world.door_locked ? "locked" : "unlocked"}.`,
    "Goal: make at(parcel, lab) true.",
  ].join(" ");
  summarySection.appendChild(summaryCopy);

  const summaryGrid = document.createElement("div");
  summaryGrid.className = "planning-world-summary";
  [
    ["Robot", world.robot_room || "unknown"],
    ["Parcel", world.parcel_carried ? "carried" : world.parcel_room || "unknown"],
    ["Keycard", world.robot_has_keycard ? "held" : world.keycard_room || "unknown"],
    ["Door", world.door_locked ? "locked" : "unlocked"],
  ].forEach(([labelText, valueText]) => {
    const card = document.createElement("div");
    card.className = "planning-group-card";
    const label = document.createElement("span");
    label.className = "planning-group-label";
    label.textContent = labelText;
    const value = document.createElement("div");
    value.textContent = valueText;
    card.append(label, value);
    summaryGrid.appendChild(card);
  });
  summarySection.appendChild(summaryGrid);
  shell.appendChild(summarySection);

  const actionsSection = document.createElement("section");
  actionsSection.className = "planning-section";
  const actionsHeading = document.createElement("h3");
  actionsHeading.className = "planning-section-title";
  actionsHeading.textContent = "Available actions";
  actionsSection.appendChild(actionsHeading);
  const actionList = document.createElement("div");
  actionList.className = "planning-action-list";
  const chosenAction = selectedPlanningAction(data);
  (planning.applicable_actions || []).forEach((action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `planning-action-button${chosenAction?.signature === action.signature ? " selected" : ""}`;
    button.dataset.actionSignature = action.signature;
    const signature = document.createElement("span");
    signature.className = "planning-action-signature";
    signature.textContent = action.signature;
    const category = document.createElement("span");
    category.className = "planning-action-category";
    category.textContent = action.category;
    button.append(signature, category);
    actionList.appendChild(button);
  });
  if (!(planning.applicable_actions || []).length) {
    const empty = document.createElement("div");
    empty.className = "planning-empty";
    empty.textContent = "No grounded actions are currently applicable.";
    actionList.appendChild(empty);
  }
  actionsSection.appendChild(actionList);
  shell.appendChild(actionsSection);

  panel.appendChild(shell);
}

function renderFoundationInternal(data) {
  const panel = $("foundation-panel");
  panel.innerHTML = "";
  const foundation = data.foundation_models;
  if (!foundation) return;

  const shell = document.createElement("div");
  shell.className = "foundation-shell";

  const tokensSection = document.createElement("section");
  tokensSection.className = "foundation-section";
  const tokensHeading = document.createElement("h3");
  tokensHeading.className = "foundation-section-title";
  tokensHeading.textContent = "Token sequence";
  tokensSection.appendChild(tokensHeading);
  const tokenList = document.createElement("div");
  tokenList.className = "foundation-token-list";
  (foundation.tokens || []).forEach((token) => {
    const card = document.createElement("div");
    card.className = "foundation-token-card";
    const meta = document.createElement("span");
    meta.className = "foundation-token-meta";
    meta.textContent = `token ${token.index}  |  id ${token.token_id}`;
    const text = document.createElement("span");
    text.className = "foundation-token-text";
    text.textContent = token.text;
    card.append(meta, text);
    tokenList.appendChild(card);
  });
  if (!(foundation.tokens || []).length) {
    const empty = document.createElement("div");
    empty.className = "foundation-empty";
    empty.textContent = "No tokens are available for the current text.";
    tokenList.appendChild(empty);
  }
  tokensSection.appendChild(tokenList);
  shell.appendChild(tokensSection);

  const comparisonSection = document.createElement("section");
  comparisonSection.className = "foundation-section";
  const comparisonHeading = document.createElement("h3");
  comparisonHeading.className = "foundation-section-title";
  comparisonHeading.textContent = "Comparison";
  comparisonSection.appendChild(comparisonHeading);
  const comparisonGrid = document.createElement("div");
  comparisonGrid.className = "foundation-comparison-grid";
  (foundation.comparison || []).forEach((entry) => {
    const card = document.createElement("div");
    card.className = `foundation-comparison-card${entry.active ? " active" : ""}`;
    const label = document.createElement("span");
    label.className = "foundation-comparison-label";
    label.textContent = entry.label;
    const count = document.createElement("strong");
    count.textContent = `${entry.token_count} tokens`;
    const stats = document.createElement("div");
    stats.className = "foundation-comparison-subtext";
    stats.textContent = `avg ${entry.average_token_length} chars  |  context ${entry.context_usage}`;
    card.append(label, count, stats);
    comparisonGrid.appendChild(card);
  });
  comparisonSection.appendChild(comparisonGrid);
  shell.appendChild(comparisonSection);

  const bpeSection = document.createElement("section");
  bpeSection.className = "foundation-section";
  const bpeHeading = document.createElement("h3");
  bpeHeading.className = "foundation-section-title";
  bpeHeading.textContent = "BPE learning trace";
  bpeSection.appendChild(bpeHeading);

  const bpeGrid = document.createElement("div");
  bpeGrid.className = "foundation-bpe-grid";

  const summaryCard = document.createElement("div");
  summaryCard.className = "foundation-bpe-card";
  const summaryLabel = document.createElement("span");
  summaryLabel.className = "foundation-bpe-label";
  summaryLabel.textContent = "Current merge step";
  const summaryValue = document.createElement("strong");
  summaryValue.textContent = `${foundation.bpe?.merge_step || 0} / ${foundation.bpe?.requested_merges || 0}`;
  summaryCard.append(summaryLabel, summaryValue);
  if (foundation.mode !== "bpe") {
    const copy = document.createElement("div");
    copy.className = "foundation-bpe-copy";
    copy.textContent = "Switch to learned BPE to step through one merge per replay step.";
    summaryCard.appendChild(copy);
  } else if (foundation.bpe?.selected_pair) {
    const merge = document.createElement("div");
    merge.className = "foundation-bpe-merge";
    merge.textContent = `${foundation.bpe.selected_pair.left} + ${foundation.bpe.selected_pair.right} -> ${foundation.bpe.selected_pair.merged}`;
    const copy = document.createElement("div");
    copy.className = "foundation-bpe-copy";
    copy.textContent = `Selected because it appears ${foundation.bpe.selected_pair.count} time(s) in the current corpus segmentation.`;
    summaryCard.append(merge, copy);
  } else {
    const copy = document.createElement("div");
    copy.className = "foundation-bpe-copy";
    copy.textContent = "The corpus is still at character level. Step forward to start merging frequent pairs.";
    summaryCard.appendChild(copy);
  }
  bpeGrid.appendChild(summaryCard);

  const pairsCard = document.createElement("div");
  pairsCard.className = "foundation-bpe-card";
  const pairsLabel = document.createElement("span");
  pairsLabel.className = "foundation-bpe-label";
  pairsLabel.textContent = "Most frequent pairs";
  pairsCard.appendChild(pairsLabel);
  const pairList = document.createElement("div");
  pairList.className = "foundation-pair-list";
  (foundation.bpe?.pair_counts || []).forEach((entry) => {
    const row = document.createElement("div");
    row.className = "foundation-pair-row";
    const pair = document.createElement("span");
    pair.className = "foundation-pair-text";
    pair.textContent = entry.pair;
    const count = document.createElement("span");
    count.className = "foundation-pair-count";
    count.textContent = `${entry.count}`;
    row.append(pair, count);
    pairList.appendChild(row);
  });
  if (!(foundation.bpe?.pair_counts || []).length) {
    const empty = document.createElement("div");
    empty.className = "foundation-empty";
    empty.textContent = "No adjacent pairs remain to merge.";
    pairList.appendChild(empty);
  }
  pairsCard.appendChild(pairList);
  bpeGrid.appendChild(pairsCard);

  const corpusCard = document.createElement("div");
  corpusCard.className = "foundation-bpe-card";
  const corpusLabel = document.createElement("span");
  corpusLabel.className = "foundation-bpe-label";
  corpusLabel.textContent = "Segmented corpus";
  corpusCard.appendChild(corpusLabel);
  const corpusList = document.createElement("div");
  corpusList.className = "foundation-corpus-list";
  (foundation.bpe?.segmented_corpus || []).forEach((line) => {
    const row = document.createElement("div");
    row.className = "foundation-corpus-row";
    row.textContent = line;
    corpusList.appendChild(row);
  });
  corpusCard.appendChild(corpusList);
  bpeGrid.appendChild(corpusCard);

  const mergesCard = document.createElement("div");
  mergesCard.className = "foundation-bpe-card";
  const mergesLabel = document.createElement("span");
  mergesLabel.className = "foundation-bpe-label";
  mergesLabel.textContent = "Learned merges";
  mergesCard.appendChild(mergesLabel);
  const mergeList = document.createElement("div");
  mergeList.className = "foundation-merge-list";
  (foundation.bpe?.learned_merges || []).forEach((entry) => {
    const row = document.createElement("div");
    row.className = "foundation-merge-row";
    row.textContent = entry;
    mergeList.appendChild(row);
  });
  if (!(foundation.bpe?.learned_merges || []).length) {
    const empty = document.createElement("div");
    empty.className = "foundation-empty";
    empty.textContent = "No merges have been learned yet.";
    mergeList.appendChild(empty);
  }
  mergesCard.appendChild(mergeList);
  bpeGrid.appendChild(mergesCard);

  bpeSection.appendChild(bpeGrid);
  shell.appendChild(bpeSection);

  panel.appendChild(shell);
}

function renderFoundationTextPanel(data) {
  const panel = $("foundation-text-panel");
  panel.innerHTML = "";
  const foundation = data.foundation_models;
  if (!foundation) return;

  const shell = document.createElement("div");
  shell.className = "foundation-shell";

  const inputSection = document.createElement("section");
  inputSection.className = "foundation-section";
  const inputHeading = document.createElement("h3");
  inputHeading.className = "foundation-section-title";
  inputHeading.textContent = foundation.custom_text_active ? "Custom text" : "Current text";
  const inputCopy = document.createElement("p");
  inputCopy.className = "foundation-copy";
  inputCopy.textContent =
    foundation.mode === "bpe"
      ? "The replay stepper follows the learned BPE merge process for the selected corpus. Edit the text and apply it to compare how the same merges behave on a new input."
      : "Edit the text and apply it to compare how different tokenisers segment the same visible string.";
  const textarea = document.createElement("textarea");
  textarea.id = "foundation-textarea";
  textarea.className = "foundation-textarea";
  textarea.value = foundation.text || "";
  textarea.spellcheck = false;
  const actions = document.createElement("div");
  actions.className = "foundation-text-actions";
  const applyButton = document.createElement("button");
  applyButton.type = "button";
  applyButton.dataset.foundationAction = "apply-text";
  applyButton.textContent = "Apply text";
  const resetButton = document.createElement("button");
  resetButton.type = "button";
  resetButton.className = "secondary-button";
  resetButton.dataset.foundationAction = "reset-text";
  resetButton.textContent = "Reset to example";
  actions.append(applyButton, resetButton);
  inputSection.append(inputHeading, inputCopy, textarea, actions);
  shell.appendChild(inputSection);

  const overlaySection = document.createElement("section");
  overlaySection.className = "foundation-section";
  const overlayHeading = document.createElement("h3");
  overlayHeading.className = "foundation-section-title";
  overlayHeading.textContent = "Token boundary overlay";
  overlaySection.appendChild(overlayHeading);
  const stream = document.createElement("div");
  stream.className = "foundation-token-stream";
  (foundation.overlay_segments || []).forEach((segment) => {
    if (segment.kind === "whitespace") {
      const space = document.createElement("span");
      space.className = "foundation-space";
      space.textContent = segment.text;
      stream.appendChild(space);
      return;
    }
    const chip = document.createElement("span");
    chip.className = `foundation-token-chip${foundation.mode === "bpe" ? " active" : ""}`;
    chip.textContent = segment.text;
    stream.appendChild(chip);
  });
  overlaySection.appendChild(stream);
  shell.appendChild(overlaySection);

  panel.appendChild(shell);
}

function renderStripsWorld(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  const world = data.planning?.world;
  if (!world?.rooms?.length) return;

  const roomBoxes = {
    mail_room: { x: 90, y: 90, width: 220, height: 110 },
    office_a: { x: 690, y: 90, width: 220, height: 110 },
    corridor: { x: 390, y: 280, width: 220, height: 110 },
    office_b: { x: 90, y: 500, width: 220, height: 110 },
    lab: { x: 690, y: 500, width: 220, height: 110 },
  };
  const roomCenters = Object.fromEntries(
    Object.entries(roomBoxes).map(([room, box]) => [
      room,
      { x: box.x + box.width / 2, y: box.y + box.height / 2 },
    ])
  );

  const connectors = $svgNode("g");
  const rooms = $svgNode("g");
  const entities = $svgNode("g");

  [
    ["corridor", "mail_room"],
    ["corridor", "office_a"],
    ["corridor", "office_b"],
    world.door_edge,
  ].forEach(([left, right]) => {
    const from = roomCenters[left];
    const to = roomCenters[right];
    connectors.appendChild(
      $svgNode("line", {
        class: `planning-connector${left === world.door_edge[0] && right === world.door_edge[1] && world.door_locked ? " locked" : ""}`,
        x1: from.x,
        y1: from.y,
        x2: to.x,
        y2: to.y,
      })
    );
  });

  const [doorLeft, doorRight] = world.door_edge;
  const doorFrom = roomCenters[doorLeft];
  const doorTo = roomCenters[doorRight];
  const doorX = (doorFrom.x + doorTo.x) / 2;
  const doorY = (doorFrom.y + doorTo.y) / 2;
  connectors.appendChild(
    $svgNode("rect", {
      class: `planning-door-body${world.door_locked ? " locked" : ""}`,
      x: doorX - 34,
      y: doorY - 18,
      width: 68,
      height: 36,
      rx: 12,
    })
  );
  connectors.appendChild(
    $svgNode(
      "text",
      {
        class: "planning-door-label",
        x: doorX,
        y: doorY + 4,
      },
      world.door_locked ? "locked" : "open"
    )
  );

  world.rooms.forEach((room) => {
    const box = roomBoxes[room];
    rooms.appendChild(
      $svgNode("rect", {
        class: `planning-room${world.robot_room === room ? " active" : ""}`,
        x: box.x,
        y: box.y,
        width: box.width,
        height: box.height,
        rx: 22,
      })
    );
    rooms.appendChild(
      $svgNode(
        "text",
        {
          class: "planning-room-label",
          x: box.x + box.width / 2,
          y: box.y + 64,
        },
        room.replace("_", " ")
      )
    );
  });

  function appendEntity(room, label, cssClass, dx, dy) {
    const centre = roomCenters[room];
    const group = $svgNode("g", {
      transform: `translate(${centre.x + dx}, ${centre.y + dy})`,
    });
    group.appendChild($svgNode("circle", { class: cssClass, r: 24 }));
    group.appendChild($svgNode("text", { class: "planning-entity-label" }, label));
    entities.appendChild(group);
  }

  if (world.parcel_room) appendEntity(world.parcel_room, "P", "planning-entity-parcel", -58, 26);
  if (world.keycard_room) appendEntity(world.keycard_room, "K", "planning-entity-keycard", 58, 26);
  if (world.robot_room) {
    appendEntity(world.robot_room, "R", "planning-entity-robot", 0, -12);
    const centre = roomCenters[world.robot_room];
    if (world.parcel_carried) {
      entities.appendChild($svgNode("circle", { class: "planning-badge", cx: centre.x + 28, cy: centre.y - 34, r: 12 }));
      entities.appendChild($svgNode("text", { class: "planning-badge-text", x: centre.x + 28, y: centre.y - 30 }, "P"));
    }
    if (world.robot_has_keycard) {
      entities.appendChild($svgNode("circle", { class: "planning-badge", cx: centre.x - 28, cy: centre.y - 34, r: 12 }));
      entities.appendChild($svgNode("text", { class: "planning-badge-text", x: centre.x - 28, y: centre.y - 30 }, "K"));
    }
  }

  svg.appendChild(connectors);
  svg.appendChild(rooms);
  svg.appendChild(entities);
}

function uncertaintyRoomBoxes() {
  return {
    mail_room: { x: 90, y: 90, width: 220, height: 110 },
    office_a: { x: 690, y: 90, width: 220, height: 110 },
    corridor: { x: 390, y: 280, width: 220, height: 110 },
    office_b: { x: 90, y: 500, width: 220, height: 110 },
    lab: { x: 690, y: 500, width: 220, height: 110 },
  };
}

function uncertaintyFeatureTokens(room) {
  const tokens = [];
  if (room.charger) tokens.push("charger");
  if (room.window) tokens.push("window");
  if (room.door_nearby) tokens.push("door");
  if (room.marker && room.marker !== "none") tokens.push(`${room.marker} marker`);
  return tokens.length ? tokens : ["no strong cue"];
}

function humaniseUncertaintyText(value) {
  if (!value) return "none";
  return String(value).replace(/^move_to_/, "move to ").replace(/_/g, " ");
}

function renderUncertaintyInternal(data) {
  const panel = $("uncertainty-panel");
  panel.innerHTML = "";
  const uncertainty = data.uncertainty;
  if (!uncertainty) return;

  const shell = document.createElement("div");
  shell.className = "uncertainty-shell";

  const beliefSection = document.createElement("section");
  beliefSection.className = "uncertainty-section";
  const beliefHeading = document.createElement("h3");
  beliefHeading.className = "uncertainty-section-title";
  beliefHeading.textContent = "Current belief distribution";
  beliefSection.appendChild(beliefHeading);
  const beliefGrid = document.createElement("div");
  beliefGrid.className = "uncertainty-belief-grid";
  (uncertainty.belief_rows || []).forEach((row) => {
    const card = document.createElement("div");
    card.className = `uncertainty-belief-card${uncertainty.most_likely_location === row.location ? " active" : ""}`;
    const heading = document.createElement("div");
    heading.className = "uncertainty-belief-heading";
    const label = document.createElement("strong");
    label.textContent = row.label;
    const probability = document.createElement("span");
    probability.textContent = `${Math.round(row.posterior * 100)}%`;
    heading.append(label, probability);
    const bar = document.createElement("div");
    bar.className = "uncertainty-belief-bar";
    const fill = document.createElement("span");
    fill.style.width = `${Math.max(6, row.posterior * 100)}%`;
    bar.appendChild(fill);
    const meta = document.createElement("div");
    meta.className = "uncertainty-belief-meta";
    meta.textContent = `prior ${row.prior.toFixed(2)}  posterior ${row.posterior.toFixed(2)}`;
    card.append(heading, bar, meta);
    beliefGrid.appendChild(card);
  });
  beliefSection.appendChild(beliefGrid);
  shell.appendChild(beliefSection);

  const updateSection = document.createElement("section");
  updateSection.className = "uncertainty-section";
  const updateHeading = document.createElement("h3");
  updateHeading.className = "uncertainty-section-title";
  updateHeading.textContent = "Bayes update trace";
  updateSection.appendChild(updateHeading);
  const table = document.createElement("div");
  table.className = "uncertainty-update-table";
  [
    "Room",
    "Prior",
    "Predicted",
    "Likelihood",
    "Posterior",
  ].forEach((text) => {
    const cell = document.createElement("span");
    cell.className = "uncertainty-update-header";
    cell.textContent = text;
    table.appendChild(cell);
  });
  (uncertainty.belief_rows || []).forEach((row) => {
    const label = document.createElement("span");
    label.className = "uncertainty-update-label";
    label.textContent = row.label;
    table.appendChild(label);
    [row.prior, row.predicted, row.likelihood, row.posterior].forEach((value) => {
      const cell = document.createElement("span");
      cell.className = "uncertainty-update-value";
      cell.textContent = Number(value).toFixed(2);
      table.appendChild(cell);
    });
  });
  updateSection.appendChild(table);
  const normaliser = document.createElement("p");
  normaliser.className = "uncertainty-note";
  normaliser.textContent = `Normalisation constant: ${Number(uncertainty.normalisation_constant || 0).toFixed(3)}`;
  updateSection.appendChild(normaliser);
  shell.appendChild(updateSection);

  const transitionSection = document.createElement("section");
  transitionSection.className = "uncertainty-section";
  const transitionHeading = document.createElement("h3");
  transitionHeading.className = "uncertainty-section-title";
  transitionHeading.textContent = "Transition model";
  transitionSection.appendChild(transitionHeading);
  const transitionCopy = document.createElement("p");
  transitionCopy.className = "uncertainty-copy";
  transitionCopy.textContent = uncertainty.current_action
    ? `Current action: ${humaniseUncertaintyText(uncertainty.current_action)}. Each row shows how that action redistributes belief mass from one source room.`
    : "No action has been applied yet. Step the replay to see the prediction phase.";
  transitionSection.appendChild(transitionCopy);
  const transitionGrid = document.createElement("div");
  transitionGrid.className = "uncertainty-transition-grid";
  (uncertainty.transition_rows || []).forEach((row) => {
    const card = document.createElement("div");
    card.className = "uncertainty-transition-card";
    const label = document.createElement("strong");
    label.className = "uncertainty-transition-label";
    label.textContent = row.label;
    const entries = document.createElement("div");
    entries.className = "uncertainty-transition-list";
    row.entries.forEach((entry) => {
      const line = document.createElement("span");
      line.textContent = `${entry.label} ${Number(entry.probability).toFixed(2)}`;
      entries.appendChild(line);
    });
    card.append(label, entries);
    transitionGrid.appendChild(card);
  });
  if (!(uncertainty.transition_rows || []).length) {
    const empty = document.createElement("p");
    empty.className = "planning-empty";
    empty.textContent = "Transition rows appear after the first action.";
    transitionSection.appendChild(empty);
  } else {
    transitionSection.appendChild(transitionGrid);
  }
  shell.appendChild(transitionSection);

  const historySection = document.createElement("section");
  historySection.className = "uncertainty-section";
  const historyHeading = document.createElement("h3");
  historyHeading.className = "uncertainty-section-title";
  historyHeading.textContent = "Filtering history";
  historySection.appendChild(historyHeading);
  const historyList = document.createElement("div");
  historyList.className = "uncertainty-history-list";
  (uncertainty.history || []).forEach((entry) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `uncertainty-history-button${entry.step_index === uncertainty.step_index ? " current" : ""}`;
    button.dataset.stepIndex = String(entry.step_index);
    const label = document.createElement("strong");
    label.textContent = `Step ${entry.step_index}`;
    const meta = document.createElement("span");
    meta.textContent =
      `${humaniseUncertaintyText(entry.action)}  |  ${humaniseUncertaintyText(entry.observation)}  |  peak ${humaniseUncertaintyText(entry.most_likely_location)}`;
    button.append(label, meta);
    historyList.appendChild(button);
  });
  if (!(uncertainty.history || []).length) {
    const empty = document.createElement("p");
    empty.className = "planning-empty";
    empty.textContent = "The history will appear once the first Bayes-filter step has been replayed.";
    historySection.appendChild(empty);
  } else {
    historySection.appendChild(historyList);
  }
  shell.appendChild(historySection);

  panel.appendChild(shell);
}

function renderUncertaintyWorldPanel(data) {
  const panel = $("uncertainty-world-panel");
  panel.innerHTML = "";
  const uncertainty = data.uncertainty;
  if (!uncertainty) return;
  const problem = state.session?.data?.uncertainty_problem || data.uncertainty_problem || {};

  const shell = document.createElement("div");
  shell.className = "uncertainty-shell";

  const currentSection = document.createElement("section");
  currentSection.className = "uncertainty-section";
  const currentHeading = document.createElement("h3");
  currentHeading.className = "uncertainty-section-title";
  currentHeading.textContent = "Current action and observation";
  const summaryGrid = document.createElement("div");
  summaryGrid.className = "uncertainty-world-summary";
  [
    {
      label: "Action",
      value: uncertainty.current_action ? humaniseUncertaintyText(uncertainty.current_action) : "none yet",
    },
    {
      label: "Observation",
      value: uncertainty.current_observation ? humaniseUncertaintyText(uncertainty.current_observation) : "none yet",
    },
    {
      label: "True location",
      value: state.view.showTrueLocation
        ? humaniseUncertaintyText(uncertainty.current_true_location)
        : "hidden",
    },
  ].forEach((item) => {
    const card = document.createElement("div");
    card.className = "uncertainty-world-card";
    const label = document.createElement("span");
    label.className = "uncertainty-world-label";
    label.textContent = item.label;
    const value = document.createElement("strong");
    value.textContent = item.value;
    card.append(label, value);
    summaryGrid.appendChild(card);
  });
  currentSection.append(currentHeading, summaryGrid);
  shell.appendChild(currentSection);

  const cuesSection = document.createElement("section");
  cuesSection.className = "uncertainty-section";
  const cuesHeading = document.createElement("h3");
  cuesHeading.className = "uncertainty-section-title";
  cuesHeading.textContent = "Room cues";
  const cuesGrid = document.createElement("div");
  cuesGrid.className = "uncertainty-cue-grid";
  (uncertainty.rooms || []).forEach((room) => {
    const card = document.createElement("div");
    card.className = "uncertainty-cue-card";
    const label = document.createElement("strong");
    label.textContent = room.label;
    const features = document.createElement("div");
    features.className = "uncertainty-cue-list";
    uncertaintyFeatureTokens(room).forEach((token) => {
      const chip = document.createElement("span");
      chip.className = "uncertainty-cue-chip";
      chip.textContent = token;
      features.appendChild(chip);
    });
    card.append(label, features);
    cuesGrid.appendChild(card);
  });
  cuesSection.append(cuesHeading, cuesGrid);
  shell.appendChild(cuesSection);

  const scenarioSection = document.createElement("section");
  scenarioSection.className = "uncertainty-section";
  const scenarioHeading = document.createElement("h3");
  scenarioHeading.className = "uncertainty-section-title";
  scenarioHeading.textContent = "Scenario sequence";
  const scenarioList = document.createElement("div");
  scenarioList.className = "uncertainty-history-list";
  (problem.scripted_steps || []).forEach((step, index) => {
    const replayIndex = index + 1;
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.stepIndex = String(replayIndex);
    const stateClass =
      replayIndex === uncertainty.step_index
        ? " current"
        : replayIndex < uncertainty.step_index
        ? " completed"
        : "";
    button.className = `uncertainty-history-button${stateClass}`;
    const label = document.createElement("strong");
    label.textContent = `Step ${replayIndex}`;
    const meta = document.createElement("span");
    meta.textContent = `${humaniseUncertaintyText(step.action)}  |  ${humaniseUncertaintyText(step.observation)}`;
    button.append(label, meta);
    scenarioList.appendChild(button);
  });
  scenarioSection.append(scenarioHeading, scenarioList);
  shell.appendChild(scenarioSection);

  panel.appendChild(shell);
}

function renderUncertaintyWorld(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  const uncertainty = data.uncertainty;
  if (!uncertainty?.rooms?.length) return;

  const roomBoxes = uncertaintyRoomBoxes();
  const roomCentres = Object.fromEntries(
    Object.entries(roomBoxes).map(([room, box]) => [
      room,
      { x: box.x + box.width / 2, y: box.y + box.height / 2 },
    ])
  );
  const connectors = $svgNode("g");
  const roomBases = $svgNode("g");
  const overlays = $svgNode("g");
  const roomLabels = $svgNode("g");
  const entities = $svgNode("g");

  (uncertainty.connections || []).forEach(([left, right]) => {
    const from = roomCentres[left];
    const to = roomCentres[right];
    connectors.appendChild(
      $svgNode("line", {
        class: "uncertainty-connector",
        x1: from.x,
        y1: from.y,
        x2: to.x,
        y2: to.y,
      })
    );
  });

  (uncertainty.rooms || []).forEach((room) => {
    const box = roomBoxes[room.id];
    const probability = Number(uncertainty.posterior_belief?.[room.id] || 0);
    roomBases.appendChild(
      $svgNode("rect", {
        class: `uncertainty-room${uncertainty.most_likely_location === room.id ? " active" : ""}`,
        x: box.x,
        y: box.y,
        width: box.width,
        height: box.height,
        rx: 22,
      })
    );
    overlays.appendChild(
      $svgNode("rect", {
        class: "uncertainty-room-overlay",
        x: box.x + 6,
        y: box.y + 6,
        width: box.width - 12,
        height: box.height - 12,
        rx: 18,
        style: `opacity: ${0.08 + probability * 0.72};`,
      })
    );
    roomLabels.appendChild(
      $svgNode(
        "text",
        {
          class: "uncertainty-room-label",
          x: box.x + box.width / 2,
          y: box.y + 38,
        },
        room.label
      )
    );
    roomLabels.appendChild(
      $svgNode(
        "text",
        {
          class: "uncertainty-room-probability",
          x: box.x + box.width / 2,
          y: box.y + 64,
        },
        `${Math.round(probability * 100)}% belief`
      )
    );
    const features = uncertaintyFeatureTokens(room);
    features.slice(0, 2).forEach((token, index) => {
      roomLabels.appendChild(
        $svgNode(
          "text",
          {
            class: "uncertainty-room-feature",
            x: box.x + box.width / 2,
            y: box.y + 86 + index * 18,
          },
          token
        )
      );
    });
    roomLabels.appendChild(
      $svgNode("rect", {
        class: "uncertainty-room-bar",
        x: box.x + 20,
        y: box.y + box.height - 18,
        width: (box.width - 40) * probability,
        height: 8,
        rx: 4,
      })
    );
  });

  if (state.view.showTrueLocation && uncertainty.current_true_location) {
    const centre = roomCentres[uncertainty.current_true_location];
    const group = $svgNode("g", {
      transform: `translate(${centre.x}, ${centre.y - 6})`,
    });
    group.appendChild($svgNode("circle", { class: "uncertainty-robot", r: 24 }));
    group.appendChild($svgNode("text", { class: "uncertainty-robot-label" }, "R"));
    entities.appendChild(group);
  }

  svg.append(connectors, roomBases, overlays, roomLabels, entities);
}

function renderControls() {
  const livePythonApp = isLivePythonApp();
  const generatedProblemApp =
    livePythonApp && !isLogic() && !isStrips() && !isUncertainty() && !isCspFamily() && !isFoundationModels();
  $("example-control-label").textContent = generatedProblemApp ? "Configuration" : "Example";
  $("size-control-label").textContent = isLabyrinth() ? "Labyrinth size" : "Graph size";
  $("generate-button").textContent = isLabyrinth() ? "Generate new labyrinth" : "Generate new graph";
  $("mode-control").classList.toggle("hidden", !livePythonApp);
  $("logic-mode-control").classList.toggle("hidden", !isLogic());
  $("logic-order-control").classList.toggle("hidden", !isLogic());
  $("foundation-mode-control").classList.toggle("hidden", !isFoundationModels());
  $("foundation-corpus-control").classList.toggle("hidden", !isFoundationModels());
  $("foundation-merges-control").classList.toggle("hidden", !isFoundationModels());
  $("foundation-context-control").classList.toggle("hidden", !isFoundationModels());
  $("csp-algorithm-control").classList.toggle("hidden", !isCspFamily());
  $("csp-variable-order-control").classList.toggle("hidden", !isCspFamily());
  $("csp-value-order-control").classList.toggle("hidden", !isCspFamily());
  $("csp-colour-control").classList.toggle("hidden", !isCsp());
  $("csp-view-control").classList.toggle("hidden", !isCspFamily());
  $("planning-toggle-grid").classList.toggle("hidden", !isStrips());
  $("uncertainty-toggle-grid").classList.toggle("hidden", !isUncertainty());
  $("csp-toggle-grid").classList.toggle("hidden", !isCspFamily());
  $("size-control").classList.toggle("hidden", !generatedProblemApp);
  $("seed-control").classList.toggle("hidden", !generatedProblemApp);
  $("generate-button").classList.toggle("hidden", !generatedProblemApp);
  $("solve-python-button").classList.toggle("hidden", !livePythonApp);
  $("download-stub-button").classList.toggle("hidden", !livePythonApp);
  $("reload-button").classList.toggle(
    "hidden",
    livePythonApp && !isStrips() && !isUncertainty() && !isLogic() && !isCspFamily()
  );
  $("search-toggle-grid").classList.toggle("hidden", !isWeightedGraphSearch());
  $("logic-toggle-grid").classList.toggle("hidden", !isLogic());
  $("search-legend").classList.toggle("hidden", !isWeightedGraphSearch());
  $("labyrinth-legend").classList.toggle("hidden", !isLabyrinth());
  $("graph-dfs-legend").classList.toggle("hidden", !isGraphReachability());
  $("logic-legend").classList.toggle("hidden", !isLogic());
  $("csp-legend").classList.toggle("hidden", !isCspFamily());
  $("uncertainty-legend").classList.toggle("hidden", !isUncertainty());
}

function render() {
  const trace = currentTrace();
  const data = currentData();
  const step = currentStep();
  const max = maxStepCount();

  $("app-title").textContent = state.manifest.app_title;
  $("app-subtitle").textContent =
    data.example_subtitle || state.session.data.example_subtitle || state.session.example_name || "default";
  $("mode-badge").textContent = state.manifest.mode;
  $("execution-badge").textContent = isLivePythonApp() ? state.player.mode : state.manifest.execution_mode;
  $("algorithm-badge").textContent = data.algorithm_label || "search replay";
  $("status-value").textContent = statusLabel(data, step);
  $("step-event").textContent = step.event_type || "initialise";
  $("step-label").textContent = step.label;
  $("step-annotation").textContent = step.annotation || "";
  $("step-note").textContent = step.teaching_note || "";
  $("step-range").max = String(max);
  $("step-range").value = String(state.player.stepIndex);
  $("step-readout").textContent = `${state.player.stepIndex} / ${max}`;
  $("previous-button").disabled = state.player.stepIndex === 0;
  $("next-button").disabled = state.player.stepIndex >= max;
  $("play-button").disabled = max === 0;
  $("pause-button").disabled = !state.playTimer;
  renderPanelCopy(data);
  renderMetrics(data);
  renderControls();

  const banner = $("message-banner");
  if (state.player.message) {
    banner.textContent = state.player.message;
    banner.classList.remove("hidden");
  } else {
    banner.textContent = "";
    banner.classList.add("hidden");
  }

  $("search-tree-svg").classList.toggle("hidden", isStrips() || isUncertainty() || isCspFamily() || isFoundationModels());
  $("csp-panel").classList.toggle("hidden", !isCspFamily());
  $("planning-panel").classList.toggle("hidden", !isStrips());
  $("uncertainty-panel").classList.toggle("hidden", !isUncertainty());
  $("planning-world-panel").classList.toggle("hidden", !isStrips());
  $("uncertainty-world-panel").classList.toggle("hidden", !isUncertainty());
  $("foundation-panel").classList.toggle("hidden", !isFoundationModels());
  if (isCsp()) {
    renderCspPanel(data);
  } else if (isDeliveryCsp()) {
    renderDeliveryCspPanel(data);
  } else if (isUncertainty()) {
    renderUncertaintyInternal(data);
    renderUncertaintyWorldPanel(data);
  } else if (isStrips()) {
    renderPlanningInternal(data);
    renderPlanningWorldPanel(data);
  } else if (isFoundationModels()) {
    renderFoundationInternal(data);
  } else {
    renderTree(data);
  }
  $("problem-svg").classList.toggle("hidden", isLogic() || isFoundationModels());
  $("problem-svg").classList.toggle("delivery-world-canvas", isDeliveryCsp());
  if (!isDeliveryCsp()) {
    $("problem-svg").setAttribute("viewBox", "0 0 1000 700");
  }
  $("logic-problem-panel").classList.toggle("hidden", !isLogic());
  $("foundation-text-panel").classList.toggle("hidden", !isFoundationModels());
  if (isLogic()) {
    renderLogicProblem(data);
  } else if (isFoundationModels()) {
    renderFoundationTextPanel(data);
  } else if (isCsp()) {
    renderCspMap(data);
  } else if (isDeliveryCsp()) {
    renderDeliverySchedule(data);
  } else if (isUncertainty()) {
    renderUncertaintyWorld(data);
  } else if (isStrips()) {
    renderStripsWorld(data);
  } else if (isLabyrinth()) {
    renderLabyrinth(data);
  } else if (isGraphReachability()) {
    renderGraphReachability(data);
  } else {
    renderWeightedGraph(data);
  }
}

function startPlay() {
  stopPlay();
  state.playTimer = window.setInterval(() => {
    if (state.player.stepIndex >= maxStepCount()) {
      stopPlay();
      render();
      return;
    }
    state.player.stepIndex += 1;
    render();
  }, playIntervalMs());
  render();
}

async function refreshFromServer(response) {
  state.session = response.state || state.session;
  state.serverTrace = response.trace || state.serverTrace;
  state.serverSnapshots = buildSnapshots(state.serverTrace);
  state.player.stepIndex = 0;
  state.player.liveTrace = null;
  state.player.liveSnapshots = [];
  state.view.planningSelectedAction = "";
  if (state.session.data.live_python) {
    state.player.size = state.session.data.live_python.size;
    state.player.seed = state.session.data.live_python.seed;
  }
  const examplesPayload = await requestJson("/api/examples");
  populateExamples(examplesPayload.examples || []);
  syncControls();
  render();
}

async function loadExample(name) {
  stopPlay();
  setMessage("");
  state.view.planningSelectedAction = "";
  const response = await postAction("load_example", { name });
  const trace = await requestJson("/api/trace");
  response.trace = trace;
  state.player.mode = "playback";
  await refreshFromServer(response);
}

async function generateLabyrinth() {
  stopPlay();
  setMessage("Generating a new solvable labyrinth.");
  render();
  const rawSeed = $("seed-input").value.trim();
  const payload = {
    command: "generate_labyrinth",
    size: $("size-select").value,
  };
  if (rawSeed) {
    payload.seed = Number(rawSeed);
  }
  const response = await postAction("app_command", payload);
  const trace = await requestJson("/api/trace");
  response.trace = trace;
  state.player.mode = "playback";
  await refreshFromServer(response);
  setMessage("Generated a new labyrinth. Playback is ready, and you can switch to live Python mode to compare it with your own solver.");
  render();
}

async function generateGraph() {
  stopPlay();
  setMessage(
    isWeightedGraphSearch() ? "Generating a new weighted graph." : "Generating a new sparse graph."
  );
  render();
  const rawSeed = $("seed-input").value.trim();
  const payload = {
    command: "generate_graph",
    size: $("size-select").value,
  };
  if (rawSeed) {
    payload.seed = Number(rawSeed);
  }
  const response = await postAction("app_command", payload);
  const trace = await requestJson("/api/trace");
  response.trace = trace;
  state.player.mode = "playback";
  await refreshFromServer(response);
  setMessage(
    isWeightedGraphSearch()
      ? "Generated a new weighted graph. Playback is ready, and you can switch to live Python mode to compare it with your own solver."
      : "Generated a new graph. Playback is ready, and you can switch to live Python mode to compare it with your own solver."
  );
  render();
}

async function solveWithPython() {
  stopPlay();
  setMessage("");
  render();
  const backendUrl = state.session.data.live_python?.backend_url || "http://127.0.0.1:9414/solve";
  const logicProblem =
    state.session.data.logic_problem ||
    state.session.data.problem || {
      mode: state.session.data.problem_mode || "sat",
      title: state.session.data.example_title || "Visual DPLL",
      subtitle: state.session.data.example_subtitle || "",
      variables: state.session.data.logic?.variables || [],
      clauses: (state.session.data.logic?.clauses || []).map((clause) =>
        (clause.literals || []).map((literal) => literal.raw)
      ),
      kb_formulas: state.session.data.logic?.kb_formulas || [],
      query: state.session.data.logic?.query || null,
      entailment_target: state.session.data.logic?.entailment_target || null,
      original_input: state.session.data.logic?.original_input || [],
    };
  const problemPayload = isLogic()
    ? {
        algorithm: "dpll",
        problem: logicProblem,
        options: clone(state.session.data.options || {}),
      }
    : isUncertainty()
    ? {
        algorithm: "bayes_filter",
        problem: clone(state.session.data.uncertainty_problem),
      }
    : isCsp()
    ? {
        algorithm: "backtracking_forward_checking",
        problem: clone(state.session.data.csp_problem),
        options: clone(state.session.data.options || {}),
      }
    : isDeliveryCsp()
    ? {
        algorithm: "backtracking_forward_checking",
        problem: clone(state.session.data.delivery_problem),
        options: clone(state.session.data.options || {}),
      }
    : isStrips()
    ? {
        algorithm: "strips_bfs",
        problem: clone(state.session.data.strips_problem),
      }
    : isLabyrinth()
    ? { algorithm: "dfs", labyrinth: state.session.data.labyrinth }
    : {
        algorithm: isWeightedSearch()
          ? "dfbb"
          : isGraphAStar()
            ? "astar"
          : isGraphGbfs()
            ? "gbfs"
            : isGraphUcs()
              ? "ucs"
              : isGraphBfs()
                ? "bfs"
                : "dfs",
        graph: state.session.data.graph,
      };
  const problemData = isLogic()
    ? logicProblem
    : isUncertainty()
      ? state.session.data.uncertainty_problem
    : isCsp()
      ? state.session.data.csp_problem
    : isDeliveryCsp()
      ? state.session.data.delivery_problem
    : isStrips()
      ? state.session.data.strips_problem
    : isLabyrinth()
      ? state.session.data.labyrinth
      : state.session.data.graph;

  try {
    const response = await fetch(backendUrl, {
      method: "POST",
      mode: "cors",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(problemPayload),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload?.message || "Python backend returned an error.");
    }
    state.player.liveTrace = isLogic()
      ? buildLogicTraceFromBackend(problemData, payload)
      : isUncertainty()
      ? payload.trace_bundle
      : isCsp()
      ? payload.trace_bundle
      : isDeliveryCsp()
      ? payload.trace_bundle
      : isStrips()
      ? payload.trace_bundle
      : isLabyrinth()
      ? buildLabyrinthTraceFromBackend(problemData, payload)
      : isWeightedSearch()
        ? buildSearchTraceFromBackend(problemData, payload)
      : isGraphAStar()
        ? buildGraphAStarTraceFromBackend(problemData, payload)
      : isGraphGbfs()
        ? buildGraphGbfsTraceFromBackend(problemData, payload)
      : isGraphUcs()
        ? buildGraphUcsTraceFromBackend(problemData, payload)
      : isGraphBfs()
        ? buildGraphBfsTraceFromBackend(problemData, payload)
        : buildGraphDfsTraceFromBackend(problemData, payload);
    state.player.liveSnapshots = buildSnapshots(state.player.liveTrace);
    state.player.stepIndex = 0;
    state.player.mode = "live";
    state.view.planningSelectedAction = "";
    syncControls();
    render();
  } catch (error) {
    let message = "Python backend not reachable. Start the local solver and try again.";
    if (
      error instanceof Error &&
      error.message &&
      !["Failed to fetch", "Load failed", "NetworkError when attempting to fetch resource."].includes(error.message)
    ) {
      message = error.message;
    }
    setMessage(message);
    render();
  }
}

function downloadPythonStub() {
  const archive = createZipArchive(
    isLogic()
      ? [
          { name: "ai9414/solve_dpll.py", content: DPLL_PYTHON_STUB },
          { name: "ai9414/requirements.txt", content: DPLL_PYTHON_REQUIREMENTS },
          { name: "ai9414/README.md", content: DPLL_PYTHON_README },
        ]
      : isUncertainty()
      ? [
          { name: "ai9414/solve_uncertainty.py", content: UNCERTAINTY_PYTHON_STUB },
          { name: "ai9414/requirements.txt", content: UNCERTAINTY_PYTHON_REQUIREMENTS },
          { name: "ai9414/README.md", content: UNCERTAINTY_PYTHON_README },
        ]
      : isCsp()
      ? [
          { name: "ai9414/solve_csp.py", content: CSP_PYTHON_STUB },
          { name: "ai9414/requirements.txt", content: CSP_PYTHON_REQUIREMENTS },
          { name: "ai9414/README.md", content: CSP_PYTHON_README },
        ]
      : isDeliveryCsp()
      ? [
          { name: "ai9414/solve_delivery_csp.py", content: DELIVERY_CSP_PYTHON_STUB },
          { name: "ai9414/requirements.txt", content: DELIVERY_CSP_PYTHON_REQUIREMENTS },
          { name: "ai9414/README.md", content: DELIVERY_CSP_PYTHON_README },
        ]
      : isStrips()
      ? [
          { name: "ai9414/solve_strips.py", content: STRIPS_PYTHON_STUB },
          { name: "ai9414/requirements.txt", content: STRIPS_PYTHON_REQUIREMENTS },
          { name: "ai9414/README.md", content: STRIPS_PYTHON_README },
        ]
      : isWeightedSearch()
      ? [
          { name: "ai9414/solve_weighted_graph.py", content: WEIGHTED_GRAPH_PYTHON_STUB },
          { name: "ai9414/requirements.txt", content: WEIGHTED_GRAPH_PYTHON_REQUIREMENTS },
          { name: "ai9414/README.md", content: WEIGHTED_GRAPH_PYTHON_README },
        ]
      : isGraphAStar()
        ? [
            { name: "ai9414/solve_graph.py", content: GRAPH_ASTAR_PYTHON_STUB },
            { name: "ai9414/requirements.txt", content: GRAPH_ASTAR_PYTHON_REQUIREMENTS },
            { name: "ai9414/README.md", content: GRAPH_ASTAR_PYTHON_README },
          ]
      : isGraphGbfs()
        ? [
            { name: "ai9414/solve_graph.py", content: GRAPH_GBFS_PYTHON_STUB },
            { name: "ai9414/requirements.txt", content: GRAPH_GBFS_PYTHON_REQUIREMENTS },
            { name: "ai9414/README.md", content: GRAPH_GBFS_PYTHON_README },
          ]
      : isGraphUcs()
        ? [
            { name: "ai9414/solve_graph.py", content: GRAPH_UCS_PYTHON_STUB },
            { name: "ai9414/requirements.txt", content: GRAPH_UCS_PYTHON_REQUIREMENTS },
            { name: "ai9414/README.md", content: GRAPH_UCS_PYTHON_README },
          ]
      : isGraphBfs()
      ? [
          { name: "ai9414/solve_graph.py", content: GRAPH_BFS_PYTHON_STUB },
          { name: "ai9414/requirements.txt", content: GRAPH_BFS_PYTHON_REQUIREMENTS },
          { name: "ai9414/README.md", content: GRAPH_BFS_PYTHON_README },
        ]
      : isGraphDfs()
      ? [
          { name: "ai9414/solve_graph.py", content: GRAPH_PYTHON_STUB },
          { name: "ai9414/requirements.txt", content: GRAPH_PYTHON_REQUIREMENTS },
          { name: "ai9414/README.md", content: GRAPH_PYTHON_README },
        ]
      : [
          { name: "ai9414/solve_labyrinth.py", content: PYTHON_STUB },
          { name: "ai9414/requirements.txt", content: PYTHON_REQUIREMENTS },
          { name: "ai9414/README.md", content: PYTHON_README },
        ]
  );
  const url = window.URL.createObjectURL(archive);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = isLogic()
    ? "logic-dpll-python-stub.zip"
    : isUncertainty()
    ? "uncertainty-bayes-filter-python-stub.zip"
    : isCsp()
    ? "csp-map-colouring-python-stub.zip"
    : isDeliveryCsp()
    ? "delivery-csp-python-stub.zip"
    : isStrips()
    ? "strips-planning-python-stub.zip"
    : isWeightedSearch()
    ? "weighted-graph-python-stub.zip"
    : isGraphAStar()
      ? "graph-astar-python-stub.zip"
    : isGraphGbfs()
      ? "graph-gbfs-python-stub.zip"
    : isGraphUcs()
      ? "graph-ucs-python-stub.zip"
    : isGraphBfs()
    ? "graph-bfs-python-stub.zip"
    : isGraphDfs()
      ? "graph-dfs-python-stub.zip"
      : "labyrinth-dfs-python-stub.zip";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
  setMessage(
    isLogic()
      ? "Downloaded logic-dpll-python-stub.zip."
      : isUncertainty()
      ? "Downloaded uncertainty-bayes-filter-python-stub.zip."
      : isCsp()
      ? "Downloaded csp-map-colouring-python-stub.zip."
      : isDeliveryCsp()
      ? "Downloaded delivery-csp-python-stub.zip."
      : isStrips()
      ? "Downloaded strips-planning-python-stub.zip."
      : isWeightedSearch()
      ? "Downloaded weighted-graph-python-stub.zip."
      : isGraphAStar()
        ? "Downloaded graph-astar-python-stub.zip."
      : isGraphGbfs()
        ? "Downloaded graph-gbfs-python-stub.zip."
      : isGraphUcs()
        ? "Downloaded graph-ucs-python-stub.zip."
      : isGraphBfs()
      ? "Downloaded graph-bfs-python-stub.zip."
      : isGraphDfs()
      ? "Downloaded graph-dfs-python-stub.zip."
      : "Downloaded labyrinth-dfs-python-stub.zip."
  );
  render();
}

async function updateLogicOptions(patch) {
  stopPlay();
  setMessage("");
  const response = await postAction("set_option", patch);
  const trace = await requestJson("/api/trace");
  response.trace = trace;
  await refreshFromServer(response);
}

async function updateCspOptions(patch) {
  stopPlay();
  setMessage("");
  const response = await postAction("set_option", patch);
  const trace = await requestJson("/api/trace");
  response.trace = trace;
  await refreshFromServer(response);
}

async function updateFoundationOptions(patch) {
  stopPlay();
  setMessage("");
  const response = await postAction("set_option", patch);
  const trace = await requestJson("/api/trace");
  response.trace = trace;
  await refreshFromServer(response);
}

async function applyFoundationText() {
  const textarea = $("foundation-textarea");
  if (!textarea) return;
  stopPlay();
  setMessage("");
  const response = await postAction("app_command", {
    command: "set_text",
    text: textarea.value,
  });
  const trace = await requestJson("/api/trace");
  response.trace = trace;
  await refreshFromServer(response);
}

async function resetFoundationText() {
  stopPlay();
  setMessage("");
  const response = await postAction("app_command", {
    command: "reset_text",
  });
  const trace = await requestJson("/api/trace");
  response.trace = trace;
  await refreshFromServer(response);
}

function bindEvents() {
  $("previous-button").addEventListener("click", () => {
    stopPlay();
    state.player.stepIndex = Math.max(state.player.stepIndex - 1, 0);
    state.view.planningSelectedAction = "";
    render();
  });
  $("next-button").addEventListener("click", () => {
    stopPlay();
    state.player.stepIndex = Math.min(state.player.stepIndex + 1, maxStepCount());
    state.view.planningSelectedAction = "";
    render();
  });
  $("play-button").addEventListener("click", () => startPlay());
  $("pause-button").addEventListener("click", () => {
    stopPlay();
    render();
  });
  $("reset-button").addEventListener("click", () => {
    stopPlay();
    state.player.stepIndex = 0;
    state.view.planningSelectedAction = "";
    render();
  });
  $("reload-button").addEventListener("click", async () => {
    if (!state.session.example_name) return;
    await loadExample(state.session.example_name);
  });
  $("example-select").addEventListener("change", async (event) => {
    if (isLivePythonApp() && !isLogic() && !isStrips() && !isUncertainty() && !isCspFamily()) {
      stopPlay();
      state.player.size = event.target.value;
      state.player.seed = "";
      $("size-select").value = state.player.size;
      $("seed-input").value = "";
      if (!isLabyrinth()) {
        await generateGraph();
      } else {
        await generateLabyrinth();
      }
      return;
    }
    await loadExample(event.target.value);
  });
  $("mode-select").addEventListener("change", (event) => {
    stopPlay();
    state.player.mode = event.target.value;
    state.player.stepIndex = 0;
    state.view.planningSelectedAction = "";
    if (state.player.mode === "playback") {
      setMessage("");
    } else if (!state.player.liveTrace) {
      setMessage(
        isLogic()
          ? "Live Python mode is ready. Run your local DPLL solver and replay the returned trace."
          : isUncertainty()
          ? "Live Python mode is ready. Run your local Bayes filter and replay the returned belief trace."
          : isCsp()
          ? "Live Python mode is ready. Run your local CSP solver and replay the returned trace."
          : isDeliveryCsp()
          ? "Live Python mode is ready. Run your local delivery CSP solver and replay the returned trace."
          : isStrips()
          ? "Live Python mode is ready. Run your local STRIPS planner and replay the returned plan."
          : !isLabyrinth()
          ? "Live Python mode is ready. Generate a graph or solve the current one with your backend."
          : "Live Python mode is ready. Generate a labyrinth or solve the current one with your backend."
      );
    }
    render();
  });
  $("logic-mode-select").addEventListener("change", async (event) => {
    await updateLogicOptions({ problem_mode: event.target.value });
  });
  $("logic-unit-propagation").addEventListener("change", async (event) => {
    await updateLogicOptions({ unit_propagation: event.target.checked });
  });
  $("logic-pure-literals").addEventListener("change", async (event) => {
    await updateLogicOptions({ pure_literals: event.target.checked });
  });
  $("logic-order-select").addEventListener("change", async (event) => {
    await updateLogicOptions({ variable_order: event.target.value });
  });
  $("foundation-mode-select").addEventListener("change", async (event) => {
    await updateFoundationOptions({ tokeniser_mode: event.target.value });
  });
  $("foundation-corpus-select").addEventListener("change", async (event) => {
    await updateFoundationOptions({ corpus: event.target.value });
  });
  $("foundation-merges-select").addEventListener("change", async (event) => {
    await updateFoundationOptions({ num_merges: Number(event.target.value) });
  });
  $("foundation-context-select").addEventListener("change", async (event) => {
    await updateFoundationOptions({ context_window: Number(event.target.value) });
  });
  $("csp-algorithm-select").addEventListener("change", async (event) => {
    await updateCspOptions({ algorithm: event.target.value });
  });
  $("csp-variable-order-select").addEventListener("change", async (event) => {
    await updateCspOptions({ variable_ordering: event.target.value });
  });
  $("csp-value-order-select").addEventListener("change", async (event) => {
    await updateCspOptions({ value_ordering: event.target.value });
  });
  $("csp-colour-select").addEventListener("change", async (event) => {
    await updateCspOptions({ num_colours: Number(event.target.value) });
  });
  $("csp-view-select").addEventListener("change", (event) => {
    state.view.cspViewMode = event.target.value;
    render();
  });
  $("size-select").addEventListener("change", (event) => {
    state.player.size = event.target.value;
  });
  $("seed-input").addEventListener("change", (event) => {
    state.player.seed = event.target.value;
  });
  $("speed-select").addEventListener("change", (event) => {
    state.view.playbackSpeed = Number(event.target.value);
  });
  $("show-explored").addEventListener("change", (event) => {
    state.view.showExploredEdges = event.target.checked;
    render();
  });
  $("show-pruned").addEventListener("change", (event) => {
    state.view.showPrunedBranches = event.target.checked;
    render();
  });
  $("show-planner-trace").addEventListener("change", (event) => {
    state.view.showPlannerTrace = event.target.checked;
    render();
  });
  $("show-true-location").addEventListener("change", (event) => {
    state.view.showTrueLocation = event.target.checked;
    render();
  });
  $("show-csp-domains").addEventListener("change", (event) => {
    state.view.showCspDomains = event.target.checked;
    render();
  });
  $("step-range").addEventListener("input", (event) => {
    stopPlay();
    state.player.stepIndex = Math.max(0, Math.min(Number(event.target.value), maxStepCount()));
    state.view.planningSelectedAction = "";
    render();
  });
  $("generate-button").addEventListener("click", async () => {
    if (!isLabyrinth()) {
      await generateGraph();
      return;
    }
    await generateLabyrinth();
  });
  $("solve-python-button").addEventListener("click", solveWithPython);
  $("download-stub-button").addEventListener("click", downloadPythonStub);
  $("planning-panel").addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    const { actionSignature, stepIndex } = target.dataset;
    if (actionSignature) {
      state.view.planningSelectedAction = actionSignature;
    }
    if (stepIndex) {
      stopPlay();
      state.player.stepIndex = Math.max(0, Math.min(Number(stepIndex), maxStepCount()));
    }
    render();
  });
  $("planning-world-panel").addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    const { actionSignature } = target.dataset;
    if (actionSignature) {
      state.view.planningSelectedAction = actionSignature;
    }
    render();
  });
  $("uncertainty-panel").addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    const { stepIndex } = target.dataset;
    if (!stepIndex) return;
    stopPlay();
    state.player.stepIndex = Math.max(0, Math.min(Number(stepIndex), maxStepCount()));
    render();
  });
  $("uncertainty-world-panel").addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    const { stepIndex } = target.dataset;
    if (!stepIndex) return;
    stopPlay();
    state.player.stepIndex = Math.max(0, Math.min(Number(stepIndex), maxStepCount()));
    render();
  });
  $("foundation-text-panel").addEventListener("click", async (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    const action = target.dataset.foundationAction;
    if (action === "apply-text") {
      await applyFoundationText();
    } else if (action === "reset-text") {
      await resetFoundationText();
    }
  });
  $("foundation-text-panel").addEventListener("keydown", async (event) => {
    if (event.target.id !== "foundation-textarea") return;
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      await applyFoundationText();
    }
  });
  $("csp-panel").addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    const { stepIndex } = target.dataset;
    if (!stepIndex) return;
    stopPlay();
    state.player.stepIndex = Math.max(0, Math.min(Number(stepIndex), maxStepCount()));
    render();
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  try {
    await loadApp();
  } catch (error) {
    window.alert(error.message);
  }
});
