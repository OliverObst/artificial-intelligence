"""Named spatial graph configuration presets for greedy best-first search."""

from __future__ import annotations

from ai9414.graph_gbfs.generator import generate_weighted_graph
from ai9414.graph_gbfs.models import GraphGbfsExample


def build_examples() -> dict[str, GraphGbfsExample]:
    small = GraphGbfsExample(
        name="small",
        title="Small configuration",
        subtitle="A compact weighted graph with a clear heuristic-driven frontier.",
        graph=generate_weighted_graph(size="small", seed=17),
        metadata={
            "difficulty": "small",
            "teaching_note": "Greedy best-first search selects the frontier node with the best heuristic estimate.",
        },
    )
    large = GraphGbfsExample(
        name="large",
        title="Large configuration",
        subtitle="A larger weighted graph where the heuristic can favour longer routes.",
        graph=generate_weighted_graph(size="large", seed=31),
        metadata={
            "difficulty": "large",
            "teaching_note": "Greedy best-first search can reach the goal quickly without guaranteeing the cheapest path.",
        },
    )
    return {small.name: small, large.name: large}
