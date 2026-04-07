"""Plain DFS solver for spatial graph reachability."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from uuid import uuid4

from ai9414.graph_dfs.models import GraphDfsTreeNode, SpatialGraphDefinition

ALGORITHM_LABEL = "Depth-first search"
ALGORITHM_NOTE = (
    "This example uses plain depth-first search for reachability. "
    "It stops once it finds any path from the start node to the goal node, so it does not guarantee a shortest path."
)


@dataclass
class RawGraphStep:
    event_type: str
    label: str
    annotation: str
    teaching_note: str
    snapshot: dict


@dataclass
class GraphDfsSolveResult:
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


class _Recorder:
    def __init__(self, graph: SpatialGraphDefinition) -> None:
        self.graph = graph
        self.tree_nodes: dict[str, GraphDfsTreeNode] = {}
        self.visible_tree_ids: list[str] = []
        self.active_tree_node: str | None = None
        self.active_tree_path: list[str] = []
        self.current_graph_path: list[str] = [graph.start]
        self.visited_order: list[str] = [graph.start]
        self.visited_set = {graph.start}
        self.dead_end_nodes: list[str] = []
        self.dead_end_set: set[str] = set()
        self.final_graph_path: list[str] = []
        self.explored_edge_ids: list[str] = []
        self.status = "searching"
        self.depth = 0
        self.simple_trace: list[dict] = []
        self.raw_steps: list[RawGraphStep] = []
        self.counter = 0
        self.trace_id = f"graph-dfs-{uuid4().hex[:8]}"

    def create_tree_node(self, node_id: str, parent: str | None, depth: int, status: str) -> str:
        tree_id = f"t{self.counter}"
        self.counter += 1
        self.tree_nodes[tree_id] = GraphDfsTreeNode(
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
                "dead_end_nodes": list(self.dead_end_nodes),
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
                "stack": list(self.current_graph_path),
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


def solve_graph_dfs(graph: SpatialGraphDefinition) -> GraphDfsSolveResult:
    adjacency = build_adjacency(graph)
    recorder = _Recorder(graph)
    root_id = recorder.create_tree_node(graph.start, None, 0, "active")
    recorder.active_tree_node = root_id
    recorder.active_tree_path = [root_id]
    recorder.record_simple(action="start", node_id=graph.start, parent=None, depth=0)
    recorder.record_raw(
        event_type="start",
        label="Start DFS",
        annotation="DFS starts at the start node and follows one branch until it must backtrack or reaches the goal.",
        teaching_note=ALGORITHM_NOTE,
    )

    found = False

    def dfs(node_id: str, tree_id: str, depth: int) -> bool:
        nonlocal found

        if node_id == graph.goal:
            recorder.set_status(tree_id, "final")
            recorder.final_graph_path = copy.deepcopy(recorder.current_graph_path)
            recorder.depth = depth
            recorder.status = "goal found"
            recorder.record_simple(
                action="found",
                node_id=node_id,
                parent=recorder.current_graph_path[-2] if len(recorder.current_graph_path) > 1 else None,
                depth=depth,
            )
            recorder.record_raw(
                event_type="found",
                label="Goal found",
                annotation="DFS has reached the goal. The highlighted route is the first successful path it discovered.",
                teaching_note="Plain DFS stops here because the goal is reachability, not optimality.",
            )
            found = True
            return True

        recorder.set_status(tree_id, "active")
        for neighbour in adjacency[node_id]:
            if neighbour in recorder.visited_set:
                continue

            child_id = recorder.create_tree_node(neighbour, tree_id, depth + 1, "active")
            recorder.add_explored_edge(node_id, neighbour)
            recorder.set_status(tree_id, "expanded")
            recorder.active_tree_node = child_id
            recorder.active_tree_path.append(child_id)
            recorder.current_graph_path.append(neighbour)
            recorder.visited_order.append(neighbour)
            recorder.visited_set.add(neighbour)
            recorder.depth = depth + 1
            recorder.status = "searching"
            recorder.record_simple(
                action="expand",
                node_id=neighbour,
                parent=node_id,
                depth=depth + 1,
            )
            recorder.record_raw(
                event_type="expand",
                label=f"Expand {neighbour}",
                annotation=f"DFS steps from {node_id} to {neighbour} and continues deeper into the graph.",
                teaching_note="The graph view shows the spatial graph, while the tree view shows the search history.",
            )

            if dfs(neighbour, child_id, depth + 1):
                recorder.set_status(tree_id, "final")
                return True

            recorder.current_graph_path.pop()
            recorder.active_tree_path.pop()
            recorder.active_tree_node = tree_id
            recorder.depth = depth
            recorder.status = "backtracking"
            if neighbour not in recorder.dead_end_set:
                recorder.dead_end_set.add(neighbour)
                recorder.dead_end_nodes.append(neighbour)
            recorder.set_status(child_id, "backtracked")
            recorder.set_status(tree_id, "active")
            recorder.record_simple(
                action="backtrack",
                node_id=neighbour,
                parent=node_id,
                depth=depth + 1,
            )
            recorder.record_raw(
                event_type="backtrack",
                label=f"Backtrack from {neighbour}",
                annotation=f"The branch through {neighbour} does not reach the goal, so DFS retreats to {node_id}.",
                teaching_note="Backtracking keeps the tree history visible even after the active path retracts.",
            )

        if tree_id != root_id:
            recorder.set_status(tree_id, "backtracked")
        return False

    dfs(graph.start, root_id, 0)

    if not found:
        recorder.status = "no path"
        recorder.active_tree_node = None
        recorder.active_tree_path = []
        recorder.current_graph_path = []
        recorder.record_simple(action="fail", node_id=None, parent=None, depth=0)
        recorder.record_raw(
            event_type="fail",
            label="No path found",
            annotation="DFS exhausted every reachable branch and did not find the goal.",
            teaching_note="No route from start to goal was found in the current graph.",
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

    return GraphDfsSolveResult(
        trace_id=recorder.trace_id,
        initial_state=initial_state,
        raw_steps=recorder.raw_steps,
        simple_trace=recorder.simple_trace,
        status="found" if found else "fail",
        path=copy.deepcopy(recorder.final_graph_path),
        visited_order=copy.deepcopy(recorder.visited_order),
    )
