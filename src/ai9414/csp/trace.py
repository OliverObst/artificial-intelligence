"""Trace construction helpers for the CSP demo."""

from __future__ import annotations

import copy
from typing import Any
from uuid import uuid4

from ai9414.core.models import TraceBundle, TraceStep, TraceSummary
from ai9414.csp.models import CspExample, CspProblem
from ai9414.csp.solver import ALGORITHM_LABEL, ALGORITHM_NAME, ALGORITHM_NOTE, solve_csp_problem


def build_csp_trace(
    example: CspExample,
    *,
    algorithm: str = ALGORITHM_NAME,
    variable_ordering: str = "fixed",
    value_ordering: str = "default",
    random_seed: int = 7,
) -> TraceBundle:
    return build_csp_trace_from_problem(
        example.problem,
        title=example.title,
        subtitle=example.subtitle,
        algorithm=algorithm,
        variable_ordering=variable_ordering,
        value_ordering=value_ordering,
        random_seed=random_seed,
    )


def build_csp_trace_from_problem(
    problem: CspProblem,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    algorithm: str = ALGORITHM_NAME,
    variable_ordering: str = "fixed",
    value_ordering: str = "default",
    random_seed: int = 7,
) -> TraceBundle:
    result = solve_csp_problem(
        problem,
        algorithm=algorithm,
        variable_ordering=variable_ordering,
        value_ordering=value_ordering,
        random_seed=random_seed,
    )
    return build_csp_trace_from_events(
        problem,
        events=result["events"],
        status=result["status"],
        assignment=result.get("assignment", {}),
        stats=result.get("stats", {}),
        title=title,
        subtitle=subtitle,
    )


