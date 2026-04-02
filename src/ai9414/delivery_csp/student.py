"""Student-facing helpers for the delivery CSP workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai9414.delivery_csp.models import DeliveryCspProblem
from ai9414.delivery_csp.trace import build_delivery_csp_trace_from_events

DELIVERY_CSP_TRACE_ACTIONS: tuple[str, ...] = (
    "start",
    "select_variable",
    "try_value",
    "assign",
    "prune",
    "domain_wipeout",
    "backtrack",
    "unassign",
    "solution_found",
    "failure",
)


def validate_delivery_csp_payload(problem: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalise a delivery CSP payload from the browser."""

    return DeliveryCspProblem.model_validate(problem).to_payload()


def build_unimplemented_delivery_csp_result(message: str | None = None) -> dict[str, Any]:
    """Return a consistent placeholder result for an unfinished student solver."""

    return {
        "algorithm": "backtracking_forward_checking",
        "status": "error",
        "message": message
        or (
            "Implement solve_delivery_csp in solve_delivery_csp.py. Return the algorithm name, a status, and an event trace."
        ),
        "events": [],
        "assignment": {},
        "stats": {},
    }


def validate_delivery_csp_solver_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate the event trace returned by the student solver."""

    if not isinstance(result, dict):
        raise ValueError("Solver result must be a dictionary.")

    required = {"algorithm", "status"}
    missing = sorted(required - set(result))
    if missing:
        raise ValueError(f"Solver result is missing required key(s): {', '.join(missing)}.")

    if result["algorithm"] != "backtracking_forward_checking":
        raise ValueError("Field 'algorithm' must be 'backtracking_forward_checking'.")
    if result["status"] not in {"found", "not_found", "error"}:
        raise ValueError("Field 'status' must be 'found', 'not_found', or 'error'.")

    raw_events = result.get("events", result.get("trace", []))
    if not isinstance(raw_events, list):
        raise ValueError("Field 'events' must be a list.")

    validated_events: list[dict[str, Any]] = []
    for expected_step, event in enumerate(raw_events):
        if not isinstance(event, dict):
            raise ValueError("Each event must be a dictionary.")
        action = event.get("action")
        if action not in DELIVERY_CSP_TRACE_ACTIONS:
            raise ValueError("Each event action must be one of: " + ", ".join(DELIVERY_CSP_TRACE_ACTIONS) + ".")
        step_index = event.get("step")
        if not isinstance(step_index, int) or step_index != expected_step:
            raise ValueError("Event steps must use consecutive integer indices starting at 0.")

        validated_event: dict[str, Any] = {"step": step_index, "action": action}
        for field in ("variable", "value", "cause", "failed_variable"):
            value = event.get(field)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"Field '{field}' must be a string when provided.")
            if value is not None:
                validated_event[field] = value

        if "domain" in event:
            domain = event["domain"]
            if not isinstance(domain, list) or not all(isinstance(value_id, str) for value_id in domain):
                raise ValueError("Field 'domain' must be a list of assignment ids.")
            validated_event["domain"] = list(domain)

        if "changes" in event:
            changes = event["changes"]
            if not isinstance(changes, list):
                raise ValueError("Field 'changes' must be a list when provided.")
            validated_changes = []
            for change in changes:
                if not isinstance(change, dict):
                    raise ValueError("Each domain change must be a dictionary.")
                variable = change.get("variable")
                removed = change.get("removed", [])
                new_domain = change.get("new_domain", [])
                if not isinstance(variable, str):
                    raise ValueError("Each domain change must include a string 'variable'.")
                if not isinstance(removed, list) or not all(isinstance(value_id, str) for value_id in removed):
                    raise ValueError("Each domain change 'removed' field must be a list of assignment ids.")
                if not isinstance(new_domain, list) or not all(isinstance(value_id, str) for value_id in new_domain):
                    raise ValueError("Each domain change 'new_domain' field must be a list of assignment ids.")
                validated_changes.append(
                    {"variable": variable, "removed": list(removed), "new_domain": list(new_domain)}
                )
            validated_event["changes"] = validated_changes

        if "assignments" in event:
            assignments = event["assignments"]
            if not isinstance(assignments, dict) or not all(
                isinstance(delivery, str) and isinstance(value_id, str) for delivery, value_id in assignments.items()
            ):
                raise ValueError("Field 'assignments' must map deliveries to assignment ids.")
            validated_event["assignments"] = dict(assignments)

        validated_events.append(validated_event)

    assignment = result.get("assignment", {})
    if not isinstance(assignment, dict) or not all(
        isinstance(delivery, str) and isinstance(value_id, str) for delivery, value_id in assignment.items()
    ):
        raise ValueError("Field 'assignment' must map deliveries to assignment ids.")

    stats = result.get("stats", {})
    if not isinstance(stats, dict):
        raise ValueError("Field 'stats' must be an object when provided.")
    validated_stats: dict[str, int] = {}
    for key in ("assignments", "prunes", "backtracks", "wipeouts"):
        if key in stats:
            value = stats[key]
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"Field 'stats.{key}' must be a non-negative integer.")
            validated_stats[key] = value

    validated = {
        "algorithm": "backtracking_forward_checking",
        "status": result["status"],
        "events": validated_events,
        "assignment": dict(assignment),
        "stats": validated_stats,
    }
    if "message" in result and result["message"] is not None:
        if not isinstance(result["message"], str):
            raise ValueError("Field 'message' must be a string when provided.")
        validated["message"] = result["message"]
    return validated


def run_delivery_csp_solver(
    solver_fn: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
    *,
    port: int = 9414,
    debug: bool = True,
) -> None:
    """Run the minimal local `/solve` server used by the delivery CSP demo."""

    app = FastAPI(title="ai9414 delivery CSP solver")
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
            return JSONResponse({"message": "Request body must include a 'problem' object."}, status_code=400)
        if not isinstance(options, dict):
            return JSONResponse({"message": "Request body field 'options' must be an object."}, status_code=400)

        try:
            validated_problem = validate_delivery_csp_payload(problem)
            problem_model = DeliveryCspProblem.model_validate(validated_problem)
        except Exception as exc:
            return JSONResponse({"message": f"Invalid delivery CSP payload: {exc}"}, status_code=400)

        try:
            result = solver_fn(validated_problem, dict(options))
        except Exception as exc:
            return JSONResponse({"message": f"Solver raised an exception: {exc}"}, status_code=500)

        try:
            validated_result = validate_delivery_csp_solver_result(result)
            bundle = build_delivery_csp_trace_from_events(
                problem_model,
                events=validated_result["events"],
                status=validated_result["status"],
                assignment=validated_result["assignment"],
                stats=validated_result["stats"],
                title=problem_model.title or "Live Python delivery CSP",
                subtitle="Trace returned by your local Python delivery scheduling solver.",
                trace_id="delivery-csp-live",
                live_trace=True,
            )
        except ValueError as exc:
            return JSONResponse({"message": str(exc)}, status_code=400)

        response_payload = {**validated_result, "trace_bundle": bundle.model_dump()}
        status_code = 200 if validated_result["status"] in {"found", "not_found"} else 400
        return JSONResponse(response_payload, status_code=status_code)

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="debug" if debug else "warning")
