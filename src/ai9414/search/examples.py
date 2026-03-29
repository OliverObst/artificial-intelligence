"""Generated weighted-graph configuration presets."""

from __future__ import annotations

from ai9414.search.generator import generate_weighted_graph
from ai9414.search.models import SearchExample


def build_examples() -> dict[str, SearchExample]:
    small = SearchExample(
        name="small",
        title="Small configuration",
        subtitle=(
            "A compact generated weighted graph for branch-and-bound playback. "
            "It remains readable while still showing best-cost updates and pruning."
        ),
        graph=generate_weighted_graph(size="small", seed=17),
        metadata={"difficulty": "small", "teaching_note": "Watch how a first solution creates a pruning bound."},
    )
    large = SearchExample(
        name="large",
        title="Large configuration",
        subtitle=(
            "A larger generated weighted graph with a longer branch-and-bound trace, "
            "more backtracking, and more pruning opportunities."
        ),
        graph=generate_weighted_graph(size="large", seed=31),
        metadata={"difficulty": "large", "teaching_note": "Larger weighted graphs make branch-and-bound behaviour more visible."},
    )
    return {small.name: small, large.name: large}
