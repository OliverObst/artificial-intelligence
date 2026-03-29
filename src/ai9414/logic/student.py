"""Student-facing helpers for the live DPLL workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai9414.logic.models import LogicProblem

DPLL_TRACE_ACTIONS: tuple[str, ...] = (
    "start",
    "choose_variable",
    "assign",
    "contradiction",
    "backtrack",
    "solution_found",
    "finished",
)


def validate_logic_payload(problem: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalise a logic problem payload from the browser."""

    return LogicProblem.model_validate(problem).model_dump()


def build_unimplemented_dpll_result(message: str | None = None) -> dict[str, Any]:
    """Return a consistent placeholder result for an unfinished student solver."""

    return {
        "algorithm": "dpll",
        "mode": "sat",
        "status": "error",
        "message": message
        or (
            "Implement solve_dpll in solve_dpll.py. Return algorithm, mode, status, "
            "trace, and optionally a satisfying assignment."
        ),
        "trace": [],
        "assignment": {},
    }


def validate_dpll_solver_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate the solver result shape returned to the browser."""

    if not isinstance(result, dict):
        raise ValueError("Solver result must be a dictionary.")

    required = {"algorithm", "mode", "status", "trace"}
    missing = sorted(required - set(result))
    if missing:
        raise ValueError(f"Solver result is missing required key(s): {', '.join(missing)}.")

    if result["algorithm"] != "dpll":
        raise ValueError("Field 'algorithm' must be 'dpll'.")
    if result["mode"] not in {"sat", "entailment"}:
        raise ValueError("Field 'mode' must be 'sat' or 'entailment'.")
    if result["status"] not in {"satisfiable", "unsatisfiable", "entailed", "not_entailed", "error"}:
        raise ValueError(
            "Field 'status' must be 'satisfiable', 'unsatisfiable', 'entailed', 'not_entailed', or 'error'."
        )

    trace = result["trace"]
    if not isinstance(trace, list):
        raise ValueError("Field 'trace' must be a list.")

    validated_trace: list[dict[str, Any]] = []
    for expected_step, step in enumerate(trace):
        if not isinstance(step, dict):
            raise ValueError("Each trace entry must be a dictionary.")
        action = step.get("action")
        if action not in DPLL_TRACE_ACTIONS:
            raise ValueError("Each trace action must be one of: " + ", ".join(DPLL_TRACE_ACTIONS) + ".")
        step_index = step.get("step")
        if not isinstance(step_index, int) or step_index != expected_step:
            raise ValueError("Trace steps must use consecutive integer indices starting at 0.")
        node_id = step.get("node_id")
        parent_id = step.get("parent_id")
        variable = step.get("variable")
        value = step.get("value")
        reason = step.get("reason")
        clause_index = step.get("clause_index")
        assignment = step.get("assignment", {})

        if node_id is not None and not isinstance(node_id, str):
            raise ValueError("Field 'node_id' must be a string or null.")
        if parent_id is not None and not isinstance(parent_id, str):
            raise ValueError("Field 'parent_id' must be a string or null.")
        if variable is not None and not isinstance(variable, str):
            raise ValueError("Field 'variable' must be a string or null.")
        if value is not None and not isinstance(value, bool):
            raise ValueError("Field 'value' must be a boolean or null.")
        if reason is not None and reason not in {"decision", "unit", "pure"}:
            raise ValueError("Field 'reason' must be 'decision', 'unit', 'pure', or null.")
        if clause_index is not None and (not isinstance(clause_index, int) or clause_index < 0):
            raise ValueError("Field 'clause_index' must be a non-negative integer or null.")
        if not isinstance(assignment, dict) or not all(
            isinstance(name, str) and isinstance(literal_value, bool)
            for name, literal_value in assignment.items()
        ):
            raise ValueError("Field 'assignment' must be a mapping from variables to booleans.")

        validated_trace.append(
            {
                "step": step_index,
                "action": action,
                "node_id": node_id,
                "parent_id": parent_id,
                "variable": variable,
                "value": value,
                "reason": reason,
                "clause_index": clause_index,
                "assignment": dict(assignment),
            }
        )

    assignment = result.get("assignment", {})
    if not isinstance(assignment, dict) or not all(
        isinstance(name, str) and isinstance(value, bool) for name, value in assignment.items()
    ):
        raise ValueError("Field 'assignment' must be a mapping from variables to booleans.")

    validated = {
        "algorithm": "dpll",
        "mode": result["mode"],
        "status": result["status"],
        "trace": validated_trace,
        "assignment": dict(assignment),
    }
    if "message" in result and result["message"] is not None:
        if not isinstance(result["message"], str):
            raise ValueError("Field 'message' must be a string when provided.")
        validated["message"] = result["message"]
    return validated


def run_dpll_solver(
    solver_fn: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
    *,
    port: int = 9414,
    debug: bool = True,
) -> None:
    """Run the minimal local `/solve` server used by the DPLL demo."""

    app = FastAPI(title="ai9414 DPLL solver")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.post("/solve")
    async def solve(payload: dict[str, Any]) -> JSONResponse:
        problem = payload.get("problem")
        options = payload.get("options", {})
        if not isinstance(problem, dict):
            return JSONResponse(
                {"message": "Request body must include a 'problem' object."},
                status_code=400,
            )
        if not isinstance(options, dict):
            return JSONResponse(
                {"message": "Request body field 'options' must be an object."},
                status_code=400,
            )

        try:
            validated_problem = validate_logic_payload(problem)
        except Exception as exc:
            return JSONResponse(
                {"message": f"Invalid logic payload: {exc}"},
                status_code=400,
            )

        try:
            result = solver_fn(validated_problem, dict(options))
        except Exception as exc:
            return JSONResponse(
                {"message": f"Solver raised an exception: {exc}"},
                status_code=500,
            )

        try:
            validated_result = validate_dpll_solver_result(result)
        except ValueError as exc:
            return JSONResponse({"message": str(exc)}, status_code=400)

        status_code = 200 if validated_result["status"] != "error" else 400
        return JSONResponse(validated_result, status_code=status_code)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="debug" if debug else "warning",
    )
