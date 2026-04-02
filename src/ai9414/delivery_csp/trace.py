"""Trace construction helpers for the delivery scheduling CSP demo."""

from __future__ import annotations

import copy
from typing import Any
from uuid import uuid4

from ai9414.core.models import TraceBundle, TraceStep, TraceSummary
from ai9414.delivery_csp.models import DeliveryCspExample, DeliveryCspProblem
from ai9414.delivery_csp.solver import (
    ALGORITHM_LABEL,
    ALGORITHM_NAME,
    ALGORITHM_NOTE,
    solve_delivery_csp_problem,
)


def build_delivery_csp_trace(
    example: DeliveryCspExample,
    *,
    algorithm: str = ALGORITHM_NAME,
    variable_ordering: str = "fixed",
    value_ordering: str = "default",
    random_seed: int = 7,
) -> TraceBundle:
    return build_delivery_csp_trace_from_problem(
        example.problem,
        title=example.title,
        subtitle=example.subtitle,
        algorithm=algorithm,
        variable_ordering=variable_ordering,
        value_ordering=value_ordering,
        random_seed=random_seed,
    )


def build_delivery_csp_trace_from_problem(
    problem: DeliveryCspProblem,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    algorithm: str = ALGORITHM_NAME,
    variable_ordering: str = "fixed",
    value_ordering: str = "default",
    random_seed: int = 7,
) -> TraceBundle:
    result = solve_delivery_csp_problem(
        problem,
        algorithm=algorithm,
        variable_ordering=variable_ordering,
        value_ordering=value_ordering,
        random_seed=random_seed,
    )
    return build_delivery_csp_trace_from_events(
        problem,
        events=result["events"],
        status=result["status"],
        assignment=result.get("assignment", {}),
        stats=result.get("stats", {}),
        title=title,
        subtitle=subtitle,
    )


