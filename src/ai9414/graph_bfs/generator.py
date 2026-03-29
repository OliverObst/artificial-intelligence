"""Procedural generation for the spatial graph BFS demo."""

from __future__ import annotations

from ai9414.graph_dfs.generator import SIZE_NODE_COUNTS
from ai9414.graph_dfs.generator import generate_spatial_graph as _generate_spatial_graph
from ai9414.graph_dfs.models import SpatialGraphDefinition


def generate_spatial_graph(*, size: str = "small", seed: int = 7) -> SpatialGraphDefinition:
    return _generate_spatial_graph(size=size, seed=seed)
