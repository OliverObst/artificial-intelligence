"""Plain BFS solver for spatial graph reachability."""

from __future__ import annotations

import copy
from collections import deque
from dataclasses import dataclass
from uuid import uuid4

from ai9414.graph_bfs.models import GraphBfsTreeNode
from ai9414.graph_dfs.models import SpatialGraphDefinition

ALGORITHM_LABEL = "Breadth-first search"
ALGORITHM_NOTE = (
    "This example uses plain breadth-first search for reachability. "
    "It expands the graph level by level, so in this unweighted graph it finds a shallowest path in number of edges."
)


@dataclass
class RawGraphStep:
    event_type: str
    label: str
    annotation: str
    teaching_note: str
    snapshot: dict


@dataclass
class GraphBfsSolveResult:
    trace_id: str
    initial_state: dict
    raw_steps: list[RawGraphStep]
    simple_trace: list[dict]
    status: str
    path: list[str]
    visited_order: list[str]


def _edge_id(u: str, v: str) -> str:
    left, right = sorted((u, v))
    return f"{left}--{right}"


def _reconstruct_path(parents: dict[str, str | None], goal: str) -> list[str]:
    path: list[str] = []
    current: str | None = goal
    while current is not None:
        path.append(current)
        current = parents[current]
    path.reverse()
    return path


class _Recorder:
    def __init__(self, graph: SpatialGraphDefinition) -> None:
        self.graph = graph
        self.tree_nodes: dict[str, GraphBfsTreeNode] = {}
        self.visible_tree_ids: list[str] = []
        self.active_tree_node: str | None = None
        self.active_tree_path: list[str] = []
        self.current_graph_path: list[str] = [graph.start]
        self.visited_order: list[str] = [graph.start]
        self.final_graph_path: list[str] = []
        self.explored_edge_ids: list[str] = []
        self.status = "searching"
        self.depth = 0
        self.simple_trace: list[dict] = []
        self.raw_steps: list[RawGraphStep] = []
        self.counter = 0
        self.trace_id = f"graph-bfs-{uuid4().hex[:8]}"

    def create_tree_node(self, node_id: str, parent: str | None, depth: int, status: str) -> str:
        tree_id = f"t{self.counter}"
        self.counter += 1
        self.tree_nodes[tree_id] = GraphBfsTreeNode(
            tree_id=tree_id,
            graph_node=node_id,
            parent=parent,
            depth=depth,
            path_cost=depth,
            status=status,
            order=len(self.visible_tree_ids),
        )
        self.visible_tree_ids.append(tree_id)
        return tree_id

    def set_status(self, tree_id: str, status: str) -> None:
        self.tree_nodes[tree_id].status = status

    def add_explored_edge(self, left: str, right: str) -> None:
        edge_id = _edge_id(left, right)
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
                "current_graph_path": list(self.current_graph_path),
                "visited_order": list(self.visited_order),
                "dead_end_nodes": [],
                "final_graph_path": list(self.final_graph_path),
                "explored_graph_edges": [
                    edge_id.split("--")
                    for edge_id in self.explored_edge_ids
                ],
                "explored_count": len(self.visited_order),
                "current_depth": self.depth,
                "status": self.status,
                "found": bool(self.final_graph_path),
            },
        }

    def record_simple(
        self,
        *,
        action: str,
        node_id: str | None,
        parent: str | None,
        depth: int,
    ) -> None:
        self.simple_trace.append(
            {
                "step": len(self.simple_trace),
                "action": action,
                "node": node_id,
                "parent": parent,
                "depth": depth,
                "route": list(self.current_graph_path),
            }
        )

    def record_raw(
        self,
        *,
        event_type: str,
        label: str,
        annotation: str,
        teaching_note: str,
    ) -> None:
        self.raw_steps.append(
            RawGraphStep(
                event_type=event_type,
                label=label,
                annotation=annotation,
                teaching_note=teaching_note,
                snapshot=self.snapshot(),
            )
        )


def build_adjacency(graph: SpatialGraphDefinition) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.u].append(edge.v)
        adjacency[edge.v].append(edge.u)
    for node_id, neighbours in adjacency.items():
        neighbours.sort()
        adjacency[node_id] = neighbours
    return adjacency


