"""Trace construction helpers for the DPLL demo."""

from __future__ import annotations

import copy
from typing import Any

from ai9414.core.models import TraceBundle, TraceStep, TraceSummary
from ai9414.logic.models import LogicExample, LogicProblem
from ai9414.logic.solver import solve_dpll


def build_logic_trace(
    example: LogicExample,
    *,
    unit_propagation: bool = True,
    pure_literals: bool = False,
    variable_order: str = "alphabetical",
) -> TraceBundle:
    return build_logic_trace_from_problem(
        example.problem,
        title=example.title,
        subtitle=example.subtitle,
        unit_propagation=unit_propagation,
        pure_literals=pure_literals,
        variable_order=variable_order,
    )


def build_logic_trace_from_problem(
    problem: LogicProblem,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    unit_propagation: bool = True,
    pure_literals: bool = False,
    variable_order: str = "alphabetical",
) -> TraceBundle:
    result = solve_dpll(
        problem,
        unit_propagation=unit_propagation,
        pure_literals=pure_literals,
        variable_order=variable_order,
    )

    all_tree_nodes = result.initial_data["tree"]["nodes"]
    for raw_step in result.raw_steps:
        all_tree_nodes = raw_step.snapshot["tree"]["nodes"]
    layout = _layout_tree(all_tree_nodes)

    initial_state = copy.deepcopy(result.initial_data)
    if title is not None:
        initial_state["example_title"] = title
    if subtitle is not None:
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
        app_type="logic",
        trace_id=result.trace_id,
        is_complete=True,
        initial_state=initial_state,
        summary=TraceSummary(step_count=len(steps), result=result.status),
        steps=steps,
    )


def _layout_tree(nodes: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    children: dict[str | None, list[str]] = {}
    depth_map: dict[str, int] = {}
    for node in nodes:
        children.setdefault(node["parent"], []).append(node["tree_id"])
        depth_map[node["tree_id"]] = int(node["depth"])

    order_map = {node["tree_id"]: node["order"] for node in nodes}
    for siblings in children.values():
        siblings.sort(key=lambda tree_id: order_map[tree_id])

    x_positions: dict[str, float] = {}
    cursor = 0

    def assign(tree_id: str) -> float:
        nonlocal cursor
        branch = children.get(tree_id, [])
        if not branch:
            cursor += 1
            x_positions[tree_id] = float(cursor)
            return x_positions[tree_id]
        child_positions = [assign(child_id) for child_id in branch]
        x_positions[tree_id] = sum(child_positions) / len(child_positions)
        return x_positions[tree_id]

    for root_id in children.get(None, []):
        assign(root_id)

    max_x = max(x_positions.values(), default=1.0)
    max_depth = max(depth_map.values(), default=0)
    return {
        tree_id: (
            0.08 + ((x - 1) / max(max_x - 1, 1)) * 0.84,
            0.12 + (depth_map[tree_id] / max(max_depth, 1)) * 0.76,
        )
        for tree_id, x in x_positions.items()
    }