def build_csp_trace_from_events(
    problem: CspProblem,
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
    regions = list(problem.regions)
    domains = {region: list(problem.domains[region]) for region in regions}
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

    def format_domain(colours: list[str]) -> str:
        return "{" + ", ".join(colours) + "}"

    def format_region_list(names: list[str]) -> str:
        if not names:
            return ""
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]} and {names[1]}"
        return ", ".join(names[:-1]) + f", and {names[-1]}"

    def assignment_text() -> str:
        if not assignments:
            return "No assignments"
        return ", ".join(f"{region} = {value}" for region, value in assignments.items())

    def snapshot() -> dict[str, Any]:
        variable_rows = []
        for region in regions:
            assigned_value = assignments.get(region)
            domain = list(domains[region])
            is_failed = region == failed_variable or len(domain) == 0
            if is_failed:
                row_status = "wipeout"
            elif assigned_value is not None:
                row_status = "assigned"
            elif region == focus_variable:
                row_status = "focus"
            elif any(change["variable"] == region for change in last_changes):
                row_status = "reduced"
            else:
                row_status = "unchanged"
            variable_rows.append(
                {
                    "variable": region,
                    "domain": domain,
                    "assigned_value": assigned_value,
                    "status": row_status,
                    "changed": any(change["variable"] == region for change in last_changes),
                    "is_focus": region == focus_variable,
                    "is_failed": is_failed,
                    "degree": len(problem.neighbours[region]),
                }
            )

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
            "csp": {
                "variables": variable_rows,
                "assignments": copy.deepcopy(assignments),
                "domains": copy.deepcopy(domains),
                "focus_variable": focus_variable,
                "failed_variable": failed_variable,
                "last_changes": copy.deepcopy(last_changes),
                "trace_entries": copy.deepcopy(trace_entries),
                "current_entry_index": len(trace_entries) - 1 if trace_entries else None,
            },
            "stats": copy.deepcopy(current_stats),
        }

    def record_trace_entry(event: dict[str, Any]) -> tuple[str, str, str]:
        action = event["action"]
        variable = event.get("variable")
        value = event.get("value")
        changes = event.get("changes", [])
        if action == "start":
            label = "Start search"
            annotation = "The map, domains, and constraints are ready. The solver will now branch and prune systematically."
            note = ALGORITHM_NOTE
            text = "Start backtracking search with forward checking."
        elif action == "select_variable":
            label = f"Select {variable}"
            annotation = f"Choose the next unassigned region. {variable} currently has domain {format_domain(event.get('domain', []))}."
            note = "Variable ordering changes which part of the CSP becomes informative first."
            text = f"Select {variable} with domain {format_domain(event.get('domain', []))}."
        elif action == "try_value":
            label = f"Try {variable} = {value}"
            annotation = f"Consider assigning {value} to {variable}."
            note = "Trying a locally legal colour does not guarantee that the whole map will still be solvable."
            text = f"Try {variable} = {value}."
        elif action == "assign":
            label = f"Assign {variable} = {value}"
            annotation = f"Assign {variable} = {value} and then propagate that choice to neighbouring domains."
            note = "Forward checking only looks one step ahead at affected neighbours."
            text = f"Assign {variable} = {value}."
        elif action == "prune":
            pruned_regions = [change["variable"] for change in changes]
            label = "Forward check"
            annotation = (
                f"Forward checking removes {value} from {format_region_list(pruned_regions)} "
                f"because those regions neighbour {variable}."
            )
            note = "Domain reduction is local propagation: it rules out impossible future values before the solver commits further."
            text = f"Forward checking removes {value} from {format_region_list(pruned_regions)}."
        elif action == "domain_wipeout":
            label = f"Domain wipe-out at {variable}"
            annotation = f"{variable} has no colours left after propagation, so this branch cannot lead to a solution."
            note = "A domain wipe-out is a concrete sign that the current partial assignment is inconsistent."
            text = f"{variable} has no colours left. This branch fails."
        elif action == "backtrack":
            label = f"Backtrack from {variable} = {value}"
            annotation = (
                f"Undo the current branch for {variable} = {value}"
                + (
                    f" because it wiped out {event['failed_variable']}."
                    if event.get("failed_variable")
                    else "."
                )
            )
            note = "Backtracking is a normal part of systematic search, not a bug in the algorithm."
            text = f"Backtrack from {variable} = {value}."
        elif action == "unassign":
            label = f"Undo {variable}"
            annotation = f"Restore the previous domains and return to the earlier choice point above {variable}."
            note = "When the solver backtracks, both the assignment and every propagated domain change must be undone."
            text = f"Undo {variable} = {value}."
        elif action == "solution_found":
            label = "Solution found"
            annotation = "Every region is assigned and all neighbouring regions have different colours."
            note = "A solution is a complete assignment that satisfies every constraint."
            text = "A complete colouring has been found."
        else:
            label = "Failure"
            annotation = "Every branch has failed. The current map-colouring CSP is unsatisfiable under these settings."
            note = "Unsatisfiable cases are useful because they show the whole search space being exhausted systematically."
            text = "Every branch fails. The CSP is unsatisfiable."

        trace_entries.append(
            {
                "step": event["step"],
                "action": action,
                "text": text,
            }
        )
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
        "goal_label": "Assign colours so every neighbouring pair differs",
        "csp_problem": problem.to_payload(),
        "options": {
            "algorithm": ALGORITHM_NAME,
        },
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
            variable = str(event["variable"])
            value = str(event["value"])
            push_state()
            assignments[variable] = value
            domains[variable] = [value]
            current_stats["assignments"] += 1
            new_tree_id = f"t{len(tree_order)}"
            tree_nodes[new_tree_id] = {
                "tree_id": new_tree_id,
                "graph_node": f"{variable} = {value}",
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
            focus_variable = variable
            search_status = "propagating"
        elif action == "prune":
            last_changes = copy.deepcopy(event.get("changes", []))
            for change in last_changes:
                region = change["variable"]
                removed = set(change.get("removed", []))
                domains[region] = [colour for colour in domains[region] if colour not in removed]
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
            assignments.update({str(region): str(value) for region, value in (assignment or event.get("assignments", {})).items()})
            for region in assignments:
                domains[region] = [assignments[region]]
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
        app_type="csp",
        trace_id=trace_id or ("csp-live" if live_trace else f"csp-{uuid4().hex[:8]}"),
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
        parent = node.get("parent")
        tree_id = node["tree_id"]
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
