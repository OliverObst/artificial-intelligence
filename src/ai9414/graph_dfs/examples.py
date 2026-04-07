"""Named spatial graph configuration presets."""

from __future__ import annotations

from ai9414.graph_dfs.generator import generate_spatial_graph
from ai9414.graph_dfs.models import GraphDfsExample


def build_examples() -> dict[str, GraphDfsExample]:
    small = GraphDfsExample(
        name="small",
        title="Small configuration",
        subtitle="A compact spatial graph with a clear DFS branch order.",
        graph=generate_spatial_graph(size="small", seed=17),
        metadata={"difficulty": "small", "teaching_note": "DFS commits to one branch until it must backtrack."},
    )
    large = GraphDfsExample(
        name="large",
        title="Large configuration",
        subtitle="A larger spatial graph with longer DFS branches and more visible backtracking.",
        graph=generate_spatial_graph(size="large", seed=16),
        metadata={"difficulty": "large", "teaching_note": "Sparse structure makes DFS backtracking easier to follow."},
    )
    return {small.name: small, large.name: large}
