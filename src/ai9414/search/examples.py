"""Generated weighted-graph configuration presets."""

from __future__ import annotations

from ai9414.search.generator import generate_weighted_graph
from ai9414.search.models import SearchExample


def build_examples() -> dict[str, SearchExample]:
    small = SearchExample(
        name="small",
        title="Small configuration",
        subtitle=(
            "A compact weighted graph with clear best-cost updates and pruning decisions."
        ),
        graph=generate_weighted_graph(size="small", seed=17),
        metadata={"difficulty": "small", "teaching_note": "The first complete path establishes the initial pruning bound."},
    )
    large = SearchExample(
        name="large",
        title="Large configuration",
        subtitle=(
            "A larger weighted graph with more backtracking and more opportunities for pruning."
        ),
        graph=generate_weighted_graph(size="large", seed=31),
        metadata={"difficulty": "large", "teaching_note": "Larger weighted graphs highlight pruning and backtracking more clearly."},
    )
    return {small.name: small, large.name: large}
