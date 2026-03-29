"""A* search solver for weighted spatial graphs."""

from __future__ import annotations

import copy
import heapq
import math
from dataclasses import dataclass
from uuid import uuid4

from ai9414.graph_astar.models import GraphAStarTreeNode
from ai9414.search.models import WeightedGraph, canonical_edge_id

ALGORITHM_LABEL = "A* search"
ALGORITHM_NOTE = (
    "This example uses A* search on a weighted spatial graph. "
    "It orders the frontier by path cost so far plus a straight-line heuristic to the goal, "
    "which still guarantees an optimal path here because the heuristic is admissible."
)


@dataclass
class RawGraphStep:
    event_type: str
    label: str
    annotation: str
    teaching_note: str
    snapshot: dict


@dataclass
class GraphAStarSolveResult:
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
        self.tree_nodes: dict[str, GraphAStarTreeNode] = {}
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
        self.current_heuristic = 0.0
        self.current_priority = 0.0
        self.best_cost: float | None = None
        self.visited_order: list[str] = [graph.start]
        self.status = "searching"
        self.simple_trace: list[dict] = []
        self.raw_steps: list[RawGraphStep] = []
        self.stats = {"expanded": 0, "relaxed": 1}
        self.counter = 0
        self.trace_id = f"graph-astar-{uuid4().hex[:8]}"

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
        self.tree_nodes[tree_id] = GraphAStarTreeNode(
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
                "best_tree_path": list(self.best_tree_path),
                "final_tree_path": list(self.final_tree_path),
                "current_graph_path": list(self.current_graph_path),
                "best_graph_path": list(self.best_graph_path),
                "final_graph_path": list(self.final_graph_path),
                "visited_order": list(self.visited_order),
                "explored_graph_edges": [edge_id.split("--") for edge_id in self.explored_edge_ids],
                "considered_edge": list(self.considered_edge) if self.considered_edge else None,
                "current_cost": round(self.current_cost, 3),
                "current_heuristic": round(self.current_heuristic, 3),
                "current_priority": round(self.current_priority, 3),
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
                "heuristic": round(self.current_heuristic, 3),
                "priority": round(self.current_priority, 3),
                "considered_edge": list(self.considered_edge) if self.considered_edge else None,
                "path_cost": round(self.current_cost, 3),
                "best_cost": None if self.best_cost is None else round(self.best_cost, 3),
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


def build_position_map(graph: WeightedGraph) -> dict[str, tuple[float, float]]:
    return {node.id: (node.x, node.y) for node in graph.nodes}


def heuristic_to_goal(position_map: dict[str, tuple[float, float]], goal: str, node_id: str) -> float:
    return math.dist(position_map[node_id], position_map[goal])


def _initial_state(graph: WeightedGraph, root: GraphAStarTreeNode) -> dict:
    start_heuristic = heuristic_to_goal(build_position_map(graph), graph.goal, graph.start)
    return {
        "example_title": "",
        "example_subtitle": "",
        "algorithm_label": ALGORITHM_LABEL,
        "algorithm_note": ALGORITHM_NOTE,
        "goal_label": "Find the optimal path from start to goal",
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
            "current_priority": round(start_heuristic, 3),
            "best_cost": None,
            "explored_count": 1,
            "current_depth": 0,
            "status": "searching",
            "found": False,
        },
        "stats": {"expanded": 0, "relaxed": 1},
    }


