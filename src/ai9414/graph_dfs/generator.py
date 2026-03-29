"""Procedural generation for the spatial graph DFS demo."""

from __future__ import annotations

from ai9414.graph_dfs.models import SpatialGraphDefinition, SpatialGraphEdge, SpatialGraphNode
from ai9414.search.generator import generate_sparse_geometric_graph

SIZE_NODE_COUNTS = {
    "small": 16,
    "large": 24,
}


def generate_spatial_graph(*, size: str = "small", seed: int = 7) -> SpatialGraphDefinition:
    if size not in SIZE_NODE_COUNTS:
        raise ValueError(f"Unknown graph size '{size}'.")

    weighted_graph = generate_sparse_geometric_graph(
        node_count=SIZE_NODE_COUNTS[size],
        seed=seed,
    )
    return SpatialGraphDefinition(
        nodes=[
            SpatialGraphNode(id=node.id, x=node.x, y=node.y)
            for node in weighted_graph.nodes
        ],
        edges=[
            SpatialGraphEdge(u=edge.u, v=edge.v)
            for edge in weighted_graph.edges
        ],
        start=weighted_graph.start,
        goal=weighted_graph.goal,
        seed=seed,
        size=size,
    )
