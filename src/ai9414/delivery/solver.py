"""DFS solver customisation for the delivery office demo."""

from __future__ import annotations

import copy
import random
from collections import deque
from uuid import uuid4

from ai9414.labyrinth.models import LabyrinthDefinition, LabyrinthTreeNode
from ai9414.labyrinth.solver import LabyrinthSolveResult, RawLabyrinthStep

ALGORITHM_LABEL = "Depth-first search"
ALGORITHM_NOTE = (
    "This example uses plain depth-first search for reachability. "
    "The robot stops once it finds any route to the delivery location, so it does not guarantee a shortest route."
)
COLLECTION_ALGORITHM_LABEL = "Stateful collection search"
COLLECTION_ALGORITHM_NOTE = (
    "This example searches over the robot's position, heading, and collected dots. "
    "The route may cross an already visited corridor when that is needed to reach remaining dots."
)

ACTION_ORDER_LABELS = {
    "straight_left_right": "forward, left turn, right turn",
    "straight_right_left": "forward, right turn, left turn",
    "random": "random choice",
}

_START_HEADING = (0, 1)
_CARDINAL_DELTAS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def _left_turn(heading: tuple[int, int]) -> tuple[int, int]:
    return (-heading[1], heading[0])


def _right_turn(heading: tuple[int, int]) -> tuple[int, int]:
    return (heading[1], -heading[0])


def _heading_between(from_cell: tuple[int, int], to_cell: tuple[int, int]) -> tuple[int, int]:
    return (to_cell[0] - from_cell[0], to_cell[1] - from_cell[1])


def _turn_robot_to(
    recorder: "_CollectionRecorder",
    desired_heading: tuple[int, int],
    *,
    cell: tuple[int, int],
    depth: int,
) -> None:
    while recorder.heading != desired_heading:
        if _left_turn(recorder.heading) == desired_heading:
            recorder.heading = _left_turn(recorder.heading)
            action = "turn_left"
            label = "Turn left"
        else:
            recorder.heading = _right_turn(recorder.heading)
            action = "turn_right"
            label = "Turn right"
        recorder.status = "turning"
        recorder.record_simple(action=action, cell=list(cell), parent=None, depth=depth)
        recorder.record_raw(
            event_type=action,
            label=label,
            annotation=(
                f"The robot turns in place at {cell}. It has not moved to another square yet."
            ),
            teaching_note="Turning changes only Pac-Man's heading; the forward action is what changes cells.",
        )


def solve_delivery(
    labyrinth: LabyrinthDefinition,
    *,
    goal_type: str = "target",
    action_order: str = "straight_left_right",
    random_seed: int = 7,
) -> LabyrinthSolveResult:
    if goal_type == "collect_all":
        return _solve_collect_all_delivery(
            labyrinth,
            action_order=action_order,
            random_seed=random_seed,
        )
    return _solve_target_delivery(
        labyrinth,
        action_order=action_order,
        random_seed=random_seed,
    )


class _CollectionRecorder:
    def __init__(self, labyrinth: LabyrinthDefinition) -> None:
        self.labyrinth = labyrinth
        self.collectibles = [list(cell) for cell in labyrinth.collectibles]
        self.tree_nodes: dict[str, LabyrinthTreeNode] = {}
        self.visible_tree_ids: list[str] = []
        self.active_tree_node: str | None = None
        self.active_tree_path: list[str] = []
        self.current_route: list[list[int]] = [list(labyrinth.start)]
        self.visited_order: list[list[int]] = [list(labyrinth.start)]
        self.visited_cell_set = {tuple(labyrinth.start)}
        self.dead_end_cells: list[list[int]] = []
        self.dead_end_set: set[tuple[int, int]] = set()
        self.collected_dots: list[list[int]] = []
        self.final_path: list[list[int]] = []
        self.heading = _START_HEADING
        self.action_order_label = ACTION_ORDER_LABELS["straight_left_right"]
        self.status = "collecting"
        self.depth = 0
        self.simple_trace: list[dict] = []
        self.raw_steps: list[RawLabyrinthStep] = []
        self.counter = 0
        self.trace_id = f"delivery-{uuid4().hex[:8]}"

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
            "action_order_label": self.action_order_label,
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
                "delivery_heading": list(self.heading),
                "collected_dots": copy.deepcopy(self.collected_dots),
                "remaining_dots": [
                    list(dot)
                    for dot in self.collectibles
                    if tuple(dot) not in {tuple(item) for item in self.collected_dots}
                ],
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
                "heading": list(self.heading),
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


