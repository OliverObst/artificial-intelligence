"""Procedural generation for the spatial graph UCS demo."""

from __future__ import annotations

from ai9414.search.generator import SIZE_NODE_COUNTS
from ai9414.search.generator import generate_weighted_graph as _generate_weighted_graph
from ai9414.search.models import WeightedGraph


def generate_weighted_graph(*, size: str = "small", seed: int = 7) -> WeightedGraph:
    return _generate_weighted_graph(size=size, seed=seed)
