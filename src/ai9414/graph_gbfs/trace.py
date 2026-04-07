"""Trace construction for the spatial graph greedy best-first demo."""

from __future__ import annotations

import copy
from typing import Any

from ai9414.core.models import TraceBundle, TraceStep, TraceSummary
from ai9414.graph_gbfs.models import GraphGbfsExample
from ai9414.graph_gbfs.solver import ALGORITHM_LABEL, ALGORITHM_NOTE, build_position_map, heuristic_to_goal, solve_graph_gbfs
from ai9414.search.models import WeightedGraph


def _layout_tree(nodes: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    children: dict[str | None, list[str]] = {}
    depth_map: dict[str, int] = {}
    order_map: dict[str, int] = {}
    for node in nodes:
        children.setdefault(node["parent"], []).append(node["tree_id"])
        depth_map[node["tree_id"]] = int(node["depth"])
        order_map[node["tree_id"]] = int(node["order"])

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


def build_blank_graph_gbfs_bundle(graph: WeightedGraph) -> TraceBundle:
    start_heuristic = heuristic_to_goal(build_position_map(graph), graph.goal, graph.start)
    initial_state = {
        "example_title": "Generated graph",
        "example_subtitle": "Generate a graph, then use Solve with Python to run greedy best-first search on the same graph.",
        "algorithm_label": ALGORITHM_LABEL,
        "algorithm_note": ALGORITHM_NOTE,
        "goal_label": "Find any path from start to goal",
        "graph": graph.model_dump(),
        "tree": {
            "nodes": [
                {
                    "tree_id": "t0",
                    "graph_node": graph.start,
                    "parent": None,
                    "depth": 0,
                    "path_cost": 0,
                    "status": "active",
                    "order": 0,
                    "x": 0.5,
                    "y": 0.12,
                    "terminal": False,
                }
            ]
        },
        "search": {
            "active_tree_node": "t0",
            "active_tree_path": ["t0"],
            "best_tree_path": [],
            "final_tree_path": [],
            "current_graph_path": [graph.start],
            "best_graph_path": [],
            "final_graph_path": [],
            "visited_order": [graph.start],
            "explored_graph_edges": [],
            "considered_edge": None,
            "current_cost": 0.0,
            "current_heuristic": round(start_heuristic, 3),
            "best_cost": None,
            "explored_count": 1,
            "current_depth": 0,
            "status": "searching",
            "found": False,
        },
        "stats": {"expanded": 0, "enqueued": 1},
    }
    return TraceBundle(
        app_type="graph_gbfs",
        trace_id="graph-gbfs-empty",
        is_complete=True,
        initial_state=initial_state,
        summary=TraceSummary(step_count=0, result="ready"),
        steps=[],
    )


def build_graph_gbfs_trace_from_definition(
    graph: WeightedGraph,
    *,
    title: str,
    subtitle: str,
) -> TraceBundle:
    result = solve_graph_gbfs(graph)
    all_tree_nodes = result.raw_steps[-1].snapshot["tree"]["nodes"] if result.raw_steps else result.initial_state["tree"]["nodes"]
    layout = _layout_tree(all_tree_nodes)

    initial_state = copy.deepcopy(result.initial_state)
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
        app_type="graph_gbfs",
        trace_id=result.trace_id,
        is_complete=True,
        initial_state=initial_state,
        summary=TraceSummary(step_count=len(steps), result=result.status),
        steps=steps,
    )


def build_graph_gbfs_trace(example: GraphGbfsExample) -> TraceBundle:
    return build_graph_gbfs_trace_from_definition(
        example.graph,
        title=example.title,
        subtitle=example.subtitle,
    )
