"""Student-facing helpers for the STRIPS planning live-Python workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai9414.strips.models import StripsProblem
from ai9414.strips.solver import (
    action_from_signature,
    apply_action,
    build_planning_snapshot,
    enumerate_applicable_actions,
    fact_payload,
    initial_state,
    render_fact,
    validate_action_plan,
)
from ai9414.strips.trace import build_strips_trace_from_validated_plan

STRIPS_TRACE_ACTIONS: tuple[str, ...] = (
    "expand",
    "goal",
)


def validate_strips_payload(problem: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalise a STRIPS problem payload from the browser."""

    return StripsProblem.model_validate(problem).model_dump()


def get_initial_facts(problem: dict[str, Any] | StripsProblem) -> list[tuple[str, ...]]:
    """Return the initial symbolic state as a sorted list of facts."""

    definition = problem if isinstance(problem, StripsProblem) else StripsProblem.model_validate(problem)
    return [tuple(fact) for fact in sorted(initial_state(definition))]


def get_applicable_actions(problem: dict[str, Any] | StripsProblem, facts: list[list[str]] | list[tuple[str, ...]]) -> list[str]:
    """Return grounded STRIPS actions that are applicable in the given symbolic state."""

    definition = problem if isinstance(problem, StripsProblem) else StripsProblem.model_validate(problem)
    state = frozenset(tuple(fact) for fact in facts)
    return [action.signature for action in enumerate_applicable_actions(definition, state)]


def apply_action_signature(
    problem: dict[str, Any] | StripsProblem,
    facts: list[list[str]] | list[tuple[str, ...]],
    signature: str,
) -> list[tuple[str, ...]]:
    """Apply one grounded action to a symbolic state and return the successor facts."""

    definition = problem if isinstance(problem, StripsProblem) else StripsProblem.model_validate(problem)
    state = frozenset(tuple(fact) for fact in facts)
    action = action_from_signature(definition, state, signature)
    return [tuple(fact) for fact in sorted(apply_action(state, action))]


def build_unimplemented_strips_result(message: str | None = None) -> dict[str, Any]:
    """Return a consistent placeholder result for an unfinished student planner."""

    return {
        "algorithm": "strips_bfs",
        "status": "error",
        "message": message
        or (
            "Implement solve_planner in solve_strips.py. Return algorithm, status, and a grounded action plan."
        ),
        "plan": [],
        "stats": {},
        "search_trace": [],
    }


def validate_strips_solver_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate the student planner result before it is replayed in the browser."""

    if not isinstance(result, dict):
        raise ValueError("Solver result must be a dictionary.")

    required = {"algorithm", "status", "plan"}
    missing = sorted(required - set(result))
    if missing:
        raise ValueError(f"Solver result is missing required key(s): {', '.join(missing)}.")

    if result["algorithm"] != "strips_bfs":
        raise ValueError("Field 'algorithm' must be 'strips_bfs'.")
    if result["status"] not in {"found", "not_found", "error"}:
        raise ValueError("Field 'status' must be 'found', 'not_found', or 'error'.")
    if not isinstance(result["plan"], list) or not all(isinstance(item, str) for item in result["plan"]):
        raise ValueError("Field 'plan' must be a list of grounded action strings.")
    if result["status"] == "found" and not result["plan"]:
        raise ValueError("A result with status 'found' must include a non-empty plan.")
    if result["status"] == "not_found" and result["plan"]:
        raise ValueError("A result with status 'not_found' must not include a plan.")

    stats = result.get("stats", {})
    if not isinstance(stats, dict):
        raise ValueError("Field 'stats' must be an object when provided.")
    validated_stats: dict[str, int] = {}
    for key in ("expanded_states", "generated_states", "frontier_peak"):
        if key in stats:
            value = stats[key]
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"Field 'stats.{key}' must be a non-negative integer.")
            validated_stats[key] = value

    search_trace = result.get("search_trace", [])
    if not isinstance(search_trace, list):
        raise ValueError("Field 'search_trace' must be a list when provided.")
    validated_trace: list[dict[str, Any]] = []
    for expected_step, step in enumerate(search_trace):
        if not isinstance(step, dict):
            raise ValueError("Each search_trace entry must be a dictionary.")
        action = step.get("action")
        if action not in STRIPS_TRACE_ACTIONS:
            raise ValueError("Each search_trace action must be one of: " + ", ".join(STRIPS_TRACE_ACTIONS) + ".")
        step_index = step.get("step")
        if not isinstance(step_index, int) or step_index != expected_step:
            raise ValueError("search_trace steps must use consecutive integer indices starting at 0.")
        facts = step.get("facts")
        plan_prefix = step.get("plan_prefix", [])
        frontier_size = step.get("frontier_size", 0)
        if not isinstance(facts, list) or not all(isinstance(item, (list, tuple)) for item in facts):
            raise ValueError("Each search_trace entry must include 'facts' as a list of fact tuples.")
        if not isinstance(plan_prefix, list) or not all(isinstance(item, str) for item in plan_prefix):
            raise ValueError("Field 'plan_prefix' must be a list of grounded action strings.")
        if not isinstance(frontier_size, int) or frontier_size < 0:
            raise ValueError("Field 'frontier_size' must be a non-negative integer.")
        validated_trace.append(
            {
                "step": step_index,
                "action": action,
                "facts": [tuple(fact) for fact in facts],
                "plan_prefix": list(plan_prefix),
                "frontier_size": frontier_size,
            }
        )

    validated = {
        "algorithm": "strips_bfs",
        "status": result["status"],
        "plan": list(result["plan"]),
        "stats": validated_stats,
        "search_trace": validated_trace,
    }
    if "message" in result and result["message"] is not None:
        if not isinstance(result["message"], str):
            raise ValueError("Field 'message' must be a string when provided.")
        validated["message"] = result["message"]
    return validated


def run_strips_solver(
    solver_fn: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    port: int = 9414,
    debug: bool = True,
) -> None:
    """Run the minimal local `/solve` server used by the STRIPS planning demo."""

    app = FastAPI(title="ai9414 STRIPS planner")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.post("/solve")
    async def solve(payload: dict[str, Any]) -> JSONResponse:
        problem = payload.get("problem")
        if not isinstance(problem, dict):
            return JSONResponse(
                {"message": "Request body must include a 'problem' object."},
                status_code=400,
            )

        try:
            validated_problem = validate_strips_payload(problem)
            problem_model = StripsProblem.model_validate(validated_problem)
        except Exception as exc:
            return JSONResponse(
                {"message": f"Invalid STRIPS payload: {exc}"},
                status_code=400,
            )

        try:
            result = solver_fn(validated_problem)
        except Exception as exc:
            return JSONResponse(
                {"message": f"Solver raised an exception: {exc}"},
                status_code=500,
            )

        try:
            validated_result = validate_strips_solver_result(result)
            validated_plan = validate_action_plan(problem_model, validated_result["plan"])
            bundle = build_strips_trace_from_validated_plan(
                problem_model,
                plan=validated_plan,
                status=validated_result["status"],
                stats=validated_result["stats"],
                title=problem_model.title or "Live Python STRIPS",
                subtitle="Trace returned by your local Python planner.",
                trace_id="strips-live",
            )
        except ValueError as exc:
            return JSONResponse({"message": str(exc)}, status_code=400)

        response_payload = {
            **validated_result,
            "trace_bundle": bundle.model_dump(),
        }
        status_code = 200 if validated_result["status"] in {"found", "not_found"} else 400
        return JSONResponse(response_payload, status_code=status_code)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="debug" if debug else "warning",
    )
