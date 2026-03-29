"""Procedural graph generation helpers for the search demo."""

from __future__ import annotations

import math
import random
from typing import Iterable

from ai9414.search.models import GraphEdge, GraphNode, WeightedGraph


def euclidean_distance(a: GraphNode, b: GraphNode) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def generate_node_ids(count: int) -> list[str]:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if count > len(alphabet):
        raise ValueError("The demo generator currently supports up to 26 nodes.")
    return list(alphabet[:count])


def _generate_positions(node_count: int, seed: int) -> list[GraphNode]:
    rng = random.Random(seed)
    columns = max(4, math.ceil(math.sqrt(node_count)))
    rows = math.ceil(node_count / columns)
    cells: list[tuple[int, int]] = [(row, col) for row in range(rows) for col in range(columns)]
    rng.shuffle(cells)
    ids = generate_node_ids(node_count)
    nodes: list[GraphNode] = []

    x_span = 0.82
    y_span = 0.72

    for node_id, (row, col) in zip(ids, cells, strict=True):
        base_x = 0.09 + (col + 0.5) * (x_span / columns)
        base_y = 0.14 + (row + 0.5) * (y_span / rows)
        jitter_x = (rng.random() - 0.5) * (x_span / columns) * 0.55
        jitter_y = (rng.random() - 0.5) * (y_span / rows) * 0.55
        nodes.append(
            GraphNode(
                id=node_id,
                x=min(0.95, max(0.05, base_x + jitter_x)),
                y=min(0.9, max(0.08, base_y + jitter_y)),
            )
        )
    return nodes


def _choose_start_goal(nodes: list[GraphNode]) -> tuple[str, str]:
    best_pair: tuple[str, str] | None = None
    best_distance = -1.0
    for left in nodes:
        for right in nodes:
            if left.id == right.id:
                continue
            distance = euclidean_distance(left, right)
            if distance > best_distance:
                best_distance = distance
                best_pair = (left.id, right.id)
    if best_pair is None:
        raise ValueError("At least two nodes are required.")
    return best_pair


def _projection_score(start: GraphNode, goal: GraphNode, candidate: GraphNode) -> tuple[float, float]:
    vx = goal.x - start.x
    vy = goal.y - start.y
    length_sq = max(vx * vx + vy * vy, 1e-9)
    wx = candidate.x - start.x
    wy = candidate.y - start.y
    projection = (wx * vx + wy * vy) / length_sq
    closest_x = start.x + projection * vx
    closest_y = start.y + projection * vy
    perpendicular = math.hypot(candidate.x - closest_x, candidate.y - closest_y)
    return projection, perpendicular


def _choose_backbone(nodes: list[GraphNode], start: str, goal: str, seed: int) -> list[str]:
    rng = random.Random(seed + 97)
    node_map = {node.id: node for node in nodes}
    candidates: list[tuple[float, float, str]] = []
    for node in nodes:
        if node.id in {start, goal}:
            continue
        projection, perpendicular = _projection_score(node_map[start], node_map[goal], node)
        if 0.05 <= projection <= 0.95:
            candidates.append((perpendicular, projection, node.id))
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))

    intermediate_count = max(3, min(5, len(nodes) // 4))
    chosen = candidates[: intermediate_count * 2]
    if len(chosen) < intermediate_count:
        remaining = [
            (_projection_score(node_map[start], node_map[goal], node)[1], node.id)
            for node in nodes
            if node.id not in {start, goal}
        ]
        remaining.sort()
        selected = [node_id for _, node_id in remaining[:intermediate_count]]
        selected.sort(key=lambda node_id: _projection_score(node_map[start], node_map[goal], node_map[node_id])[0])
        return [start, *selected, goal]

    rng.shuffle(chosen)
    selected = sorted(
        [node_id for _, _, node_id in chosen[:intermediate_count]],
        key=lambda node_id: _projection_score(node_map[start], node_map[goal], node_map[node_id])[0],
    )
    return [start, *selected, goal]


def build_graph_from_pairs(
    nodes: list[GraphNode],
    edge_pairs: Iterable[tuple[str, str]],
    *,
    start: str,
    goal: str,
) -> WeightedGraph:
    node_map = {node.id: node for node in nodes}
    canonical_pairs = {tuple(sorted((u, v))) for u, v in edge_pairs if u != v}
    edges = [
        GraphEdge(
            u=u,
            v=v,
            cost=round(euclidean_distance(node_map[u], node_map[v]), 3),
        )
        for u, v in sorted(canonical_pairs)
    ]
    return WeightedGraph(nodes=nodes, edges=edges, start=start, goal=goal)


def generate_sparse_geometric_graph(node_count: int = 16, seed: int = 7) -> WeightedGraph:
    nodes = _generate_positions(node_count, seed)
    start, goal = _choose_start_goal(nodes)
    backbone = _choose_backbone(nodes, start, goal, seed)
    edge_pairs: set[tuple[str, str]] = {
        tuple(sorted((left, right)))
        for left, right in zip(backbone, backbone[1:])
    }

    rng = random.Random(seed + 211)
    for node in nodes:
        degree_target = rng.randint(2, 4)
        neighbours = sorted(
            (
                (euclidean_distance(node, other), other.id)
                for other in nodes
                if other.id != node.id
            ),
            key=lambda item: (item[0], item[1]),
        )
        for _, neighbour_id in neighbours[:degree_target]:
            edge_pairs.add(tuple(sorted((node.id, neighbour_id))))

    return build_graph_from_pairs(nodes, edge_pairs, start=start, goal=goal)
