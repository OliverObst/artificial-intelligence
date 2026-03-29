"""Plain DFS solver for labyrinth reachability."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from uuid import uuid4

from ai9414.labyrinth.models import LabyrinthDefinition, LabyrinthTreeNode

ALGORITHM_LABEL = "Depth-first search"
ALGORITHM_NOTE = (
    "This example uses plain depth-first search for reachability. "
    "It stops once it finds any path from the start to the exit, so it does not guarantee a shortest path."
)


@dataclass
class RawLabyrinthStep:
    event_type: str
    label: str
    annotation: str
    teaching_note: str
    snapshot: dict


@dataclass
class SimpleStep:
    step: int
    action: str
    cell: list[int] | None
    parent: list[int] | None
    depth: int
    stack: list[list[int]]


@dataclass
class LabyrinthSolveResult:
    trace_id: str
    initial_state: dict
    raw_steps: list[RawLabyrinthStep]
    simple_trace: list[dict]
    status: str
    path: list[list[int]]
    visited_order: list[list[int]]


class _Recorder:
    def __init__(self, labyrinth: LabyrinthDefinition) -> None:
        self.labyrinth = labyrinth
        self.tree_nodes: dict[str, LabyrinthTreeNode] = {}
        self.visible_tree_ids: list[str] = []
        self.active_tree_node: str | None = None
        self.active_tree_path: list[str] = []
        self.current_route: list[list[int]] = [list(labyrinth.start)]
        self.visited_order: list[list[int]] = [list(labyrinth.start)]
        self.visited_set = {tuple(labyrinth.start)}
        self.dead_end_cells: list[list[int]] = []
        self.dead_end_set: set[tuple[int, int]] = set()
        self.final_path: list[list[int]] = []
        self.status = "searching"
        self.depth = 0
        self.simple_trace: list[dict] = []
        self.raw_steps: list[RawLabyrinthStep] = []
        self.counter = 0
        self.trace_id = f"labyrinth-{uuid4().hex[:8]}"

    def create_tree_node(self, cell: list[int], parent: str | None, depth: int, status: str) -> str:
        tree_id = f"t{self.counter}"
        self.counter += 1
        self.tree_nodes[tree_id] = LabyrinthTreeNode(
            tree_id=tree_id,
            graph_node=f"({cell[0]}, {cell[1]})",
            cell=list(cell),
            parent=parent,
            depth=depth,
            path_cost=depth,
            status=status,
            order=len(self.visible_tree_ids),
        )
        self.visible_tree_ids.append(tree_id)
        return tree_id

    def set_status(self, tree_id: str, status: str) -> None:
        self.tree_nodes[tree_id].status = status

    def snapshot(self) -> dict:
        return {
            "tree": {
                "nodes": [
                    self.tree_nodes[tree_id].model_dump()
                    for tree_id in self.visible_tree_ids
                ]
            },
            "search": {
                "active_tree_node": self.active_tree_node,
                "active_tree_path": list(self.active_tree_path),
                "current_route": copy.deepcopy(self.current_route),
                "visited_order": copy.deepcopy(self.visited_order),
                "dead_end_cells": copy.deepcopy(self.dead_end_cells),
                "final_path": copy.deepcopy(self.final_path),
                "explored_count": len(self.visited_order),
                "current_depth": self.depth,
                "status": self.status,
                "found": bool(self.final_path),
            },
        }

    def record_simple(
        self,
        *,
        action: str,
        cell: list[int] | None,
        parent: list[int] | None,
        depth: int,
    ) -> None:
        self.simple_trace.append(
            {
                "step": len(self.simple_trace),
                "action": action,
                "cell": copy.deepcopy(cell),
                "parent": copy.deepcopy(parent),
                "depth": depth,
                "stack": copy.deepcopy(self.current_route),
            }
        )

    def record_raw(
        self,
        *,
        event_type: str,
        label: str,
        annotation: str,
        teaching_note: str,
    ) -> None:
        self.raw_steps.append(
            RawLabyrinthStep(
                event_type=event_type,
                label=label,
                annotation=annotation,
                teaching_note=teaching_note,
                snapshot=self.snapshot(),
            )
        )


def _cell_value(labyrinth: LabyrinthDefinition, cell: tuple[int, int]) -> str:
    return labyrinth.grid[cell[0]][cell[1]]


def _neighbours(labyrinth: LabyrinthDefinition, cell: tuple[int, int]) -> list[tuple[int, int]]:
    row, col = cell
    ordered = [(row, col + 1), (row + 1, col), (row, col - 1), (row - 1, col)]
    valid: list[tuple[int, int]] = []
    for nr, nc in ordered:
        if not (0 <= nr < labyrinth.rows and 0 <= nc < labyrinth.cols):
            continue
        if _cell_value(labyrinth, (nr, nc)) == "#":
            continue
        valid.append((nr, nc))
    return valid


def solve_labyrinth(labyrinth: LabyrinthDefinition) -> LabyrinthSolveResult:
    recorder = _Recorder(labyrinth)
    root_id = recorder.create_tree_node(list(labyrinth.start), None, 0, "active")
    recorder.active_tree_node = root_id
    recorder.active_tree_path = [root_id]
    recorder.record_simple(action="start", cell=list(labyrinth.start), parent=None, depth=0)
    recorder.record_raw(
        event_type="start",
        label="Start DFS",
        annotation="DFS starts at the maze entrance and follows one branch until it must backtrack or reaches the exit.",
        teaching_note=ALGORITHM_NOTE,
    )

    found = False

    def dfs(cell: tuple[int, int], tree_id: str, depth: int) -> bool:
        nonlocal found
        if cell == tuple(labyrinth.exit):
            recorder.set_status(tree_id, "final")
            recorder.final_path = copy.deepcopy(recorder.current_route)
            recorder.depth = depth
            recorder.status = "exit found"
            recorder.record_simple(
                action="found",
                cell=list(cell),
                parent=recorder.current_route[-2] if len(recorder.current_route) > 1 else None,
                depth=depth,
            )
            recorder.record_raw(
                event_type="found",
                label="Exit found",
                annotation="DFS has reached the exit. The highlighted route is the first successful path it discovered.",
                teaching_note="Plain DFS stops here because the goal is reachability, not optimality.",
            )
            found = True
            return True

        recorder.set_status(tree_id, "active")
        for neighbour in _neighbours(labyrinth, cell):
            if neighbour in recorder.visited_set:
                continue
            child = list(neighbour)
            child_id = recorder.create_tree_node(child, tree_id, depth + 1, "active")
            recorder.set_status(tree_id, "expanded")
            recorder.active_tree_node = child_id
            recorder.active_tree_path.append(child_id)
            recorder.current_route.append(child)
            recorder.visited_order.append(child)
            recorder.visited_set.add(neighbour)
            recorder.depth = depth + 1
            recorder.status = "searching"
            recorder.record_simple(action="expand", cell=child, parent=list(cell), depth=depth + 1)
            recorder.record_raw(
                event_type="expand",
                label=f"Expand {child}",
                annotation=f"DFS steps into {tuple(child)} and continues deeper into the maze.",
                teaching_note="The maze route on the right and the tree branch on the left advance together.",
            )

            if dfs(neighbour, child_id, depth + 1):
                recorder.set_status(tree_id, "final")
                return True

            recorder.current_route.pop()
            recorder.active_tree_path.pop()
            recorder.active_tree_node = tree_id
            recorder.depth = depth
            recorder.status = "backtracking"
            if tuple(child) not in recorder.dead_end_set:
                recorder.dead_end_set.add(tuple(child))
                recorder.dead_end_cells.append(child)
            recorder.set_status(child_id, "backtracked")
            recorder.set_status(tree_id, "active")
            recorder.record_simple(action="backtrack", cell=child, parent=list(cell), depth=depth + 1)
            recorder.record_raw(
                event_type="backtrack",
                label=f"Backtrack from {child}",
                annotation=f"The branch through {tuple(child)} leads to a dead end, so DFS retreats to {cell}.",
                teaching_note="Backtracking is the moment where the search tree keeps its history even though the maze route retracts.",
            )

        if tree_id != root_id:
            recorder.set_status(tree_id, "backtracked")
        return False

    dfs(tuple(labyrinth.start), root_id, 0)

    if not found:
        recorder.status = "no path"
        recorder.active_tree_node = None
        recorder.active_tree_path = []
        recorder.current_route = []
        recorder.record_simple(action="fail", cell=None, parent=None, depth=0)
        recorder.record_raw(
            event_type="fail",
            label="No path found",
            annotation="DFS exhausted every reachable branch and did not find an exit path.",
            teaching_note="This is unusual for the generated mazes because they are constructed to be solvable.",
        )

    initial_state = {
        "example_title": "",
        "example_subtitle": "",
        "algorithm_label": ALGORITHM_LABEL,
        "algorithm_note": ALGORITHM_NOTE,
        "goal_label": "Find any path from start to exit",
        "labyrinth": labyrinth.model_dump(),
        "tree": {"nodes": [recorder.tree_nodes[root_id].model_dump()]},
        "search": {
            "active_tree_node": root_id,
            "active_tree_path": [root_id],
            "current_route": [list(labyrinth.start)],
            "visited_order": [list(labyrinth.start)],
            "dead_end_cells": [],
            "final_path": [],
            "explored_count": 1,
            "current_depth": 0,
            "status": "searching",
            "found": False,
        },
    }

    return LabyrinthSolveResult(
        trace_id=recorder.trace_id,
        initial_state=initial_state,
        raw_steps=recorder.raw_steps,
        simple_trace=recorder.simple_trace,
        status="found" if found else "fail",
        path=copy.deepcopy(recorder.final_path),
        visited_order=copy.deepcopy(recorder.visited_order),
    )
