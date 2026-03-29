"""Student-facing helpers for the labyrinth live-Python workflow."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, TypeAlias

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai9414.labyrinth.models import LabyrinthDefinition

LabyrinthState: TypeAlias = tuple[int, int]

LABYRINTH_ACTIONS: tuple[str, ...] = (
    "move_up",
    "move_right",
    "move_down",
    "move_left",
)

LABYRINTH_ACTION_DELTAS: dict[str, LabyrinthState] = {
    "move_up": (-1, 0),
    "move_right": (0, 1),
    "move_down": (1, 0),
    "move_left": (0, -1),
}

LABYRINTH_TRACE_ACTIONS: tuple[str, ...] = (
    "start",
    "expand",
    "backtrack",
    "found",
    "fail",
)


def validate_labyrinth_payload(labyrinth: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalise a labyrinth payload from the browser."""

    return LabyrinthDefinition.model_validate(labyrinth).model_dump()


def apply_labyrinth_action(cell: LabyrinthState, action: str) -> LabyrinthState:
    """Apply one labyrinth action to a state and return the successor state."""

    if action not in LABYRINTH_ACTION_DELTAS:
        raise ValueError(f"Unknown labyrinth action: {action}")
    row, col = cell
    dr, dc = LABYRINTH_ACTION_DELTAS[action]
    return (row + dr, col + dc)


def get_available_actions(
    labyrinth: dict[str, Any] | LabyrinthDefinition,
    cell: LabyrinthState,
) -> list[str]:
    """Return legal actions from a cell in deterministic DFS order."""

    definition = (
        labyrinth
        if isinstance(labyrinth, LabyrinthDefinition)
        else LabyrinthDefinition.model_validate(labyrinth)
    )
    actions: list[str] = []
    for action in LABYRINTH_ACTIONS:
        nr, nc = apply_labyrinth_action(cell, action)
        if not (0 <= nr < definition.rows and 0 <= nc < definition.cols):
            continue
        if definition.grid[nr][nc] == "#":
            continue
        actions.append(action)
    return actions


def get_open_neighbours(
    labyrinth: dict[str, Any] | LabyrinthDefinition,
    cell: LabyrinthState,
) -> list[LabyrinthState]:
    """Return open neighbouring cells in deterministic DFS order."""

    return [
        apply_labyrinth_action(cell, action)
        for action in get_available_actions(labyrinth, cell)
    ]


def build_unimplemented_result(message: str | None = None) -> dict[str, Any]:
    """Return a consistent placeholder result for an unfinished student solver."""

    return {
        "algorithm": "dfs",
        "status": "error",
        "message": message
        or (
            "Implement solve_dfs in solve_labyrinth.py. Return algorithm, status, "
            "trace, path, and visited_order."
        ),
        "trace": [],
        "path": [],
        "visited_order": [],
    }


def _is_cell_sequence(value: Any) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and len(value) == 2
        and all(isinstance(item, int) for item in value)
    )


def _validate_cell(value: Any, *, field_name: str) -> list[int]:
    if not _is_cell_sequence(value):
        raise ValueError(f"Field '{field_name}' must be a [row, col] pair.")
    return [int(value[0]), int(value[1])]


def _validate_cell_list(value: Any, *, field_name: str) -> list[list[int]]:
    if not isinstance(value, list):
        raise ValueError(f"Field '{field_name}' must be a list of cells.")
    return [_validate_cell(cell, field_name=field_name) for cell in value]


def validate_labyrinth_solver_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate the solver result shape returned to the browser."""

    if not isinstance(result, dict):
        raise ValueError("Solver result must be a dictionary.")

    required = {"algorithm", "status", "trace", "path", "visited_order"}
    missing = sorted(required - set(result))
    if missing:
        raise ValueError(f"Solver result is missing required key(s): {', '.join(missing)}.")

    algorithm = result["algorithm"]
    if algorithm != "dfs":
        raise ValueError("Field 'algorithm' must be 'dfs'.")

    status = result["status"]
    if status not in {"found", "not_found", "error"}:
        raise ValueError("Field 'status' must be 'found', 'not_found', or 'error'.")

    trace = result["trace"]
    if not isinstance(trace, list):
        raise ValueError("Field 'trace' must be a list.")

    validated_trace: list[dict[str, Any]] = []
    for expected_step, step in enumerate(trace):
        if not isinstance(step, dict):
            raise ValueError("Each trace entry must be a dictionary.")
        action = step.get("action")
        if action not in LABYRINTH_TRACE_ACTIONS:
            raise ValueError(
                "Each trace action must be one of: "
                + ", ".join(LABYRINTH_TRACE_ACTIONS)
                + "."
            )
        step_index = step.get("step")
        if not isinstance(step_index, int) or step_index != expected_step:
            raise ValueError("Trace steps must use consecutive integer indices starting at 0.")
        cell = step.get("cell")
        parent = step.get("parent")
        depth = step.get("depth")
        stack = step.get("stack")
        if cell is not None:
            cell = _validate_cell(cell, field_name="cell")
        if parent is not None:
            parent = _validate_cell(parent, field_name="parent")
        if not isinstance(depth, int) or depth < 0:
            raise ValueError("Field 'depth' in each trace entry must be a non-negative integer.")
        validated_stack = _validate_cell_list(stack, field_name="stack")
        validated_trace.append(
            {
                "step": step_index,
                "action": action,
                "cell": cell,
                "parent": parent,
                "depth": depth,
                "stack": validated_stack,
            }
        )

    path = _validate_cell_list(result["path"], field_name="path")
    visited_order = _validate_cell_list(result["visited_order"], field_name="visited_order")

    if status == "found" and not path:
        raise ValueError("A result with status 'found' must include a non-empty path.")

    validated_result = {
        "algorithm": "dfs",
        "status": status,
        "trace": validated_trace,
        "path": path,
        "visited_order": visited_order,
    }
    if "message" in result and result["message"] is not None:
        if not isinstance(result["message"], str):
            raise ValueError("Field 'message' must be a string when provided.")
        validated_result["message"] = result["message"]
    return validated_result


def run_labyrinth_solver(
    solver_fn: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    port: int = 9414,
    debug: bool = True,
) -> None:
    """Run the minimal local `/solve` server used by the live labyrinth demo."""

    app = FastAPI(title="ai9414 labyrinth solver")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.post("/solve")
    async def solve(payload: dict[str, Any]) -> JSONResponse:
        labyrinth = payload.get("labyrinth")
        if not isinstance(labyrinth, dict):
            return JSONResponse(
                {"message": "Request body must include a 'labyrinth' object."},
                status_code=400,
            )

        try:
            validated_labyrinth = validate_labyrinth_payload(labyrinth)
        except Exception as exc:
            return JSONResponse(
                {"message": f"Invalid labyrinth payload: {exc}"},
                status_code=400,
            )

        try:
            result = solver_fn(validated_labyrinth)
        except Exception as exc:
            return JSONResponse(
                {"message": f"Solver raised an exception: {exc}"},
                status_code=500,
            )

        try:
            validated_result = validate_labyrinth_solver_result(result)
        except ValueError as exc:
            return JSONResponse({"message": str(exc)}, status_code=400)

        status_code = 200 if validated_result["status"] in {"found", "not_found"} else 400
        return JSONResponse(validated_result, status_code=status_code)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="debug" if debug else "warning",
    )


def run_labyrinth_solver_server(
    solve_dfs: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    port: int = 9414,
    debug: bool = True,
) -> None:
    """Backward-compatible alias for the canonical live labyrinth runner."""

    run_labyrinth_solver(solve_dfs, port=port, debug=debug)
