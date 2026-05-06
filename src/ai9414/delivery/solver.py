"""DFS solver customisation for the delivery office demo."""

from __future__ import annotations

import random
from uuid import uuid4

from ai9414.labyrinth.models import LabyrinthDefinition
from ai9414.labyrinth.solver import LabyrinthSolveResult, solve_labyrinth

ALGORITHM_LABEL = "Depth-first search"
ALGORITHM_NOTE = (
    "This example uses plain depth-first search for reachability. "
    "The robot stops once it finds any route to the delivery location, so it does not guarantee a shortest route."
)

ACTION_ORDER_LABELS = {
    "straight_left_right": "straight, left, right",
    "straight_right_left": "straight, right, left",
    "random": "random choice",
}

_START_HEADING = (0, 1)
_CARDINAL_DELTAS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def solve_delivery(
    labyrinth: LabyrinthDefinition,
    *,
    action_order: str = "straight_left_right",
    random_seed: int = 7,
) -> LabyrinthSolveResult:
    result = solve_labyrinth(
        labyrinth,
        neighbour_order=lambda office, cell, previous, depth: _delivery_neighbours(
            office,
            cell,
            previous,
            depth,
            action_order=action_order,
            random_seed=random_seed,
        ),
    )
    result.trace_id = f"delivery-{uuid4().hex[:8]}"
    result.initial_state["algorithm_label"] = ALGORITHM_LABEL
    result.initial_state["algorithm_note"] = ALGORITHM_NOTE
    result.initial_state["goal_label"] = "Find any route from the robot to the delivery location"
    result.initial_state["action_order_label"] = ACTION_ORDER_LABELS[action_order]

    for raw_step in result.raw_steps:
        raw_step.snapshot["search"]["status"] = _delivery_status(raw_step.snapshot["search"]["status"])
        raw_step.snapshot["action_order_label"] = ACTION_ORDER_LABELS[action_order]
        if raw_step.event_type == "start":
            raw_step.label = "Start DFS"
            raw_step.annotation = (
                "The robot starts in the office and DFS follows one possible route until "
                "it must backtrack or reaches the delivery location."
            )
            raw_step.teaching_note = ALGORITHM_NOTE
        elif raw_step.event_type == "expand":
            raw_step.label = raw_step.label.replace("Expand", "Move to")
            raw_step.annotation = raw_step.annotation.replace("the maze", "the office")
            raw_step.teaching_note = "The office route on the right and the tree branch on the left advance together."
        elif raw_step.event_type == "backtrack":
            raw_step.annotation = raw_step.annotation.replace("dead end", "unhelpful route")
            raw_step.annotation = raw_step.annotation.replace("DFS retreats", "the robot retreats")
            raw_step.teaching_note = (
                "Backtracking keeps the search history visible even though the current office route retracts."
            )
        elif raw_step.event_type == "found":
            raw_step.label = "Delivery location found"
            raw_step.annotation = (
                "DFS has reached the delivery location. The highlighted route is the first successful route it discovered."
            )
            raw_step.teaching_note = "Plain DFS stops here because the goal is reachability, not optimality."
        elif raw_step.event_type == "fail":
            raw_step.label = "No delivery route found"
            raw_step.annotation = "DFS exhausted every reachable office cell and did not find the delivery location."
            raw_step.teaching_note = "No route from the robot to the delivery location was found."

    return result


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
