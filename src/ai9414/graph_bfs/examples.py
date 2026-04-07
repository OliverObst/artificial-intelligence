"""Named spatial graph configuration presets for BFS."""

from __future__ import annotations

from ai9414.graph_bfs.generator import generate_spatial_graph
from ai9414.graph_bfs.models import GraphBfsExample


def build_examples() -> dict[str, GraphBfsExample]:
    small = GraphBfsExample(
        name="small",
        title="Small configuration",
        subtitle="A compact spatial graph with a clear breadth-first frontier.",
        graph=generate_spatial_graph(size="small", seed=17),
        metadata={"difficulty": "small", "teaching_note": "BFS expands nodes level by level from the start."},
    )
    large = GraphBfsExample(
        name="large",
        title="Large configuration",
        subtitle="A larger spatial graph with a broader breadth-first frontier.",
        graph=generate_spatial_graph(size="large", seed=16),
        metadata={"difficulty": "large", "teaching_note": "The wider frontier makes the breadth-first expansion pattern easier to see."},
    )
    return {small.name: small, large.name: large}
