"""Trace construction helpers for the STRIPS planning demo."""

from __future__ import annotations

import copy

from ai9414.core.models import TraceBundle, TraceStep, TraceSummary
from ai9414.strips.models import StripsExample, StripsProblem
from ai9414.strips.solver import (
    ALGORITHM_LABEL,
    ALGORITHM_NOTE,
    GroundedAction,
    PlannerResult,
    apply_action,
    build_planning_snapshot,
    goal_satisfied,
    initial_state,
    solve_strips_problem,
)


def build_strips_trace(example: StripsExample) -> TraceBundle:
    return build_strips_trace_from_problem(
        example.problem,
        title=example.title,
        subtitle=example.subtitle,
    )


def build_strips_trace_from_problem(
    problem: StripsProblem,
    *,
    title: str | None = None,
    subtitle: str | None = None,
) -> TraceBundle:
    return build_strips_trace_from_result(
        solve_strips_problem(problem),
        title=title,
        subtitle=subtitle,
    )


def build_strips_trace_from_validated_plan(
    problem: StripsProblem,
    *,
    plan: list[GroundedAction],
    status: str,
    search_trace: list | None = None,
    stats: dict[str, int] | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    trace_id: str | None = None,
) -> TraceBundle:
    result = PlannerResult(
        trace_id=trace_id or "strips-live",
        problem=problem,
        initial_state=initial_state(problem),
        plan=list(plan),
        search_trace=list(search_trace or []),
        status=status,
        stats=copy.deepcopy(stats or {"expanded_states": 0, "generated_states": 1, "frontier_peak": 1}),
    )
    return build_strips_trace_from_result(result, title=title, subtitle=subtitle, live_trace=True)


def build_strips_trace_from_result(
    result: PlannerResult,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    live_trace: bool = False,
) -> TraceBundle:
    problem = result.problem
    start_snapshot = build_planning_snapshot(
        problem,
        state=result.initial_state,
        plan=[],
        selected_action=None,
        plan_index=0,
        search_trace=[],
        stats={"expanded_states": 0, "generated_states": 1, "frontier_peak": 1},
    )
    initial_state_payload = {
        "example_title": title or problem.title,
        "example_subtitle": subtitle or problem.subtitle,
        "algorithm_label": ALGORITHM_LABEL,
        "algorithm_note": ALGORITHM_NOTE,
        "goal_label": "Deliver the parcel to the lab",
        "strips_problem": problem.model_dump(),
        **start_snapshot,
    }

    steps: list[TraceStep] = []
    if result.status == "found":
        plan_found_snapshot = build_planning_snapshot(
            problem,
            state=result.initial_state,
            plan=result.plan,
            selected_action=result.plan[0] if result.plan else None,
            plan_index=0,
            search_trace=result.search_trace,
            stats=result.stats,
        )
        plan_found_snapshot["search"]["status"] = "plan ready"
        steps.append(
            TraceStep(
                index=0,
                event_type="plan_found",
                label="Plan found",
                annotation=(
                    f"BFS found a plan with {len(result.plan)} action"
                    f"{'' if len(result.plan) == 1 else 's'}. Step through it to see how each symbolic action changes the world."
                ),
                teaching_note=(
                    "The plan is a sequence of grounded STRIPS actions. The world view on the right is derived from those predicates."
                ),
                state_patch=plan_found_snapshot,
            )
        )

        state = result.initial_state
        for action_index, action in enumerate(result.plan, start=1):
            state = apply_action(state, action)
            snapshot = build_planning_snapshot(
                problem,
                state=state,
                plan=result.plan,
                selected_action=action,
                plan_index=action_index,
                search_trace=result.search_trace,
                stats=result.stats,
            )
            snapshot["search"]["status"] = "goal reached" if goal_satisfied(problem, state) else "executing"
            steps.append(
                TraceStep(
                    index=len(steps),
                    event_type="apply_action",
                    label=action.signature,
                    annotation=(
                        "Apply "
                        + action.signature
                        + (
                            ". The goal fact is now true."
                            if goal_satisfied(problem, state)
                            else ". The planner advances to the next symbolic state."
                        )
                    ),
                    teaching_note=(
                        "Every step updates both the predicate set and the rendered world, because the world is only a view of the symbolic state."
                    ),
                    state_patch=snapshot,
                )
            )
    else:
        no_plan_snapshot = build_planning_snapshot(
            problem,
            state=result.initial_state,
            plan=[],
            selected_action=None,
            plan_index=0,
            search_trace=result.search_trace,
            stats=result.stats,
        )
        no_plan_snapshot["search"]["status"] = "no plan"
        steps.append(
            TraceStep(
                index=0,
                event_type="plan_failed",
                label="No plan found",
                annotation="The planner exhausted the reachable symbolic states without satisfying the goal.",
                teaching_note="Planning fails when no action sequence can make the goal facts true.",
                state_patch=no_plan_snapshot,
            )
        )

    return TraceBundle(
        app_type="strips",
        trace_id=result.trace_id,
        is_complete=True,
        initial_state=initial_state_payload,
        summary=TraceSummary(step_count=len(steps), result="found" if result.status == "found" else result.status),
        steps=steps,
    )
