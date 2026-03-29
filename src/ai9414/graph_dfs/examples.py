"""Named spatial graph configuration presets."""

from __future__ import annotations

from ai9414.graph_dfs.generator import generate_spatial_graph
from ai9414.graph_dfs.models import GraphDfsExample


def build_examples() -> dict[str, GraphDfsExample]:
    small = GraphDfsExample(
        name="small",
        title="Small configuration",
        subtitle="A compact generated spatial graph configuration for quick DFS playback.",
        graph=generate_spatial_graph(size="small", seed=17),
        metadata={"difficulty": "small", "teaching_note": "Watch how DFS commits to one branch in the graph."},
    )
    large = GraphDfsExample(
        name="large",
        title="Large configuration",
        subtitle="A larger generated spatial graph configuration with a longer DFS trace and visible backtracking.",
        graph=generate_spatial_graph(size="large", seed=16),
        metadata={"difficulty": "large", "teaching_note": "Larger sparse graphs make backtracking more visible."},
    )
    return {small.name: small, large.name: large}
