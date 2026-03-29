"""Named spatial graph configuration presets for A* search."""

from __future__ import annotations

from ai9414.graph_astar.generator import generate_weighted_graph
from ai9414.graph_astar.models import GraphAStarExample


def build_examples() -> dict[str, GraphAStarExample]:
    small = GraphAStarExample(
        name="small",
        title="Small configuration",
        subtitle="A compact generated weighted graph configuration for quick A* playback.",
        graph=generate_weighted_graph(size="small", seed=17),
        metadata={
            "difficulty": "small",
            "teaching_note": "Watch how A* balances path cost so far with straight-line distance to the goal.",
        },
    )
    large = GraphAStarExample(
        name="large",
        title="Large configuration",
        subtitle="A larger generated weighted graph configuration where A* has a richer frontier history.",
        graph=generate_weighted_graph(size="large", seed=31),
        metadata={
            "difficulty": "large",
            "teaching_note": "With an admissible heuristic, A* still guarantees an optimal path.",
        },
    )
    return {small.name: small, large.name: large}
