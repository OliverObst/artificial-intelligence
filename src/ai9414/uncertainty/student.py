"""Student-facing helpers for the live Bayes-filter corridor workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai9414.uncertainty.models import CorridorProblem, MotionModel, SensorModel
from ai9414.uncertainty.trace import (
    build_uncertainty_trace_from_problem,
    reference_motion_update_right,
    reference_normalise,
    reference_sensor_update,
)

Belief: TypeAlias = list[float]


def validate_uncertainty_payload(problem: dict[str, object]) -> dict[str, object]:
    """Validate and normalise an uncertainty problem payload from the browser."""

    return CorridorProblem.model_validate(problem).model_dump()


def run_uncertainty_solver(
    normalise_fn: Callable[[list[float]], list[float]] = reference_normalise,
    sensor_update_fn: Callable[[list[float], CorridorProblem, SensorModel, bool, str], list[float]] = reference_sensor_update,
    motion_update_right_fn: Callable[[list[float], MotionModel], list[float]] = reference_motion_update_right,
    *,
    port: int = 9414,
    debug: bool = True,
) -> None:
    """Run the minimal local `/solve` server used by the uncertainty demo."""

    app = FastAPI(title="ai9414 Bayes filter solver")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.post("/solve")
    async def solve(payload: dict[str, object]) -> JSONResponse:
        problem = payload.get("problem")
        if not isinstance(problem, dict):
            return JSONResponse(
                {"message": "Request body must include a 'problem' object."},
                status_code=400,
            )

        try:
            validated_problem = validate_uncertainty_payload(problem)
            problem_model = CorridorProblem.model_validate(validated_problem)
        except Exception as exc:
            return JSONResponse(
                {"message": f"Invalid uncertainty payload: {exc}"},
                status_code=400,
            )

        try:
            trace_bundle = build_uncertainty_trace_from_problem(
                problem_model,
                title=problem_model.title or "Live Python Bayes filter",
                subtitle="Trace returned by your local Python Bayes filter.",
                normalise_fn=normalise_fn,
                sensor_update_fn=sensor_update_fn,
                motion_update_right_fn=motion_update_right_fn,
                trace_id="uncertainty-live",
            )
        except NotImplementedError as exc:
            return JSONResponse({"message": str(exc)}, status_code=400)
        except ValueError as exc:
            return JSONResponse({"message": str(exc)}, status_code=400)
        except Exception as exc:
            return JSONResponse(
                {"message": f"Solver raised an exception: {exc}"},
                status_code=500,
            )

        return JSONResponse(
            {
                "algorithm": "bayes_filter",
                "status": "complete",
                "trace_bundle": trace_bundle.model_dump(),
            },
            status_code=200,
        )

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="debug" if debug else "warning",
    )


__all__ = [
    "Belief",
    "reference_motion_update_right",
    "reference_normalise",
    "reference_sensor_update",
    "run_uncertainty_solver",
    "validate_uncertainty_payload",
]

