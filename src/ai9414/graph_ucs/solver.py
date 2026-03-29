"""Uniform-cost search solver for weighted spatial graphs."""

from __future__ import annotations

import copy
import heapq
from dataclasses import dataclass
from uuid import uuid4

from ai9414.graph_ucs.models import GraphUcsTreeNode
from ai9414.search.models import WeightedGraph, canonical_edge_id

ALGORITHM_LABEL = "Uniform-cost search"
ALGORITHM_NOTE = (
    "This example uses uniform-cost search on a weighted graph with positive edge costs. "
    "It always expands the frontier path with the lowest total cost so far, "
    "which guarantees an optimal path to the goal."
)


@dataclass
class RawGraphStep:
    event_type: str
    label: str
    annotation: str
    teaching_note: str
    snapshot: dict


@dataclass
class GraphUcsSolveResult:
    trace_id: str
    initial_state: dict
    raw_steps: list[RawGraphStep]
    simple_trace: list[dict]
    status: str
    path: list[str]
    visited_order: list[str]
    best_cost: float | None


class _Recorder:
    def __init__(self, graph: WeightedGraph) -> None:
        self.graph = graph
        self.tree_nodes: dict[str, GraphUcsTreeNode] = {}
        self.visible_tree_ids: list[str] = []
        self.active_tree_node: str | None = None
        self.active_tree_path: list[str] = []
        self.best_tree_path: list[str] = []
        self.final_tree_path: list[str] = []
        self.current_graph_path: list[str] = [graph.start]
        self.best_graph_path: list[str] = []
        self.final_graph_path: list[str] = []
        self.explored_edge_ids: list[str] = []
        self.considered_edge: list[str] | None = None
        self.current_cost = 0.0
        self.best_cost: float | None = None
        self.visited_order: list[str] = [graph.start]
        self.status = "searching"
        self.simple_trace: list[dict] = []
        self.raw_steps: list[RawGraphStep] = []
        self.stats = {"expanded": 0, "relaxed": 0}
        self.counter = 0
        self.trace_id = f"graph-ucs-{uuid4().hex[:8]}"

    def create_tree_node(
        self,
        node_id: str,
        parent: str | None,
        depth: int,
        path_cost: float,
        status: str,
        *,
        terminal: bool = False,
    ) -> str:
        tree_id = f"t{self.counter}"
        self.counter += 1
        self.tree_nodes[tree_id] = GraphUcsTreeNode(
            tree_id=tree_id,
            graph_node=node_id,
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

    def snapshot(self) -> dict:
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
                "visited_order": list(self.visited_order),
                "explored_graph_edges": [edge_id.split("--") for edge_id in self.explored_edge_ids],
                "considered_edge": list(self.considered_edge) if self.considered_edge else None,
                "current_cost": round(self.current_cost, 3),
                "best_cost": None if self.best_cost is None else round(self.best_cost, 3),
                "explored_count": len(self.visited_order),
                "current_depth": max(len(self.current_graph_path) - 1, 0),
                "status": self.status,
                "found": bool(self.final_graph_path),
            },
            "stats": copy.deepcopy(self.stats),
        }

    def record_simple(self, *, action: str, node_id: str | None, parent: str | None, depth: int) -> None:
        self.simple_trace.append(
            {
                "step": len(self.simple_trace),
                "action": action,
                "node": node_id,
                "parent": parent,
                "depth": depth,
                "current_path": list(self.current_graph_path),
                "current_cost": round(self.current_cost, 3),
                "best_path": list(self.best_graph_path),
                "best_cost": None if self.best_cost is None else round(self.best_cost, 3),
                "considered_edge": list(self.considered_edge) if self.considered_edge else None,
                "path_cost": round(self.current_cost, 3),
            }
        )

    def record_raw(self, *, event_type: str, label: str, annotation: str, teaching_note: str) -> None:
        self.raw_steps.append(
            RawGraphStep(
                event_type=event_type,
                label=label,
                annotation=annotation,
                teaching_note=teaching_note,
                snapshot=self.snapshot(),
            )
        )


