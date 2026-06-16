"""Trace helpers for the resolution/refutation demo."""

from __future__ import annotations

import copy

from ai9414.core.models import TraceBundle, TraceStep, TraceSummary
from ai9414.resolution.models import ResolutionExample, ResolutionProblem
from ai9414.resolution.solver import build_resolution_result


def build_resolution_trace(example: ResolutionExample) -> TraceBundle:
    return build_resolution_trace_from_problem(example.problem)


def build_resolution_trace_from_problem(problem: ResolutionProblem) -> TraceBundle:
    result = build_resolution_result(problem)
    steps = [
        TraceStep(
            index=index,
            event_type=raw_step.event_type,
            label=raw_step.label,
            annotation=raw_step.annotation,
            teaching_note=raw_step.teaching_note,
            state_patch=copy.deepcopy(raw_step.snapshot),
        )
        for index, raw_step in enumerate(result.raw_steps)
    ]
    return TraceBundle(
        app_type="resolution",
        trace_id=result.trace_id,
        is_complete=True,
        initial_state=result.initial_data,
        summary=TraceSummary(step_count=len(steps), result=result.status),
        steps=steps,
    )
