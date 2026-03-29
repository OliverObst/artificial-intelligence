"""Named spatial graph configuration presets for BFS."""

from __future__ import annotations

from ai9414.graph_bfs.generator import generate_spatial_graph
from ai9414.graph_bfs.models import GraphBfsExample


def build_examples() -> dict[str, GraphBfsExample]:
    small = GraphBfsExample(
        name="small",
        title="Small configuration",
        subtitle="A compact generated spatial graph configuration for quick BFS playback.",
        graph=generate_spatial_graph(size="small", seed=17),
        metadata={"difficulty": "small", "teaching_note": "Watch how BFS expands outward level by level."},
    )
    large = GraphBfsExample(
        name="large",
        title="Large configuration",
        subtitle="A larger generated spatial graph configuration with a broader BFS frontier.",
        graph=generate_spatial_graph(size="large", seed=16),
        metadata={"difficulty": "large", "teaching_note": "Larger sparse graphs make the breadth-first frontier easier to see."},
    )
    return {small.name: small, large.name: large}
