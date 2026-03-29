"""Curated example definitions for the weighted graph search demo."""

from __future__ import annotations

from ai9414.search.generator import build_graph_from_pairs, generate_sparse_geometric_graph
from ai9414.search.models import GraphNode, SearchExample


def _misleading_branch_example() -> SearchExample:
    nodes = [
        GraphNode(id="A", x=0.1, y=0.52),
        GraphNode(id="B", x=0.26, y=0.32),
        GraphNode(id="C", x=0.27, y=0.73),
        GraphNode(id="D", x=0.45, y=0.18),
        GraphNode(id="E", x=0.49, y=0.68),
        GraphNode(id="F", x=0.66, y=0.24),
        GraphNode(id="H", x=0.68, y=0.64),
        GraphNode(id="G", x=0.88, y=0.47),
    ]
    graph = build_graph_from_pairs(
        nodes,
        [
            ("A", "B"),
            ("A", "C"),
            ("B", "D"),
            ("C", "E"),
            ("D", "F"),
            ("E", "H"),
            ("F", "G"),
            ("H", "G"),
            ("D", "E"),
        ],
        start="A",
        goal="G",
    )
    return SearchExample(
        name="misleading_branch",
        title="Longer misleading branch",
        subtitle=(
            "DFS reaches a complete solution early on the lower branch, "
            "but a shorter path is only discovered after backtracking."
        ),
        graph=graph,
        metadata={"teaching_focus": "first-found is not necessarily optimal"},
    )


def _strong_pruning_example() -> SearchExample:
    nodes = [
        GraphNode(id="A", x=0.1, y=0.48),
        GraphNode(id="B", x=0.24, y=0.26),
        GraphNode(id="C", x=0.31, y=0.72),
        GraphNode(id="D", x=0.44, y=0.52),
        GraphNode(id="E", x=0.55, y=0.24),
        GraphNode(id="F", x=0.57, y=0.76),
        GraphNode(id="G", x=0.92, y=0.46),
        GraphNode(id="H", x=0.78, y=0.2),
        GraphNode(id="I", x=0.81, y=0.75),
    ]
    graph = build_graph_from_pairs(
        nodes,
        [
            ("A", "B"),
            ("A", "C"),
            ("A", "D"),
            ("B", "E"),
            ("E", "G"),
            ("C", "F"),
            ("F", "I"),
            ("D", "H"),
            ("H", "G"),
            ("D", "G"),
        ],
        start="A",
        goal="G",
    )
    return SearchExample(
        name="strong_pruning",
        title="Strong pruning",
        subtitle=(
            "An early decent route sets a best-cost bound that later branches cannot beat, "
            "so they are pruned without full expansion."
        ),
        graph=graph,
        metadata={"teaching_focus": "branch-and-bound pruning"},
    )


def build_examples(node_count: int = 16, seed: int = 7) -> dict[str, SearchExample]:
    default = SearchExample(
        name="default_sparse_graph",
        title="Default sparse graph",
        subtitle=(
            "A deterministic random geometric graph with a guaranteed backbone path "
            "between the start and goal."
        ),
        graph=generate_sparse_geometric_graph(node_count=node_count, seed=seed),
        metadata={"seed": seed, "node_count": node_count},
    )
    misleading = _misleading_branch_example()
    pruning = _strong_pruning_example()
    return {
        default.name: default,
        misleading.name: misleading,
        pruning.name: pruning,
    }