def solve_graph_bfs(graph: SpatialGraphDefinition) -> GraphBfsSolveResult:
    adjacency = build_adjacency(graph)
    recorder = _Recorder(graph)
    root_id = recorder.create_tree_node(graph.start, None, 0, "active")
    recorder.active_tree_node = root_id
    recorder.active_tree_path = [root_id]
    recorder.record_simple(action="start", node_id=graph.start, parent=None, depth=0)
    recorder.record_raw(
        event_type="start",
        label="Start BFS",
        annotation="BFS starts at the start node and expands the graph level by level.",
        teaching_note=ALGORITHM_NOTE,
    )

    parents: dict[str, str | None] = {graph.start: None}
    depths: dict[str, int] = {graph.start: 0}
    tree_ids: dict[str, str] = {graph.start: root_id}
    visited = {graph.start}
    frontier = deque([graph.start])

    if graph.start == graph.goal:
        recorder.set_status(root_id, "final")
        recorder.final_graph_path = [graph.start]
        recorder.status = "goal found"
        recorder.record_simple(action="found", node_id=graph.start, parent=None, depth=0)
        recorder.record_raw(
            event_type="found",
            label="Goal found",
            annotation="The start node is already the goal, so BFS succeeds immediately.",
            teaching_note="In an unweighted graph, BFS reaches goals in increasing depth order.",
        )
        found = True
    else:
        found = False

    while frontier and not found:
        node_id = frontier.popleft()
        route = _reconstruct_path(parents, node_id)
        recorder.current_graph_path = copy.deepcopy(route)
        recorder.active_tree_node = tree_ids[node_id]
        recorder.active_tree_path = [tree_ids[path_node] for path_node in route]
        recorder.depth = depths[node_id]
        recorder.status = "searching"
        recorder.set_status(tree_ids[node_id], "active")

        for neighbour in adjacency[node_id]:
            if neighbour in visited:
                continue

            visited.add(neighbour)
            parents[neighbour] = node_id
            depths[neighbour] = depths[node_id] + 1
            recorder.visited_order.append(neighbour)
            child_id = recorder.create_tree_node(neighbour, tree_ids[node_id], depths[neighbour], "active")
            tree_ids[neighbour] = child_id
            recorder.add_explored_edge(node_id, neighbour)
            frontier.append(neighbour)

            route_to_child = _reconstruct_path(parents, neighbour)
            recorder.current_graph_path = copy.deepcopy(route_to_child)
            recorder.active_tree_node = child_id
            recorder.active_tree_path = [tree_ids[path_node] for path_node in route_to_child]
            recorder.depth = depths[neighbour]
            recorder.status = "searching"
            recorder.set_status(tree_ids[node_id], "expanded")
            recorder.record_simple(
                action="expand",
                node_id=neighbour,
                parent=node_id,
                depth=depths[neighbour],
            )
            recorder.record_raw(
                event_type="expand",
                label=f"Expand {neighbour}",
                annotation=f"BFS discovers {neighbour} from {node_id} and adds it to the next frontier layer.",
                teaching_note="The tree shows discovery order, while the graph view shows the route from the start to the highlighted node.",
            )
            recorder.set_status(child_id, "expanded")

            if neighbour == graph.goal:
                recorder.final_graph_path = copy.deepcopy(route_to_child)
                recorder.status = "goal found"
                for path_node in route_to_child:
                    recorder.set_status(tree_ids[path_node], "final")
                recorder.active_tree_node = child_id
                recorder.active_tree_path = [tree_ids[path_node] for path_node in route_to_child]
                recorder.current_graph_path = copy.deepcopy(route_to_child)
                recorder.depth = depths[neighbour]
                recorder.record_simple(
                    action="found",
                    node_id=neighbour,
                    parent=node_id,
                    depth=depths[neighbour],
                )
                recorder.record_raw(
                    event_type="found",
                    label="Goal found",
                    annotation="BFS has reached the goal. The highlighted route is the first goal path discovered at this depth.",
                    teaching_note="Because this graph is unweighted, BFS finds a shallowest path in number of edges.",
                )
                found = True
                break

        if not found:
            recorder.set_status(tree_ids[node_id], "expanded")

    if not found:
        recorder.status = "no path"
        recorder.active_tree_node = None
        recorder.active_tree_path = []
        recorder.current_graph_path = []
        recorder.record_simple(action="fail", node_id=None, parent=None, depth=0)
        recorder.record_raw(
            event_type="fail",
            label="No path found",
            annotation="BFS exhausted the reachable graph and did not find the goal.",
            teaching_note="This is unusual for the generated graphs because they are constructed to be connected.",
        )

    initial_state = {
        "example_title": "",
        "example_subtitle": "",
        "algorithm_label": ALGORITHM_LABEL,
        "algorithm_note": ALGORITHM_NOTE,
        "goal_label": "Find any path from start to goal",
        "graph": graph.model_dump(),
        "tree": {"nodes": [recorder.tree_nodes[root_id].model_dump()]},
        "search": {
            "active_tree_node": root_id,
            "active_tree_path": [root_id],
            "current_graph_path": [graph.start],
            "visited_order": [graph.start],
            "dead_end_nodes": [],
            "final_graph_path": [],
            "explored_graph_edges": [],
            "explored_count": 1,
            "current_depth": 0,
            "status": "searching",
            "found": False,
        },
    }

    return GraphBfsSolveResult(
        trace_id=recorder.trace_id,
        initial_state=initial_state,
        raw_steps=recorder.raw_steps,
        simple_trace=recorder.simple_trace,
        status="found" if found else "fail",
        path=copy.deepcopy(recorder.final_graph_path),
        visited_order=copy.deepcopy(recorder.visited_order),
    )