def build_delivery_csp_trace_from_events(
    problem: DeliveryCspProblem,
    *,
    events: list[dict[str, Any]],
    status: str,
    assignment: dict[str, str] | None = None,
    stats: dict[str, int] | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    trace_id: str | None = None,
    live_trace: bool = False,
) -> TraceBundle:
    deliveries = [delivery.id for delivery in problem.deliveries]
    delivery_map = problem.delivery_map()
    value_map = problem.value_map()
    domains = {delivery.id: list(problem.domains[delivery.id]) for delivery in problem.deliveries}
    assignments: dict[str, str] = {}
    focus_variable: str | None = None
    failed_variable: str | None = None
    last_changes: list[dict[str, Any]] = []
    trace_entries: list[dict[str, Any]] = []
    current_stats = {"assignments": 0, "prunes": 0, "backtracks": 0, "wipeouts": 0}
    if stats:
        for key in current_stats:
            current_stats[key] = 0

    tree_nodes: dict[str, dict[str, Any]] = {
        "t0": {
            "tree_id": "t0",
            "graph_node": "start",
            "assignment_text": "No assignments",
            "parent": None,
            "depth": 0,
            "status": "active",
            "order": 0,
        }
    }
    tree_order = ["t0"]
    active_tree_node: str | None = "t0"
    active_tree_path: list[str] = ["t0"]
    final_tree_path: list[str] = []
    state_stack: list[dict[str, Any]] = []
    search_status = "ready"
    result_label: str | None = None

    def format_domain(value_ids: list[str]) -> str:
        labels = [value_map[value_id].label for value_id in value_ids]
        return "{" + ", ".join(labels) + "}"

    def format_name(delivery_id: str) -> str:
        return delivery_map[delivery_id].label

    def format_value(value_id: str) -> str:
        return value_map[value_id].label

    def format_list(items: list[str]) -> str:
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"

    def assignment_text() -> str:
        if not assignments:
            return "No assignments"
        return ", ".join(
            f"{delivery_map[delivery_id].short_label}: {format_value(value_id)}"
            for delivery_id, value_id in assignments.items()
        )

    def build_candidate_map() -> dict[str, list[str]]:
        candidate_map = {value.id: [] for value in problem.values}
        for delivery_id in deliveries:
            if delivery_id in assignments:
                continue
            for value_id in domains[delivery_id]:
                candidate_map[value_id].append(delivery_id)
        return candidate_map

    def snapshot() -> dict[str, Any]:
        variable_rows = []
        for delivery_id in deliveries:
            assigned_value = assignments.get(delivery_id)
            domain = list(domains[delivery_id])
            is_failed = delivery_id == failed_variable or len(domain) == 0
            if is_failed:
                row_status = "wipeout"
            elif assigned_value is not None:
                row_status = "assigned"
            elif delivery_id == focus_variable:
                row_status = "focus"
            elif any(change["variable"] == delivery_id for change in last_changes):
                row_status = "reduced"
            else:
                row_status = "unchanged"
            variable_rows.append(
                {
                    "variable": delivery_id,
                    "label": delivery_map[delivery_id].label,
                    "short_label": delivery_map[delivery_id].short_label,
                    "colour": delivery_map[delivery_id].colour,
                    "domain": domain,
                    "domain_labels": [format_value(value_id) for value_id in domain],
                    "assigned_value": assigned_value,
                    "assigned_label": format_value(assigned_value) if assigned_value else None,
                    "status": row_status,
                    "changed": any(change["variable"] == delivery_id for change in last_changes),
                    "is_focus": delivery_id == focus_variable,
                    "is_failed": is_failed,
                }
            )

        placements = [
            {
                "delivery": delivery_id,
                "label": delivery_map[delivery_id].label,
                "short_label": delivery_map[delivery_id].short_label,
                "colour": delivery_map[delivery_id].colour,
                "value": value_id,
                "slot": value_map[value_id].slot,
                "room": value_map[value_id].room,
                "value_label": value_map[value_id].label,
            }
            for delivery_id, value_id in assignments.items()
        ]

        return {
            "tree": {"nodes": [copy.deepcopy(tree_nodes[tree_id]) for tree_id in tree_order]},
            "search": {
                "active_tree_node": active_tree_node,
                "active_tree_path": list(active_tree_path),
                "best_tree_path": [],
                "final_tree_path": list(final_tree_path),
                "finished": search_status in {"solved", "failed"},
                "status": search_status,
                "result": result_label,
            },
            "delivery_csp": {
                "variables": variable_rows,
                "assignments": copy.deepcopy(assignments),
                "domains": copy.deepcopy(domains),
                "focus_variable": focus_variable,
                "failed_variable": failed_variable,
                "last_changes": copy.deepcopy(last_changes),
                "trace_entries": copy.deepcopy(trace_entries),
                "current_entry_index": len(trace_entries) - 1 if trace_entries else None,
                "placements": placements,
                "candidate_map": build_candidate_map(),
            },
            "stats": copy.deepcopy(current_stats),
        }

    def record_trace_entry(event: dict[str, Any]) -> tuple[str, str, str]:
        action = event["action"]
        variable = event.get("variable")
        value_id = event.get("value")
        changes = event.get("changes", [])
        if action == "start":
            label = "Start search"
            annotation = "The deliveries, slot-room options, and scheduling constraints are ready. The solver will now branch and prune systematically."
            note = ALGORITHM_NOTE
            text = "Start backtracking search with forward checking."
        elif action == "select_variable":
            label = f"Select {format_name(variable)}"
            annotation = f"Choose the next unassigned delivery. {format_name(variable)} currently has domain {format_domain(event.get('domain', []))}."
            note = "Variable ordering changes which delivery becomes informative first."
            text = f"Select {format_name(variable)}."
        elif action == "try_value":
            label = f"Try {format_name(variable)}"
            annotation = f"Consider assigning {format_name(variable)} to {format_value(value_id)}."
            note = "A locally legal slot does not guarantee the whole schedule will still be solvable."
            text = f"Try {format_name(variable)} = {format_value(value_id)}."
        elif action == "assign":
            label = f"Assign {format_name(variable)}"
            annotation = f"Assign {format_name(variable)} to {format_value(value_id)} and then propagate that choice to future deliveries."
            note = "Forward checking removes future values that can no longer coexist with this assignment."
            text = f"Assign {format_name(variable)} = {format_value(value_id)}."
        elif action == "prune":
            pruned = [format_name(change["variable"]) for change in changes]
            label = "Forward check"
            annotation = (
                f"Forward checking removes incompatible slot-room options from {format_list(pruned)} "
                f"after assigning {format_name(variable)}."
            )
            note = "The schedule board on the right loses candidate badges immediately when a delivery becomes impossible in some cell."
            text = f"Forward checking prunes future options for {format_list(pruned)}."
        elif action == "domain_wipeout":
            label = f"Domain wipe-out at {format_name(variable)}"
            annotation = f"{format_name(variable)} has no slot-room options left after propagation, so this branch cannot produce a valid schedule."
            note = "A domain wipe-out means the current partial schedule is inconsistent with the remaining constraints."
            text = f"{format_name(variable)} has no time slots left. This branch fails."
        elif action == "backtrack":
            label = f"Backtrack from {format_name(variable)}"
            annotation = f"Undo the current branch for {format_name(variable)} and return to the previous choice point."
            note = "Backtracking is the normal way a CSP solver explores alternatives systematically."
            text = f"Backtrack from {format_name(variable)} = {format_value(value_id)}."
        elif action == "unassign":
            label = f"Undo {format_name(variable)}"
            annotation = f"Restore the previous domains and remove {format_name(variable)} from the partial schedule."
            note = "Undoing an assignment also restores every slot-room option that was pruned because of it."
            text = f"Undo {format_name(variable)}."
        elif action == "solution_found":
            label = "Solution found"
            annotation = "Every delivery has a legal room and time slot, and all scheduling constraints are satisfied."
            note = "A solution is a complete assignment that satisfies every ordering, incompatibility, and capacity restriction."
            text = "A complete delivery schedule has been found."
        else:
            label = "Failure"
            annotation = "Every branch has failed. The current delivery scheduling CSP is unsatisfiable under these settings."
            note = "Unsatisfiable schedules are still useful because they show where local choices eventually block every remaining option."
            text = "Every branch fails. The schedule is unsatisfiable."

        trace_entries.append({"step": event["step"], "action": action, "text": text})
        return label, annotation, note

    def push_state() -> None:
        state_stack.append(
            {
                "assignments": copy.deepcopy(assignments),
                "domains": copy.deepcopy(domains),
                "active_tree_node": active_tree_node,
                "active_tree_path": list(active_tree_path),
                "focus_variable": focus_variable,
            }
        )

    def pop_state() -> None:
        nonlocal active_tree_node, active_tree_path, focus_variable
        if not state_stack:
            return
        restored = state_stack.pop()
        assignments.clear()
        assignments.update(restored["assignments"])
        domains.clear()
        domains.update(restored["domains"])
        active_tree_node = restored["active_tree_node"]
        active_tree_path = list(restored["active_tree_path"])
        focus_variable = restored["focus_variable"]

    initial_state = {
        "example_title": title or problem.title,
        "example_subtitle": subtitle or problem.subtitle,
        "algorithm_label": ALGORITHM_LABEL,
        "algorithm_note": ALGORITHM_NOTE,
        "goal_label": "Assign every delivery to a legal room and time slot",
        "delivery_problem": problem.to_payload(),
        "options": {"algorithm": ALGORITHM_NAME},
        **snapshot(),
    }

    steps: list[TraceStep] = []
    for index, event in enumerate(events):
        action = event["action"]
        last_changes = []
        failed_variable = None

        if action == "start":
            search_status = "searching"
            result_label = None
            active_tree_node = "t0"
            active_tree_path = ["t0"]
            if tree_nodes["t0"]["status"] != "solution":
                tree_nodes["t0"]["status"] = "active"
        elif action == "select_variable":
            focus_variable = event.get("variable")
            search_status = "branching"
        elif action == "try_value":
            focus_variable = event.get("variable")
            search_status = "branching"
        elif action == "assign":
            delivery_id = str(event["variable"])
            value_id = str(event["value"])
            push_state()
            assignments[delivery_id] = value_id
            domains[delivery_id] = [value_id]
            current_stats["assignments"] += 1
            new_tree_id = f"t{len(tree_order)}"
            tree_nodes[new_tree_id] = {
                "tree_id": new_tree_id,
                "graph_node": delivery_map[delivery_id].short_label,
                "assignment_text": assignment_text(),
                "parent": active_tree_node,
                "depth": len(assignments),
                "status": "active",
                "order": len(tree_order),
            }
            tree_order.append(new_tree_id)
            if active_tree_node in tree_nodes and tree_nodes[active_tree_node]["status"] not in {"solution", "contradiction"}:
                tree_nodes[active_tree_node]["status"] = "branched"
            active_tree_node = new_tree_id
            active_tree_path = list(active_tree_path) + [new_tree_id]
            focus_variable = delivery_id
            search_status = "propagating"
        elif action == "prune":
            last_changes = copy.deepcopy(event.get("changes", []))
            for change in last_changes:
                delivery_id = change["variable"]
                removed = set(change.get("removed", []))
                domains[delivery_id] = [value_id for value_id in domains[delivery_id] if value_id not in removed]
                current_stats["prunes"] += len(removed)
            search_status = "propagating"
        elif action == "domain_wipeout":
            failed_variable = str(event["variable"])
            if active_tree_node in tree_nodes:
                tree_nodes[active_tree_node]["status"] = "contradiction"
            current_stats["wipeouts"] += 1
            search_status = "backtracking"
        elif action == "backtrack":
            current_stats["backtracks"] += 1
            if active_tree_node in tree_nodes and tree_nodes[active_tree_node]["status"] != "contradiction":
                tree_nodes[active_tree_node]["status"] = "backtracked"
            search_status = "backtracking"
        elif action == "unassign":
            pop_state()
            search_status = "searching"
            if active_tree_node in tree_nodes and tree_nodes[active_tree_node]["status"] not in {"solution", "contradiction"}:
                tree_nodes[active_tree_node]["status"] = "active"
        elif action == "solution_found":
            assignments.clear()
            assignments.update({str(delivery_id): str(value_id) for delivery_id, value_id in (assignment or event.get("assignments", {})).items()})
            for delivery_id in assignments:
                domains[delivery_id] = [assignments[delivery_id]]
            if active_tree_node in tree_nodes:
                tree_nodes[active_tree_node]["status"] = "solution"
            final_tree_path = list(active_tree_path)
            search_status = "solved"
            result_label = "found"
        elif action == "failure":
            search_status = "failed"
            result_label = "not_found"

        label, annotation, note = record_trace_entry(event)
        steps.append(
            TraceStep(
                index=index,
                event_type=action,
                label=label,
                annotation=annotation,
                teaching_note=note,
                state_patch=snapshot(),
            )
        )

    layout = _layout_tree([tree_nodes[tree_id] for tree_id in tree_order])
    initial_state["tree"]["nodes"] = [
        {**node, "x": layout[node["tree_id"]][0], "y": layout[node["tree_id"]][1]}
        for node in initial_state["tree"]["nodes"]
    ]
    for step in steps:
        step.state_patch["tree"]["nodes"] = [
            {**node, "x": layout[node["tree_id"]][0], "y": layout[node["tree_id"]][1]}
            for node in step.state_patch["tree"]["nodes"]
        ]

    result_value = "found" if status == "found" else "not_found"
    return TraceBundle(
        app_type="delivery_csp",
        trace_id=trace_id or ("delivery-csp-live" if live_trace else f"delivery-csp-{uuid4().hex[:8]}"),
        is_complete=True,
        initial_state=initial_state,
        summary=TraceSummary(step_count=len(steps), result=result_value),
        steps=steps,
    )


def _layout_tree(nodes: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    children: dict[str | None, list[str]] = {}
    depth_map: dict[str, int] = {}
    order_map: dict[str, int] = {}
    for node in nodes:
        tree_id = node["tree_id"]
        parent = node.get("parent")
        children.setdefault(parent, []).append(tree_id)
        depth_map[tree_id] = int(node.get("depth", 0))
        order_map[tree_id] = int(node.get("order", 0))

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
            0.16 + (depth_map[tree_id] / max(max_depth, 1)) * 0.72,
        )
        for tree_id, x in x_positions.items()
    }