def solve_graph_astar(graph: WeightedGraph) -> GraphAStarSolveResult:
    adjacency = build_adjacency(graph)
    position_map = build_position_map(graph)
    recorder = _Recorder(graph)
    root_id = recorder.create_tree_node(graph.start, None, 0, 0.0, "active")
    root_h = heuristic_to_goal(position_map, graph.goal, graph.start)
    recorder.active_tree_node = root_id
    recorder.active_tree_path = [root_id]
    recorder.current_heuristic = root_h
    recorder.current_priority = root_h
    recorder.record_simple(action="start", node_id=graph.start, parent=None, depth=0)
    recorder.record_raw(
        event_type="start",
        label="Start A*",
        annotation="A* starts at the start node and orders the frontier by path cost plus straight-line distance to the goal.",
        teaching_note=ALGORITHM_NOTE,
    )

    best_costs = {graph.start: 0.0}
    best_routes = {graph.start: [graph.start]}
    best_tree_routes = {graph.start: [root_id]}
    frontier: list[tuple[float, float, str]] = [(root_h, 0.0, graph.start)]
    expanded: set[str] = set()

    while frontier:
        priority, current_cost, node_id = heapq.heappop(frontier)
        if current_cost != best_costs.get(node_id):
            continue

        current_route = best_routes[node_id]
        current_tree_route = best_tree_routes[node_id]
        current_tree_id = current_tree_route[-1]
        heuristic_value = heuristic_to_goal(position_map, graph.goal, node_id)

        recorder.current_graph_path = list(current_route)
        recorder.active_tree_path = list(current_tree_route)
        recorder.active_tree_node = current_tree_id
        recorder.current_cost = current_cost
        recorder.current_heuristic = heuristic_value
        recorder.current_priority = priority
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
            annotation=f"A* expands {node_id} because its f-score {priority:.3f} is the lowest on the frontier.",
            teaching_note="A* combines path cost so far with a heuristic estimate to decide what to expand next.",
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
                annotation="The goal has been removed from the frontier, so the highlighted path is optimal.",
                teaching_note="Because the straight-line heuristic is admissible here, A* still guarantees an optimal path.",
            )
            return GraphAStarSolveResult(
                trace_id=recorder.trace_id,
                initial_state=_initial_state(graph, recorder.tree_nodes[root_id]),
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
                annotation=f"Check whether going from {node_id} to {neighbour} improves the best known g-cost to {neighbour}.",
                teaching_note="A* relaxes edges using the path cost so far, then adds the heuristic to rank the frontier.",
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
                "queued",
                terminal=neighbour == graph.goal,
            )
            next_route = current_route + [neighbour]
            next_tree_route = current_tree_route + [child_id]
            best_costs[neighbour] = new_cost
            best_routes[neighbour] = next_route
            best_tree_routes[neighbour] = next_tree_route
            neighbour_h = heuristic_to_goal(position_map, graph.goal, neighbour)
            neighbour_priority = new_cost + neighbour_h
            heapq.heappush(frontier, (neighbour_priority, new_cost, neighbour))
            if neighbour not in recorder.visited_order:
                recorder.visited_order.append(neighbour)
            recorder.current_graph_path = list(next_route)
            recorder.active_tree_path = list(next_tree_route)
            recorder.active_tree_node = child_id
            recorder.current_cost = new_cost
            recorder.current_heuristic = neighbour_h
            recorder.current_priority = neighbour_priority
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
                annotation=f"The path to {neighbour} improves to g = {new_cost:.3f}, so A* updates its frontier priority to f = {neighbour_priority:.3f}.",
                teaching_note="A node can appear more than once in the tree if A* later finds a cheaper route to it.",
            )
            recorder.set_status(child_id, "queued")

    recorder.active_tree_node = None
    recorder.active_tree_path = []
    recorder.current_graph_path = []
    recorder.current_cost = 0.0
    recorder.current_heuristic = 0.0
    recorder.current_priority = 0.0
    recorder.considered_edge = None
    recorder.status = "no path"
    recorder.record_simple(action="fail", node_id=None, parent=None, depth=0)
    recorder.record_raw(
        event_type="fail",
        label="No path found",
        annotation="A* exhausted the frontier without reaching the goal.",
        teaching_note="This is unusual for the generated graphs because they are constructed to be connected.",
    )
    return GraphAStarSolveResult(
        trace_id=recorder.trace_id,
        initial_state=_initial_state(graph, recorder.tree_nodes[root_id]),
        raw_steps=recorder.raw_steps,
        simple_trace=recorder.simple_trace,
        status="fail",
        path=[],
        visited_order=list(recorder.visited_order),
        best_cost=None,
    )
