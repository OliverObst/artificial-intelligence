"""Student-facing helpers for the live Bayes-filter workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai9414.uncertainty.models import UncertaintyProblem
from ai9414.uncertainty.trace import (
    build_uncertainty_trace_from_problem,
    reference_bayes_filter_step,
    reference_predict_belief,
    reference_update_belief,
)

Belief: TypeAlias = dict[str, float]
TransitionModel: TypeAlias = dict[str, dict[str, float]]
ObservationModel: TypeAlias = dict[str, dict[str, float]]


def validate_uncertainty_payload(problem: dict[str, object]) -> dict[str, object]:
    """Validate and normalise an uncertainty problem payload from the browser."""

    return UncertaintyProblem.model_validate(problem).model_dump()


def run_uncertainty_solver(
    predict_fn: Callable[[Belief, TransitionModel], Belief],
    update_fn: Callable[[Belief, str, ObservationModel], Belief],
    bayes_step_fn: Callable[[Belief, TransitionModel, str, ObservationModel], Belief],
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
            problem_model = UncertaintyProblem.model_validate(validated_problem)
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
                predict_fn=predict_fn,
                update_fn=update_fn,
                bayes_step_fn=bayes_step_fn,
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
    "ObservationModel",
    "TransitionModel",
    "reference_bayes_filter_step",
    "reference_predict_belief",
    "reference_update_belief",
    "run_uncertainty_solver",
    "validate_uncertainty_payload",
]