def _solve_target_delivery(
    labyrinth: LabyrinthDefinition,
    *,
    action_order: str,
    random_seed: int,
) -> LabyrinthSolveResult:
    recorder = _CollectionRecorder(labyrinth)
    recorder.action_order_label = ACTION_ORDER_LABELS[action_order]
    recorder.status = "searching"
    root_id = recorder.create_tree_node(list(labyrinth.start), None, 0, "active")
    recorder.active_tree_node = root_id
    recorder.active_tree_path = [root_id]
    recorder.record_simple(action="start", cell=list(labyrinth.start), parent=None, depth=0)
    recorder.record_raw(
        event_type="start",
        label="Start DFS",
        annotation=(
            "The robot starts in the office facing right. Turn actions change its heading, "
            "and forward actions move it to another square."
        ),
        teaching_note=ALGORITHM_NOTE,
    )

    found = False

    def dfs(
        cell: tuple[int, int],
        tree_id: str,
        depth: int,
        previous: tuple[int, int] | None,
    ) -> bool:
        nonlocal found
        if cell == tuple(labyrinth.exit):
            recorder.set_status(tree_id, "final")
            recorder.final_path = copy.deepcopy(recorder.current_route)
            recorder.depth = depth
            recorder.status = "delivery found"
            recorder.record_simple(
                action="found",
                cell=list(cell),
                parent=recorder.current_route[-2] if len(recorder.current_route) > 1 else None,
                depth=depth,
            )
            recorder.record_raw(
                event_type="found",
                label="Delivery location found",
                annotation=(
                    "DFS has reached the delivery location. The highlighted route is the first successful route it discovered."
                ),
                teaching_note="Plain DFS stops here because the goal is reachability, not optimality.",
            )
            found = True
            return True

        recorder.set_status(tree_id, "active")
        for neighbour in _delivery_neighbours(
            labyrinth,
            cell,
            previous,
            depth,
            action_order=action_order,
            random_seed=random_seed,
        ):
            if neighbour in recorder.visited_cell_set:
                continue
            desired_heading = _heading_between(cell, neighbour)
            _turn_robot_to(recorder, desired_heading, cell=cell, depth=depth)

            child = list(neighbour)
            child_id = recorder.create_tree_node(child, tree_id, depth + 1, "active")
            recorder.set_status(tree_id, "expanded")
            recorder.active_tree_node = child_id
            recorder.active_tree_path.append(child_id)
            recorder.current_route.append(child)
            recorder.visited_order.append(child)
            recorder.visited_cell_set.add(neighbour)
            recorder.depth = depth + 1
            recorder.status = "searching"
            recorder.record_simple(action="forward", cell=child, parent=list(cell), depth=depth + 1)
            recorder.record_raw(
                event_type="expand",
                label=f"Forward to {child}",
                annotation=f"The robot moves forward from {cell} to {tuple(child)}.",
                teaching_note="Forward is the only action that moves Pac-Man to another square.",
            )

            if dfs(neighbour, child_id, depth + 1, cell):
                recorder.set_status(tree_id, "final")
                return True

            back_heading = _heading_between(neighbour, cell)
            _turn_robot_to(recorder, back_heading, cell=neighbour, depth=depth + 1)
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
            recorder.record_simple(action="forward_back", cell=list(cell), parent=child, depth=depth)
            recorder.record_raw(
                event_type="backtrack",
                label=f"Forward back to {list(cell)}",
                annotation=f"The robot moves forward back from {tuple(child)} to {cell} after exhausting that branch.",
                teaching_note=(
                    "Backtracking still uses the same movement rule: turn in place if needed, then move forward one square."
                ),
            )

        if tree_id != root_id:
            recorder.set_status(tree_id, "backtracked")
        return False

    dfs(tuple(labyrinth.start), root_id, 0, None)

    if not found:
        recorder.status = "no route"
        recorder.active_tree_node = None
        recorder.active_tree_path = []
        recorder.current_route = []
        recorder.record_simple(action="fail", cell=None, parent=None, depth=0)
        recorder.record_raw(
            event_type="fail",
            label="No delivery route found",
            annotation="DFS exhausted every reachable office cell and did not find the delivery location.",
            teaching_note="No route from the robot to the delivery location was found.",
        )

    initial_state = {
        "example_title": "",
        "example_subtitle": "",
        "algorithm_label": ALGORITHM_LABEL,
        "algorithm_note": ALGORITHM_NOTE,
        "goal_label": "Find any route from the robot to the delivery location",
        "action_order_label": ACTION_ORDER_LABELS[action_order],
        "labyrinth": labyrinth.model_dump(),
        "tree": {"nodes": [recorder.tree_nodes[root_id].model_dump()]},
        "search": {
            "active_tree_node": root_id,
            "active_tree_path": [root_id],
            "current_route": [list(labyrinth.start)],
            "visited_order": [list(labyrinth.start)],
            "dead_end_cells": [],
            "final_path": [],
            "delivery_heading": list(_START_HEADING),
            "collected_dots": [],
            "remaining_dots": [],
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


def _solve_collect_all_delivery(
    labyrinth: LabyrinthDefinition,
    *,
    action_order: str,
    random_seed: int,
) -> LabyrinthSolveResult:
    recorder = _CollectionRecorder(labyrinth)
    recorder.action_order_label = ACTION_ORDER_LABELS[action_order]
    collectible_set = {tuple(cell) for cell in labyrinth.collectibles}
    root_cell = tuple(labyrinth.start)
    root_collected = frozenset([root_cell] if root_cell in collectible_set else [])
    if root_collected:
        recorder.collected_dots = [list(root_cell)]

    root_id = recorder.create_tree_node(list(labyrinth.start), None, 0, "active")
    recorder.active_tree_node = root_id
    recorder.active_tree_path = [root_id]
    recorder.record_simple(action="start", cell=list(labyrinth.start), parent=None, depth=0)
    recorder.record_raw(
        event_type="start",
        label="Start collection search",
        annotation="The robot starts in the maze and follows a route that tracks which dots have been collected.",
        teaching_note=COLLECTION_ALGORITHM_NOTE,
    )

    route = _build_collection_route(labyrinth, collectible_set)
    found = route is not None

    if not found:
        recorder.status = "not all dots reachable"
        recorder.active_tree_node = None
        recorder.active_tree_path = []
        recorder.current_route = []
        recorder.record_simple(action="fail", cell=None, parent=None, depth=0)
        recorder.record_raw(
            event_type="fail",
            label="Dots not collected",
            annotation="DFS exhausted every reachable collection state without collecting all dots.",
            teaching_note="At least one dot could not be collected from the current office layout.",
        )
    else:
        parent_tree_id = root_id
        collected = set(root_collected)
        for depth, next_cell in enumerate(route[1:], start=1):
            current_cell = tuple(recorder.current_route[-1])
            desired_heading = _heading_between(current_cell, next_cell)
            _turn_robot_to(recorder, desired_heading, cell=current_cell, depth=depth - 1)

            child = list(next_cell)
            child_id = recorder.create_tree_node(child, parent_tree_id, depth, "active")
            recorder.set_status(parent_tree_id, "expanded")
            recorder.active_tree_node = child_id
            recorder.active_tree_path.append(child_id)
            recorder.current_route.append(child)
            recorder.visited_cell_set.add(next_cell)
            recorder.visited_order.append(child)
            is_new_dot = next_cell in collectible_set and next_cell not in collected
            if is_new_dot:
                collected.add(next_cell)
            recorder.collected_dots = [list(dot) for dot in sorted(collected)]
            recorder.depth = depth
            recorder.status = "collecting"
            recorder.record_simple(action="forward", cell=child, parent=list(current_cell), depth=depth)
            recorder.record_raw(
                event_type="expand",
                label=f"{'Collect dot at' if is_new_dot else 'Forward to'} {child}",
                annotation=(
                    f"The robot moves forward from {current_cell} to {tuple(child)}"
                    f"{' and collects a dot' if is_new_dot else ''}."
                ),
                teaching_note="Forward is the only action that moves Pac-Man to another square.",
            )
            parent_tree_id = child_id

        recorder.set_status(parent_tree_id, "final")
        recorder.final_path = copy.deepcopy(recorder.current_route)
        recorder.status = "all dots collected"
        recorder.record_simple(
            action="found",
            cell=copy.deepcopy(recorder.current_route[-1]),
            parent=recorder.current_route[-2] if len(recorder.current_route) > 1 else None,
            depth=len(route) - 1,
        )
        recorder.record_raw(
            event_type="found",
            label="All dots collected",
            annotation="The robot has collected every dot in the maze.",
            teaching_note="The collected-dot set is part of the state, so returning through a corridor is not the same as making no progress.",
        )

    initial_state = {
        "example_title": "",
        "example_subtitle": "",
        "algorithm_label": COLLECTION_ALGORITHM_LABEL,
        "algorithm_note": COLLECTION_ALGORITHM_NOTE,
        "goal_label": "Collect every dot in the office",
        "action_order_label": ACTION_ORDER_LABELS[action_order],
        "labyrinth": labyrinth.model_dump(),
        "tree": {"nodes": [recorder.tree_nodes[root_id].model_dump()]},
        "search": {
            "active_tree_node": root_id,
            "active_tree_path": [root_id],
            "current_route": [list(labyrinth.start)],
            "visited_order": [list(labyrinth.start)],
            "dead_end_cells": [],
            "final_path": [],
            "delivery_heading": list(_START_HEADING),
            "collected_dots": [list(dot) for dot in sorted(root_collected)],
            "remaining_dots": [
                list(dot)
                for dot in sorted(collectible_set - set(root_collected))
            ],
            "explored_count": 1,
            "current_depth": 0,
            "status": "collecting",
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


def _build_collection_route(
    labyrinth: LabyrinthDefinition,
    collectible_set: set[tuple[int, int]],
) -> list[tuple[int, int]] | None:
    current = tuple(labyrinth.start)
    route = [current]
    remaining = set(collectible_set)
    remaining.discard(current)

    while remaining:
        path = _shortest_path_to_dot(
            labyrinth,
            current,
            remaining=remaining,
        )
        if path is None:
            return None
        for cell in path:
            route.append(cell)
            remaining.discard(cell)
            current = cell

    return route


def _shortest_path_to_dot(
    labyrinth: LabyrinthDefinition,
    start: tuple[int, int],
    *,
    remaining: set[tuple[int, int]],
) -> list[tuple[int, int]] | None:
    queue = deque([(start, [])])
    seen = {start}
    while queue:
        cell, path = queue.popleft()
        if cell in remaining and cell != start:
            return path
        for neighbour in _plain_open_neighbours(labyrinth, cell):
            if neighbour in seen:
                continue
            seen.add(neighbour)
            queue.append((neighbour, [*path, neighbour]))
    return None


def _open_cells(labyrinth: LabyrinthDefinition) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row in range(labyrinth.rows)
        for col in range(labyrinth.cols)
        if labyrinth.grid[row][col] != "#"
    }


def _plain_open_neighbours(
    labyrinth: LabyrinthDefinition,
    cell: tuple[int, int],
) -> list[tuple[int, int]]:
    row, col = cell
    return [
        candidate
        for candidate in ((row, col + 1), (row + 1, col), (row, col - 1), (row - 1, col))
        if _is_open(labyrinth, candidate)
    ]


def _delivery_neighbours(
    labyrinth: LabyrinthDefinition,
    cell: tuple[int, int],
    previous: tuple[int, int] | None,
    depth: int,
    *,
    action_order: str,
    random_seed: int,
) -> list[tuple[int, int]]:
    row, col = cell
    valid = []
    for dr, dc in _CARDINAL_DELTAS:
        candidate = (row + dr, col + dc)
        if not _is_open(labyrinth, candidate):
            continue
        valid.append(candidate)

    if action_order == "random":
        ordered = list(valid)
        rng = random.Random(f"{random_seed}:{row}:{col}:{depth}")
        rng.shuffle(ordered)
        return ordered

    heading = _heading_from(previous, cell)
    straight = heading
    left = (-heading[1], heading[0])
    right = (heading[1], -heading[0])
    back = (-heading[0], -heading[1])
    relative_order = (
        (straight, left, right, back)
        if action_order == "straight_left_right"
        else (straight, right, left, back)
    )
    priority = {
        (row + dr, col + dc): index
        for index, (dr, dc) in enumerate(relative_order)
    }
    return sorted(valid, key=lambda candidate: priority.get(candidate, len(priority)))


def _heading_from(previous: tuple[int, int] | None, cell: tuple[int, int]) -> tuple[int, int]:
    if previous is None:
        return _START_HEADING
    return (cell[0] - previous[0], cell[1] - previous[1])


def _is_open(labyrinth: LabyrinthDefinition, cell: tuple[int, int]) -> bool:
    row, col = cell
    return 0 <= row < labyrinth.rows and 0 <= col < labyrinth.cols and labyrinth.grid[row][col] != "#"


def _delivery_status(status: str) -> str:
    return {
        "exit found": "delivery found",
        "no path": "no route",
    }.get(status, status)
