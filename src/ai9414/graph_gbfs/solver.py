"""Greedy best-first search solver for weighted spatial graphs."""

from __future__ import annotations

import copy
import heapq
import math
from dataclasses import dataclass
from uuid import uuid4

from ai9414.graph_gbfs.models import GraphGbfsTreeNode
from ai9414.search.models import WeightedGraph, canonical_edge_id

ALGORITHM_LABEL = "Greedy best-first search"
ALGORITHM_NOTE = (
    "This example uses greedy best-first search on a weighted spatial graph. "
    "It expands the frontier node that looks closest to the goal according to a heuristic, "
    "so it can find a path quickly but it does not guarantee the cheapest path."
)


@dataclass
class RawGraphStep:
    event_type: str
    label: str
    annotation: str
    teaching_note: str
    snapshot: dict


@dataclass
class GraphGbfsSolveResult:
    trace_id: str
    initial_state: dict
    raw_steps: list[RawGraphStep]
    simple_trace: list[dict]
    status: str
    path: list[str]
    visited_order: list[str]
    path_cost: float | None


class _Recorder:
    def __init__(self, graph: WeightedGraph) -> None:
        self.graph = graph
        self.tree_nodes: dict[str, GraphGbfsTreeNode] = {}
        self.visible_tree_ids: list[str] = []
        self.active_tree_node: str | None = None
        self.active_tree_path: list[str] = []
        self.final_tree_path: list[str] = []
        self.current_graph_path: list[str] = [graph.start]
        self.final_graph_path: list[str] = []
        self.explored_edge_ids: list[str] = []
        self.considered_edge: list[str] | None = None
        self.current_cost = 0.0
        self.current_heuristic = 0.0
        self.visited_order: list[str] = [graph.start]
        self.status = "searching"
        self.simple_trace: list[dict] = []
        self.raw_steps: list[RawGraphStep] = []
        self.stats = {"expanded": 0, "enqueued": 1}
        self.counter = 0
        self.trace_id = f"graph-gbfs-{uuid4().hex[:8]}"

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
        self.tree_nodes[tree_id] = GraphGbfsTreeNode(
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
            "tree": {"nodes": [self.tree_nodes[tree_id].model_dump() for tree_id in self.visible_tree_ids]},
            "search": {
                "active_tree_node": self.active_tree_node,
                "active_tree_path": list(self.active_tree_path),
                "best_tree_path": [],
                "final_tree_path": list(self.final_tree_path),
                "current_graph_path": list(self.current_graph_path),
                "best_graph_path": [],
                "final_graph_path": list(self.final_graph_path),
                "visited_order": list(self.visited_order),
                "explored_graph_edges": [edge_id.split("--") for edge_id in self.explored_edge_ids],
                "considered_edge": list(self.considered_edge) if self.considered_edge else None,
                "current_cost": round(self.current_cost, 3),
                "current_heuristic": round(self.current_heuristic, 3),
                "best_cost": None,
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
                "heuristic": round(self.current_heuristic, 3),
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
        neighbours.sort(key=lambda item: item[0])
        adjacency[node_id] = neighbours
    return adjacency


def build_position_map(graph: WeightedGraph) -> dict[str, tuple[float, float]]:
    return {node.id: (node.x, node.y) for node in graph.nodes}


def heuristic_to_goal(position_map: dict[str, tuple[float, float]], goal: str, node_id: str) -> float:
    left = position_map[node_id]
    right = position_map[goal]
    return math.dist(left, right)


def _initial_state(graph: WeightedGraph, root: GraphGbfsTreeNode) -> dict:
    start_heuristic = heuristic_to_goal(build_position_map(graph), graph.goal, graph.start)
    return {
        "example_title": "",
        "example_subtitle": "",
        "algorithm_label": ALGORITHM_LABEL,
        "algorithm_note": ALGORITHM_NOTE,
        "goal_label": "Find any path from start to goal",
        "graph": graph.model_dump(),
        "tree": {"nodes": [root.model_dump()]},
        "search": {
            "active_tree_node": root.tree_id,
            "active_tree_path": [root.tree_id],
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


def solve_graph_gbfs(graph: WeightedGraph) -> GraphGbfsSolveResult:
    adjacency = build_adjacency(graph)
    position_map = build_position_map(graph)
    recorder = _Recorder(graph)
    root_id = recorder.create_tree_node(graph.start, None, 0, 0.0, "active")
    recorder.active_tree_node = root_id
    recorder.active_tree_path = [root_id]
    recorder.current_heuristic = heuristic_to_goal(position_map, graph.goal, graph.start)
    recorder.record_simple(action="start", node_id=graph.start, parent=None, depth=0)
    recorder.record_raw(
        event_type="start",
        label="Start greedy best-first",
        annotation="Greedy best-first search starts at the start node and prioritises whichever frontier node looks closest to the goal.",
        teaching_note=ALGORITHM_NOTE,
    )

    parents = {graph.start: None}
    route_costs = {graph.start: 0.0}
    routes = {graph.start: [graph.start]}
    tree_routes = {graph.start: [root_id]}
    tree_id_by_node = {graph.start: root_id}
    frontier: list[tuple[float, str, str]] = [
        (heuristic_to_goal(position_map, graph.goal, graph.start), graph.start, graph.start)
    ]
    visited = {graph.start}

    while frontier:
        heuristic_value, _, node_id = heapq.heappop(frontier)
        current_route = routes[node_id]
        current_tree_route = tree_routes[node_id]
        current_tree_id = current_tree_route[-1]
        current_cost = route_costs[node_id]

        recorder.current_graph_path = list(current_route)
        recorder.active_tree_path = list(current_tree_route)
        recorder.active_tree_node = current_tree_id
        recorder.current_cost = current_cost
        recorder.current_heuristic = heuristic_value
        recorder.considered_edge = None
        recorder.status = "searching"
        recorder.stats["expanded"] += 1
        recorder.record_simple(
            action="expand",
            node_id=node_id,
            parent=current_route[-2] if len(current_route) > 1 else None,
            depth=len(current_route) - 1,
        )
        recorder.record_raw(
            event_type="expand",
            label=f"Expand {node_id}",
            annotation=f"Greedy best-first search expands {node_id} because it currently looks closest to the goal by the heuristic.",
            teaching_note="Greedy best-first search follows the heuristic estimate, not the accumulated path cost.",
        )

        if node_id == graph.goal:
            recorder.final_graph_path = list(current_route)
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
                annotation="Greedy best-first search has reached the goal, so the first path it found is now highlighted.",
                teaching_note="This path is not guaranteed to be optimal because greedy best-first search ignores the full path cost when choosing what to expand next.",
            )
            return GraphGbfsSolveResult(
                trace_id=recorder.trace_id,
                initial_state=_initial_state(graph, recorder.tree_nodes[root_id]),
                raw_steps=recorder.raw_steps,
                simple_trace=recorder.simple_trace,
                status="found",
                path=list(current_route),
                visited_order=list(recorder.visited_order),
                path_cost=current_cost,
            )

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
                annotation=f"Check whether {neighbour} has already been discovered, and if not add it to the heuristic frontier.",
                teaching_note="Greedy best-first search usually keeps a visited set and does not revisit nodes it has already discovered.",
            )

            if neighbour in visited:
                continue

            visited.add(neighbour)
            parents[neighbour] = node_id
            route_costs[neighbour] = current_cost + edge_cost
            routes[neighbour] = current_route + [neighbour]
            child_id = recorder.create_tree_node(
                neighbour,
                current_tree_id,
                len(current_route),
                route_costs[neighbour],
                "queued",
                terminal=neighbour == graph.goal,
            )
            tree_routes[neighbour] = current_tree_route + [child_id]
            tree_id_by_node[neighbour] = child_id
            heuristic_score = heuristic_to_goal(position_map, graph.goal, neighbour)
            heapq.heappush(frontier, (heuristic_score, neighbour, neighbour))
            recorder.stats["enqueued"] += 1
            recorder.visited_order.append(neighbour)
            recorder.current_graph_path = list(routes[neighbour])
            recorder.active_tree_path = list(tree_routes[neighbour])
            recorder.active_tree_node = child_id
            recorder.current_cost = route_costs[neighbour]
            recorder.current_heuristic = heuristic_score
            recorder.status = "searching"
            recorder.record_simple(
                action="enqueue",
                node_id=neighbour,
                parent=node_id,
                depth=len(routes[neighbour]) - 1,
            )
            recorder.record_raw(
                event_type="enqueue",
                label=f"Queue {neighbour}",
                annotation=f"{neighbour} is added to the frontier with heuristic estimate {heuristic_score:.3f}.",
                teaching_note="The frontier order depends only on the heuristic estimate, not on the total path cost taken to reach the node.",
            )
            recorder.set_status(child_id, "queued")
            recorder.active_tree_path = list(current_tree_route)
            recorder.active_tree_node = current_tree_id
            recorder.current_graph_path = list(current_route)
            recorder.current_cost = current_cost
            recorder.current_heuristic = heuristic_value

    recorder.active_tree_node = None
    recorder.active_tree_path = []
    recorder.current_graph_path = []
    recorder.current_cost = 0.0
    recorder.current_heuristic = 0.0
    recorder.considered_edge = None
    recorder.status = "no path"
    recorder.record_simple(action="fail", node_id=None, parent=None, depth=0)
    recorder.record_raw(
        event_type="fail",
        label="No path found",
        annotation="Greedy best-first search exhausted the frontier without reaching the goal.",
        teaching_note="This is unusual for the generated graphs because they are constructed to be connected.",
    )
    return GraphGbfsSolveResult(
        trace_id=recorder.trace_id,
        initial_state=_initial_state(graph, recorder.tree_nodes[root_id]),
        raw_steps=recorder.raw_steps,
        simple_trace=recorder.simple_trace,
        status="fail",
        path=[],
        visited_order=list(recorder.visited_order),
        path_cost=None,
    )
