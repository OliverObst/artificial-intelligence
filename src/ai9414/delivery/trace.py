"""Trace construction for the delivery DFS demo."""

from __future__ import annotations

import copy
from typing import Any

from ai9414.core.models import TraceBundle, TraceStep, TraceSummary
from ai9414.delivery.models import DeliveryExample
from ai9414.delivery.solver import solve_delivery
from ai9414.labyrinth.models import LabyrinthDefinition
from ai9414.labyrinth.trace import _layout_tree


def build_delivery_trace_from_definition(
    labyrinth: LabyrinthDefinition,
    *,
    title: str,
    subtitle: str,
    action_order: str = "straight_left_right",
    random_seed: int = 7,
) -> TraceBundle:
    result = solve_delivery(labyrinth, action_order=action_order, random_seed=random_seed)
    all_tree_nodes = result.raw_steps[-1].snapshot["tree"]["nodes"] if result.raw_steps else result.initial_state["tree"]["nodes"]
    layout = _layout_tree(all_tree_nodes)

    initial_state: dict[str, Any] = copy.deepcopy(result.initial_state)
    initial_state["example_title"] = title
    initial_state["example_subtitle"] = subtitle
    for node in initial_state["tree"]["nodes"]:
        node["x"], node["y"] = layout[node["tree_id"]]

    steps: list[TraceStep] = []
    for index, raw_step in enumerate(result.raw_steps):
        snapshot = copy.deepcopy(raw_step.snapshot)
        for node in snapshot["tree"]["nodes"]:
            node["x"], node["y"] = layout[node["tree_id"]]
        steps.append(
            TraceStep(
                index=index,
                event_type=raw_step.event_type,
                label=raw_step.label,
                annotation=raw_step.annotation,
                teaching_note=raw_step.teaching_note,
                state_patch=snapshot,
            )
        )

    return TraceBundle(
        app_type="delivery",
        trace_id=result.trace_id,
        is_complete=True,
        initial_state=initial_state,
        summary=TraceSummary(step_count=len(steps), result=result.status),
        steps=steps,
    )


def build_delivery_trace(
    example: DeliveryExample,
    *,
    action_order: str = "straight_left_right",
    random_seed: int = 7,
) -> TraceBundle:
    return build_delivery_trace_from_definition(
        example.labyrinth,
        title=example.title,
        subtitle=example.subtitle,
        action_order=action_order,
        random_seed=random_seed,
    )
