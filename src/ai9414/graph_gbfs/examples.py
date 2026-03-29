"""Named spatial graph configuration presets for greedy best-first search."""

from __future__ import annotations

from ai9414.graph_gbfs.generator import generate_weighted_graph
from ai9414.graph_gbfs.models import GraphGbfsExample


def build_examples() -> dict[str, GraphGbfsExample]:
    small = GraphGbfsExample(
        name="small",
        title="Small configuration",
        subtitle="A compact generated weighted graph configuration for quick greedy best-first playback.",
        graph=generate_weighted_graph(size="small", seed=17),
        metadata={
            "difficulty": "small",
            "teaching_note": "Watch how greedy best-first search chases the most promising-looking node first.",
        },
    )
    large = GraphGbfsExample(
        name="large",
        title="Large configuration",
        subtitle="A larger generated weighted graph configuration where the heuristic can lead the search down misleading routes.",
        graph=generate_weighted_graph(size="large", seed=31),
        metadata={
            "difficulty": "large",
            "teaching_note": "Greedy best-first search can reach the goal quickly without guaranteeing the cheapest path.",
        },
    )
    return {small.name: small, large.name: large}
