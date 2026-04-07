"""Depth-first branch-and-bound solver for weighted graphs."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from ai9414.search.models import SearchTreeNode, WeightedGraph, canonical_edge_id

ALGORITHM_LABEL = "Depth-first branch-and-bound"
ALGORITHM_NOTE = (
    "Plain depth-first search does not guarantee the shortest path in a weighted graph. "
    "This demo uses exhaustive DFS with backtracking and best-cost pruning, "
    "which remains optimal because it explores every branch that could still improve the best path found so far."
)


@dataclass
class RawTraceStep:
    event_type: str
    label: str
    annotation: str
    teaching_note: str
    snapshot: dict[str, Any]


@dataclass
class SolverResult:
    trace_id: str
    graph: WeightedGraph
    raw_steps: list[RawTraceStep]
    initial_data: dict[str, Any]


class _TraceRecorder:
    def __init__(self, graph: WeightedGraph) -> None:
        self.graph = graph
        self.goal = graph.goal
        self.tree_nodes: dict[str, SearchTreeNode] = {}
        self.visible_tree_ids: list[str] = []
        self.raw_steps: list[RawTraceStep] = []
        self.active_tree_node: str | None = None
        self.active_tree_path: list[str] = []
        self.current_graph_path: list[str] = [graph.start]
        self.current_cost = 0.0
        self.considered_edge: list[str] | None = None
        self.explored_edge_ids: list[str] = []
        self.best_graph_path: list[str] = []
        self.best_tree_path: list[str] = []
        self.best_cost: float | None = None
        self.final_graph_path: list[str] = []
        self.final_tree_path: list[str] = []
        self.finished = False
        self.status = "searching"
        self.stats = {"expanded": 0, "pruned": 0, "solutions_found": 0, "backtracks": 0}
        self.tree_counter = 0
        self.trace_id = f"search-{uuid4().hex[:8]}"

    def create_tree_node(
        self,
        *,
        graph_node: str,
        parent: str | None,
        depth: int,
        path_cost: float,
        status: str,
        terminal: bool = False,
    ) -> str:
        tree_id = f"t{self.tree_counter}"
        self.tree_counter += 1
        self.tree_nodes[tree_id] = SearchTreeNode(
            tree_id=tree_id,
            graph_node=graph_node,
            parent=parent,
            depth=depth,
            path_cost=round(path_cost, 3),
            status=status,
            order=len(self.visible_tree_ids),
            terminal=terminal,
        )
        self.visible_tree_ids.append(tree_id)
        return tree_id

    def set_status(self, tree_id: str, status: str) -> None:
        self.tree_nodes[tree_id].status = status

    def add_explored_edge(self, u: str, v: str) -> None:
        edge_id = canonical_edge_id(u, v)
        if edge_id not in self.explored_edge_ids:
            self.explored_edge_ids.append(edge_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "tree": {
                "nodes": [
                    self.tree_nodes[tree_id].model_dump()
                    for tree_id in self.visible_tree_ids
                ]
            },
            "search": {
                "active_tree_node": self.active_tree_node,
                "active_tree_path": list(self.active_tree_path),
                "best_tree_path": list(self.best_tree_path),
                "final_tree_path": list(self.final_tree_path),
                "current_graph_path": list(self.current_graph_path),
                "best_graph_path": list(self.best_graph_path),
                "final_graph_path": list(self.final_graph_path),
                "explored_graph_edges": [
                    edge_id.split("--")
                    for edge_id in self.explored_edge_ids
                ],
                "considered_edge": list(self.considered_edge) if self.considered_edge else None,
                "current_cost": round(self.current_cost, 3),
                "best_cost": None if self.best_cost is None else round(self.best_cost, 3),
                "finished": self.finished,
                "status": self.status,
            },
            "stats": copy.deepcopy(self.stats),
        }

    def record(
        self,
        *,
        event_type: str,
        label: str,
        annotation: str,
        teaching_note: str,
    ) -> None:
        self.raw_steps.append(
            RawTraceStep(
                event_type=event_type,
                label=label,
                annotation=annotation,
                teaching_note=teaching_note,
                snapshot=self.snapshot(),
            )
        )

    def initial_data(self) -> dict[str, Any]:
        return {
            "example_title": "",
            "example_subtitle": "",
            "algorithm_label": ALGORITHM_LABEL,
            "algorithm_note": ALGORITHM_NOTE,
            "graph": self.graph.model_dump(),
            **self.snapshot(),
        }


def build_adjacency(graph: WeightedGraph) -> dict[str, list[tuple[str, float]]]:
    adjacency: dict[str, list[tuple[str, float]]] = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.u].append((edge.v, edge.cost))
        adjacency[edge.v].append((edge.u, edge.cost))
    for node_id, neighbours in adjacency.items():
        neighbours.sort(key=lambda item: (item[1], item[0]))
        adjacency[node_id] = neighbours
    return adjacency


def solve_weighted_graph(graph: WeightedGraph) -> SolverResult:
    adjacency = build_adjacency(graph)
    recorder = _TraceRecorder(graph)
    root_id = recorder.create_tree_node(
        graph_node=graph.start,
        parent=None,
        depth=0,
        path_cost=0.0,
        status="active",
    )
    recorder.active_tree_node = root_id
    recorder.active_tree_path = [root_id]
    recorder.record(
        event_type="initialise",
        label=f"Initialise at {graph.start}",
        annotation=(
            f"Search starts at {graph.start} and aims for {graph.goal}. "
            "The graph on the right is fixed, while the search tree on the left grows as DFS explores branches."
        ),
        teaching_note=ALGORITHM_NOTE,
    )
    initial_data = copy.deepcopy(recorder.initial_data())

    def dfs(graph_node: str, tree_id: str, cost_so_far: float) -> None:
        recorder.active_tree_node = tree_id
        recorder.current_cost = cost_so_far
        recorder.set_status(tree_id, "active")
        recorder.status = "searching"

        if graph_node == graph.goal:
            recorder.stats["solutions_found"] += 1
            recorder.set_status(tree_id, "goal")
            recorder.status = "solution found"
            recorder.record(
                event_type="solution_found",
                label=f"Found a complete path to {graph.goal}",
                annotation=(
                    f"The branch {' -> '.join(recorder.current_graph_path)} reaches the goal "
                    f"with total cost {cost_so_far:.3f}."
                ),
                teaching_note="A complete path is a candidate solution, but it might not be the cheapest one yet.",
            )
            if recorder.best_cost is None or cost_so_far < recorder.best_cost:
                recorder.best_cost = cost_so_far
                recorder.best_graph_path = list(recorder.current_graph_path)
                recorder.best_tree_path = list(recorder.active_tree_path)
                recorder.record(
                    event_type="best_updated",
                    label="Update best solution",
                    annotation=(
                        f"This is the best complete path seen so far with cost {cost_so_far:.3f}. "
                        "Future branches can be pruned once they are already this expensive."
                    ),
                    teaching_note="Branch-and-bound becomes effective only after a complete solution establishes a best-cost bound.",
                )
            return

        recorder.stats["expanded"] += 1
        recorder.record(
            event_type="expand",
            label=f"Expand {graph_node}",
            annotation=(
                f"Expand {graph_node} in neighbour order. "
                f"The current partial path cost is {cost_so_far:.3f}."
            ),
            teaching_note="Deterministic neighbour ordering keeps the replay stable for a fixed graph.",
        )

        for neighbour, edge_cost in adjacency[graph_node]:
            recorder.considered_edge = [graph_node, neighbour]
            recorder.status = "considering"
            recorder.record(
                event_type="consider_edge",
                label=f"Consider {graph_node} -> {neighbour}",
                annotation=(
                    f"Check whether extending the current branch from {graph_node} to {neighbour} "
                    f"is still worth exploring."
                ),
                teaching_note="Each step records one search decision in the active branch.",
            )

            next_cost = cost_so_far + edge_cost
            if neighbour in recorder.current_graph_path:
                recorder.stats["pruned"] += 1
                recorder.status = "pruned"
                recorder.create_tree_node(
                    graph_node=neighbour,
                    parent=tree_id,
                    depth=len(recorder.current_graph_path),
                    path_cost=next_cost,
                    status="pruned",
                    terminal=neighbour == graph.goal,
                )
                recorder.record(
                    event_type="prune",
                    label=f"Prune cycle to {neighbour}",
                    annotation=(
                        f"The branch would revisit {neighbour}, which is already on the current DFS path, "
                        "so the cycle is rejected."
                    ),
                    teaching_note="Cycle handling blocks repeated nodes within the current path.",
                )
                continue

            if recorder.best_cost is not None and next_cost >= recorder.best_cost:
                recorder.stats["pruned"] += 1
                recorder.status = "pruned"
                recorder.create_tree_node(
                    graph_node=neighbour,
                    parent=tree_id,
                    depth=len(recorder.current_graph_path),
                    path_cost=next_cost,
                    status="pruned",
                    terminal=neighbour == graph.goal,
                )
                recorder.record(
                    event_type="prune",
                    label=f"Prune {neighbour}",
                    annotation=(
                        f"The partial cost would become {next_cost:.3f}, which cannot beat the current best cost "
                        f"of {recorder.best_cost:.3f}. The branch is pruned safely."
                    ),
                    teaching_note="Pruning is sound here because all edge costs are positive, so any continuation would only increase the total cost.",
                )
                continue

            recorder.set_status(tree_id, "expanded")
            child_id = recorder.create_tree_node(
                graph_node=neighbour,
                parent=tree_id,
                depth=len(recorder.current_graph_path),
                path_cost=next_cost,
                status="active",
                terminal=neighbour == graph.goal,
            )
            recorder.current_graph_path.append(neighbour)
            recorder.active_tree_path.append(child_id)
            recorder.active_tree_node = child_id
            recorder.current_cost = next_cost
            recorder.add_explored_edge(graph_node, neighbour)
            recorder.status = "searching"
            recorder.record(
                event_type="descend",
                label=f"Descend to {neighbour}",
                annotation=(
                    f"DFS commits to {neighbour}. The active branch is now "
                    f"{' -> '.join(recorder.current_graph_path)} with cost {next_cost:.3f}."
                ),
                teaching_note="Depth-first search follows one branch as far as it can before backtracking.",
            )

            dfs(neighbour, child_id, next_cost)

            recorder.current_graph_path.pop()
            recorder.active_tree_path.pop()
            if recorder.tree_nodes[child_id].status not in {"pruned", "goal"}:
                recorder.set_status(child_id, "backtracked")
            recorder.set_status(tree_id, "active")
            recorder.active_tree_node = tree_id
            recorder.current_cost = cost_so_far
            recorder.stats["backtracks"] += 1
            recorder.status = "backtracking"
            recorder.record(
                event_type="backtrack",
                label=f"Backtrack from {neighbour}",
                annotation=(
                    f"No better continuation remains below {neighbour}, so DFS backtracks to {graph_node}."
                ),
                teaching_note="Backtracking is what allows a depth-first strategy to remain exhaustive.",
            )

        recorder.considered_edge = None
        if tree_id != root_id:
            recorder.set_status(tree_id, "backtracked")
        else:
            recorder.set_status(tree_id, "expanded")

    dfs(graph.start, root_id, 0.0)

    if not recorder.best_graph_path:
        raise ValueError("The graph does not contain a path from start to goal.")

    recorder.final_graph_path = list(recorder.best_graph_path)
    recorder.final_tree_path = list(recorder.best_tree_path)
    recorder.active_tree_node = None
    recorder.active_tree_path = []
    recorder.current_graph_path = []
    recorder.current_cost = 0.0
    recorder.considered_edge = None
    recorder.finished = True
    recorder.status = "finished"
    recorder.record(
        event_type="finished",
        label="Search finished",
        annotation=(
            f"The optimal path is {' -> '.join(recorder.best_graph_path)} "
            f"with total cost {recorder.best_cost:.3f}."
        ),
        teaching_note=ALGORITHM_NOTE,
    )

    return SolverResult(
        trace_id=recorder.trace_id,
        graph=graph,
        raw_steps=recorder.raw_steps,
        initial_data=initial_data,
    )
