"""Student-facing helpers for the spatial graph UCS live-Python workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai9414.search.models import WeightedGraph

GRAPH_UCS_TRACE_ACTIONS: tuple[str, ...] = (
    "start",
    "expand",
    "consider_edge",
    "relax",
    "found",
    "fail",
)


def validate_graph_payload(graph: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalise a weighted graph payload from the browser."""

    return WeightedGraph.model_validate(graph).model_dump()


def get_neighbours(graph: dict[str, Any] | WeightedGraph, node_id: str) -> list[tuple[str, float]]:
    """Return neighbouring node ids and edge costs in deterministic UCS order."""

    definition = graph if isinstance(graph, WeightedGraph) else WeightedGraph.model_validate(graph)
    neighbours: list[tuple[str, float]] = []
    for edge in definition.edges:
        if edge.u == node_id:
            neighbours.append((edge.v, float(edge.cost)))
        elif edge.v == node_id:
            neighbours.append((edge.u, float(edge.cost)))
    neighbours.sort(key=lambda item: (item[1], item[0]))
    return neighbours


def build_unimplemented_graph_ucs_result(message: str | None = None) -> dict[str, Any]:
    """Return a consistent placeholder result for an unfinished student solver."""

    return {
        "algorithm": "ucs",
        "status": "error",
        "message": message
        or (
            "Implement solve_ucs in solve_graph.py. Return algorithm, status, "
            "trace, path, best_cost, and visited_order."
        ),
        "trace": [],
        "path": [],
        "best_cost": None,
        "visited_order": [],
    }


def validate_graph_ucs_solver_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate the solver result shape returned to the browser."""

    if not isinstance(result, dict):
        raise ValueError("Solver result must be a dictionary.")

    required = {"algorithm", "status", "trace", "path", "best_cost", "visited_order"}
    missing = sorted(required - set(result))
    if missing:
        raise ValueError(f"Solver result is missing required key(s): {', '.join(missing)}.")

    if result["algorithm"] != "ucs":
        raise ValueError("Field 'algorithm' must be 'ucs'.")

    if result["status"] not in {"found", "not_found", "error"}:
        raise ValueError("Field 'status' must be 'found', 'not_found', or 'error'.")

    trace = result["trace"]
    if not isinstance(trace, list):
        raise ValueError("Field 'trace' must be a list.")

    validated_trace: list[dict[str, Any]] = []
    for expected_step, step in enumerate(trace):
        if not isinstance(step, dict):
            raise ValueError("Each trace entry must be a dictionary.")
        action = step.get("action")
        if action not in GRAPH_UCS_TRACE_ACTIONS:
            raise ValueError(
                "Each trace action must be one of: "
                + ", ".join(GRAPH_UCS_TRACE_ACTIONS)
                + "."
            )
        step_index = step.get("step")
        if not isinstance(step_index, int) or step_index != expected_step:
            raise ValueError("Trace steps must use consecutive integer indices starting at 0.")
        node_id = step.get("node")
        parent = step.get("parent")
        depth = step.get("depth")
        path_cost = step.get("path_cost")
        current_path = step.get("current_path")
        current_cost = step.get("current_cost")
        best_path = step.get("best_path")
        best_cost = step.get("best_cost")
        considered_edge = step.get("considered_edge")

        if node_id is not None and not isinstance(node_id, str):
            raise ValueError("Field 'node' in each trace entry must be a string or null.")
        if parent is not None and not isinstance(parent, str):
            raise ValueError("Field 'parent' in each trace entry must be a string or null.")
        if not isinstance(depth, int) or depth < 0:
            raise ValueError("Field 'depth' in each trace entry must be a non-negative integer.")
        if not isinstance(path_cost, (int, float)):
            raise ValueError("Field 'path_cost' in each trace entry must be numeric.")
        if not isinstance(current_path, list) or not all(isinstance(item, str) for item in current_path):
            raise ValueError("Field 'current_path' in each trace entry must be a list of node ids.")
        if not isinstance(current_cost, (int, float)):
            raise ValueError("Field 'current_cost' in each trace entry must be numeric.")
        if not isinstance(best_path, list) or not all(isinstance(item, str) for item in best_path):
            raise ValueError("Field 'best_path' in each trace entry must be a list of node ids.")
        if best_cost is not None and not isinstance(best_cost, (int, float)):
            raise ValueError("Field 'best_cost' in each trace entry must be numeric or null.")
        if considered_edge is not None:
            if (
                not isinstance(considered_edge, list)
                or len(considered_edge) != 2
                or not all(isinstance(item, str) for item in considered_edge)
            ):
                raise ValueError("Field 'considered_edge' must be null or a two-node list.")
        validated_trace.append(
            {
                "step": step_index,
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
        )

    path = result["path"]
    visited_order = result["visited_order"]
    best_cost = result["best_cost"]
    if not isinstance(path, list) or not all(isinstance(item, str) for item in path):
        raise ValueError("Field 'path' must be a list of node ids.")
    if not isinstance(visited_order, list) or not all(isinstance(item, str) for item in visited_order):
        raise ValueError("Field 'visited_order' must be a list of node ids.")
    if best_cost is not None and not isinstance(best_cost, (int, float)):
        raise ValueError("Field 'best_cost' must be numeric or null.")
    if result["status"] == "found":
        if not path:
            raise ValueError("A result with status 'found' must include a non-empty path.")
        if best_cost is None:
            raise ValueError("A result with status 'found' must include 'best_cost'.")

    validated_result = {
        "algorithm": "ucs",
        "status": result["status"],
        "trace": validated_trace,
        "path": list(path),
        "best_cost": None if best_cost is None else float(best_cost),
        "visited_order": list(visited_order),
    }
    if "message" in result and result["message"] is not None:
        if not isinstance(result["message"], str):
            raise ValueError("Field 'message' must be a string when provided.")
        validated_result["message"] = result["message"]
    return validated_result


def run_graph_ucs_solver(
    solver_fn: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    port: int = 9414,
    debug: bool = True,
) -> None:
    """Run the minimal local `/solve` server used by the live graph UCS demo."""

    app = FastAPI(title="ai9414 spatial graph UCS solver")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.post("/solve")
    async def solve(payload: dict[str, Any]) -> JSONResponse:
        graph = payload.get("graph")
        if not isinstance(graph, dict):
            return JSONResponse({"message": "Request body must include a 'graph' object."}, status_code=400)

        try:
            validated_graph = validate_graph_payload(graph)
        except Exception as exc:
            return JSONResponse({"message": f"Invalid graph payload: {exc}"}, status_code=400)

        try:
            result = solver_fn(validated_graph)
        except Exception as exc:
            return JSONResponse({"message": f"Solver raised an exception: {exc}"}, status_code=500)

        try:
            validated_result = validate_graph_ucs_solver_result(result)
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