def build_adjacency(graph: WeightedGraph) -> dict[str, list[tuple[str, float]]]:
    adjacency: dict[str, list[tuple[str, float]]] = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.u].append((edge.v, edge.cost))
        adjacency[edge.v].append((edge.u, edge.cost))
    for node_id, neighbours in adjacency.items():
        neighbours.sort(key=lambda item: (item[1], item[0]))
        adjacency[node_id] = neighbours
    return adjacency


def solve_graph_ucs(graph: WeightedGraph) -> GraphUcsSolveResult:
    adjacency = build_adjacency(graph)
    recorder = _Recorder(graph)
    root_id = recorder.create_tree_node(graph.start, None, 0, 0.0, "active")
    recorder.active_tree_node = root_id
    recorder.active_tree_path = [root_id]
    recorder.record_simple(action="start", node_id=graph.start, parent=None, depth=0)
    recorder.record_raw(
        event_type="start",
        label="Start UCS",
        annotation="Uniform-cost search starts at the start node and always expands the cheapest frontier path next.",
        teaching_note=ALGORITHM_NOTE,
    )

    best_costs = {graph.start: 0.0}
    best_routes = {graph.start: [graph.start]}
    best_tree_routes = {graph.start: [root_id]}
    frontier: list[tuple[float, int, str]] = [(0.0, 0, graph.start)]
    frontier_counter = 1
    expanded: set[str] = set()
    discovered = {graph.start}

    while frontier:
        current_cost, _, node_id = heapq.heappop(frontier)
        if current_cost != best_costs.get(node_id):
            continue

        current_route = best_routes[node_id]
        current_tree_route = best_tree_routes[node_id]
        current_tree_id = current_tree_route[-1]
        recorder.current_graph_path = list(current_route)
        recorder.active_tree_path = list(current_tree_route)
        recorder.active_tree_node = current_tree_id
        recorder.current_cost = current_cost
        recorder.considered_edge = None
        recorder.status = "searching"
        recorder.record_simple(
            action="expand",
            node_id=node_id,
            parent=current_route[-2] if len(current_route) > 1 else None,
            depth=len(current_route) - 1,
        )
        recorder.record_raw(
            event_type="expand",
            label=f"Expand {node_id}",
            annotation=f"UCS expands {node_id} because its path cost {current_cost:.3f} is the lowest on the frontier.",
            teaching_note="Uniform-cost search always expands the cheapest available path first.",
        )

        if node_id == graph.goal:
            recorder.best_cost = current_cost
            recorder.best_graph_path = list(current_route)
            recorder.final_graph_path = list(current_route)
            recorder.best_tree_path = list(current_tree_route)
            recorder.final_tree_path = list(current_tree_route)
            for tree_id in current_tree_route:
                recorder.set_status(tree_id, "final")
            recorder.status = "goal found"
            recorder.record_simple(
                action="found",
                node_id=node_id,
                parent=current_route[-2] if len(current_route) > 1 else None,
                depth=len(current_route) - 1,
            )
            recorder.record_raw(
                event_type="found",
                label="Goal found",
                annotation="The goal has been removed from the frontier, so this path is optimal.",
                teaching_note="With positive edge costs, the first time UCS expands the goal, the path cost is optimal.",
            )
            return GraphUcsSolveResult(
                trace_id=recorder.trace_id,
                initial_state={
                    "example_title": "",
                    "example_subtitle": "",
                    "algorithm_label": ALGORITHM_LABEL,
                    "algorithm_note": ALGORITHM_NOTE,
                    "goal_label": "Find the optimal path from start to goal",
                    "graph": graph.model_dump(),
                    "tree": {"nodes": [recorder.tree_nodes[root_id].model_dump()]},
                    "search": {
                        "active_tree_node": root_id,
                        "active_tree_path": [root_id],
                        "best_tree_path": [],
                        "final_tree_path": [],
                        "current_graph_path": [graph.start],
                        "best_graph_path": [],
                        "final_graph_path": [],
                        "visited_order": [graph.start],
                        "explored_graph_edges": [],
                        "considered_edge": None,
                        "current_cost": 0.0,
                        "best_cost": None,
                        "explored_count": 1,
                        "current_depth": 0,
                        "status": "searching",
                        "found": False,
                    },
                    "stats": {"expanded": 0, "relaxed": 0},
                },
                raw_steps=recorder.raw_steps,
                simple_trace=recorder.simple_trace,
                status="found",
                path=list(current_route),
                visited_order=list(recorder.visited_order),
                best_cost=current_cost,
            )

        expanded.add(node_id)
        recorder.stats["expanded"] += 1
        recorder.set_status(current_tree_id, "expanded")

        for neighbour, edge_cost in adjacency[node_id]:
            recorder.considered_edge = [node_id, neighbour]
            recorder.add_explored_edge(node_id, neighbour)
            recorder.status = "considering"
            recorder.record_simple(
                action="consider_edge",
                node_id=node_id,
                parent=current_route[-2] if len(current_route) > 1 else None,
                depth=len(current_route) - 1,
            )
            recorder.record_raw(
                event_type="consider_edge",
                label=f"Consider {node_id} -> {neighbour}",
                annotation=f"Check whether going from {node_id} to {neighbour} improves the known best path to {neighbour}.",
                teaching_note="UCS relaxes edges by comparing new path costs with the best cost known so far.",
            )

            if neighbour in expanded:
                continue

            new_cost = current_cost + edge_cost
            known_cost = best_costs.get(neighbour)
            if known_cost is not None and new_cost >= known_cost:
                continue

            child_id = recorder.create_tree_node(
                neighbour,
                current_tree_id,
                len(current_route),
                new_cost,
                "active",
                terminal=neighbour == graph.goal,
            )
            next_route = current_route + [neighbour]
            next_tree_route = current_tree_route + [child_id]
            best_costs[neighbour] = new_cost
            best_routes[neighbour] = next_route
            best_tree_routes[neighbour] = next_tree_route
            heapq.heappush(frontier, (new_cost, frontier_counter, neighbour))
            frontier_counter += 1
            if neighbour not in discovered:
                discovered.add(neighbour)
                recorder.visited_order.append(neighbour)
            recorder.current_graph_path = list(next_route)
            recorder.active_tree_path = list(next_tree_route)
            recorder.active_tree_node = child_id
            recorder.current_cost = new_cost
            recorder.stats["relaxed"] += 1
            recorder.status = "searching"
            recorder.record_simple(
                action="relax",
                node_id=neighbour,
                parent=node_id,
                depth=len(next_route) - 1,
            )
            recorder.record_raw(
                event_type="relax",
                label=f"Relax {neighbour}",
                annotation=f"The path to {neighbour} improves to cost {new_cost:.3f}, so UCS updates the frontier entry.",
                teaching_note="A node can appear more than once in the search tree if UCS later finds a cheaper route to it.",
            )
            recorder.set_status(child_id, "expanded")

    recorder.active_tree_node = None
    recorder.active_tree_path = []
    recorder.current_graph_path = []
    recorder.current_cost = 0.0
    recorder.considered_edge = None
    recorder.status = "no path"
    recorder.record_simple(action="fail", node_id=None, parent=None, depth=0)
    recorder.record_raw(
        event_type="fail",
        label="No path found",
        annotation="UCS exhausted the frontier without reaching the goal.",
        teaching_note="This is unusual for the generated graphs because they are constructed to be connected.",
    )
    return GraphUcsSolveResult(
        trace_id=recorder.trace_id,
        initial_state={
            "example_title": "",
            "example_subtitle": "",
            "algorithm_label": ALGORITHM_LABEL,
            "algorithm_note": ALGORITHM_NOTE,
            "goal_label": "Find the optimal path from start to goal",
            "graph": graph.model_dump(),
            "tree": {"nodes": [recorder.tree_nodes[root_id].model_dump()]},
            "search": {
                "active_tree_node": root_id,
                "active_tree_path": [root_id],
                "best_tree_path": [],
                "final_tree_path": [],
                "current_graph_path": [graph.start],
                "best_graph_path": [],
                "final_graph_path": [],
                "visited_order": [graph.start],
                "explored_graph_edges": [],
                "considered_edge": None,
                "current_cost": 0.0,
                "best_cost": None,
                "explored_count": 1,
                "current_depth": 0,
                "status": "searching",
                "found": False,
            },
            "stats": {"expanded": 0, "relaxed": 0},
        },
        raw_steps=recorder.raw_steps,
        simple_trace=recorder.simple_trace,
        status="fail",
        path=[],
        visited_order=list(recorder.visited_order),
        best_cost=None,
    )
