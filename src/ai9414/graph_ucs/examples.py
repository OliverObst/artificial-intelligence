"""Named spatial graph configuration presets for UCS."""

from __future__ import annotations

from ai9414.graph_ucs.generator import generate_weighted_graph
from ai9414.graph_ucs.models import GraphUcsExample


def build_examples() -> dict[str, GraphUcsExample]:
    small = GraphUcsExample(
        name="small",
        title="Small configuration",
        subtitle="A compact generated weighted graph configuration for quick uniform-cost playback.",
        graph=generate_weighted_graph(size="small", seed=17),
        metadata={"difficulty": "small", "teaching_note": "Watch how UCS always expands the cheapest frontier path next."},
    )
    large = GraphUcsExample(
        name="large",
        title="Large configuration",
        subtitle="A larger generated weighted graph configuration with a longer UCS frontier trace.",
        graph=generate_weighted_graph(size="large", seed=31),
        metadata={"difficulty": "large", "teaching_note": "Larger weighted graphs make cost-based expansion more visible."},
    )
    return {small.name: small, large.name: large}
