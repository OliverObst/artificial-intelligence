"""Installed command-line interface for ai9414 demos."""

from __future__ import annotations

import argparse
import difflib
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TextIO

from ai9414.core import AI9414Error, AppLauncher, BaseEducationalApp


@dataclass(frozen=True)
class DemoSpec:
    """Describe one installed demo entry."""

    name: str
    title: str
    description: str
    default_example: str
    factory: Callable[[], BaseEducationalApp]
    aliases: tuple[str, ...] = ()
    example_names: Callable[[], Sequence[str]] | None = None


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level parser for the installed CLI."""

    parser = argparse.ArgumentParser(
        prog="ai9414",
        description="Launch ai9414 teaching demos from an installed package.",
    )
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser(
        "list",
        help="List available demos or curated examples.",
    )
    list_parser.add_argument(
        "--examples",
        metavar="DEMO",
        help="Show the curated example names for one demo.",
    )

    demo_parser = subparsers.add_parser(
        "demo",
        help="Launch one demo in a local browser session.",
    )
    demo_parser.add_argument(
        "name",
        help="Demo name. Run 'ai9414 list' to see the available options.",
    )
    source_group = demo_parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--example",
        help="Curated example name to load before launching the demo.",
    )
    source_group.add_argument(
        "--config",
        help="Path to a JSON configuration file to load before launching the demo.",
    )
    demo_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface to bind the local demo server to.",
    )
    demo_parser.add_argument(
        "--port",
        type=int,
        help="Port for the local demo server. If omitted, a free port is chosen automatically.",
    )
    demo_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start the local server without opening a browser window automatically.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the installed ai9414 CLI."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.command is None:
            _print_overview(parser)
            return 0
        if args.command == "list":
            return _run_list_command(args)
        if args.command == "demo":
            return _run_demo_command(args)
    except AI9414Error as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        return 1

    parser.print_help()
    return 1


def _run_list_command(args: argparse.Namespace) -> int:
    if args.examples:
        spec = resolve_demo_spec(args.examples)
        print(f"{spec.name} examples:")
        for example_name in _demo_example_names(spec):
            print(f"- {example_name}")
        return 0

    print("Available demos:")
    for spec in demo_specs():
        alias_text = ""
        if spec.aliases:
            alias_text = f" | aliases: {', '.join(spec.aliases)}"
        print(
            f"- {spec.name}: {spec.description} "
            f"(default example: {spec.default_example}{alias_text})"
        )
    print()
    print("Start one with: ai9414 demo <name>")
    print("Show example names with: ai9414 list --examples <name>")
    return 0


def _run_demo_command(args: argparse.Namespace) -> int:
    spec = resolve_demo_spec(args.name)
    app = spec.factory()

    if args.config:
        app.load_config(args.config)
    elif args.example:
        app.load_example(args.example)

    launcher = AppLauncher(
        app,
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
    )
    launcher.start()
    return 0


def _print_overview(parser: argparse.ArgumentParser, *, file: TextIO | None = None) -> None:
    output = file or sys.stdout
    parser.print_help(file=output)
    print(file=output)
    print("Examples:", file=output)
    print("  ai9414 list", file=output)
    print("  ai9414 demo graph-bnb", file=output)
    print("  python -m ai9414 demo graph-dfs", file=output)


def resolve_demo_spec(name: str) -> DemoSpec:
    """Resolve a canonical or alias demo name."""

    normalised = _normalise_demo_name(name)
    for spec in demo_specs():
        if normalised == spec.name:
            return spec
        if normalised in spec.aliases:
            return spec

    suggestions = difflib.get_close_matches(normalised, _known_demo_names(), n=3)
    hint = ""
    if suggestions:
        hint = f" Did you mean: {', '.join(suggestions)}?"
    raise AI9414Error(
        code="demo_not_found",
        message=f"Unknown demo '{name}'. Run 'ai9414 list' to see the available demos.{hint}",
    )


def _known_demo_names() -> list[str]:
    names: list[str] = []
    for spec in demo_specs():
        names.append(spec.name)
        names.extend(spec.aliases)
    return names


def _normalise_demo_name(name: str) -> str:
    return str(name).strip().lower().replace("_", "-")


def _demo_example_names(spec: DemoSpec) -> list[str]:
    if spec.example_names is not None:
        return list(spec.example_names())
    app = spec.factory()
    return list(app.list_examples())


def demo_specs() -> tuple[DemoSpec, ...]:
    """Return the installed demo catalogue."""

    return (
        DemoSpec(
            name="labyrinth",
            title="Labyrinth DFS",
            description="Labyrinth depth-first search",
            default_example="small",
            factory=_create_labyrinth_demo,
        ),
        DemoSpec(
            name="graph-dfs",
            title="Graph DFS",
            description="Spatial graph depth-first search",
            default_example="small",
            factory=_create_graph_dfs_demo,
            aliases=("graph_dfs",),
        ),
        DemoSpec(
            name="graph-bfs",
            title="Graph BFS",
            description="Spatial graph breadth-first search",
            default_example="small",
            factory=_create_graph_bfs_demo,
            aliases=("graph_bfs",),
        ),
        DemoSpec(
            name="graph-gbfs",
            title="Graph Greedy Best-First Search",
            description="Spatial graph greedy best-first search",
            default_example="small",
            factory=_create_graph_gbfs_demo,
            aliases=("graph_gbfs",),
        ),
        DemoSpec(
            name="graph-astar",
            title="Graph A* Search",
            description="Spatial graph A* search",
            default_example="small",
            factory=_create_graph_astar_demo,
            aliases=("graph_astar",),
        ),
        DemoSpec(
            name="graph-ucs",
            title="Graph Uniform-Cost Search",
            description="Spatial graph uniform-cost search",
            default_example="small",
            factory=_create_graph_ucs_demo,
            aliases=("graph_ucs",),
        ),
        DemoSpec(
            name="graph-bnb",
            title="Graph Branch-and-Bound Search",
            description="Spatial graph branch-and-bound search",
            default_example="small",
            factory=_create_graph_bnb_demo,
            aliases=("graph_branch_and_bound", "graph-branch-and-bound"),
        ),
        DemoSpec(
            name="logic-dpll",
            title="Visual DPLL",
            description="Propositional logic DPLL",
            default_example="simple_sat",
            factory=_create_logic_demo,
            aliases=("logic_dpll",),
            example_names=_list_logic_examples,
        ),
        DemoSpec(
            name="uncertainty",
            title="Belief-State Explorer",
            description="Reasoning with uncertainty belief-state explorer",
            default_example="office_localisation_basic",
            factory=_create_uncertainty_demo,
        ),
        DemoSpec(
            name="foundation-models",
            title="Tokenisation Explorer",
            description="Foundation models tokenisation explorer",
            default_example="simple_sentence",
            factory=_create_foundation_models_demo,
            aliases=("foundation_models",),
        ),
        DemoSpec(
            name="csp-map",
            title="CSP Map Colouring",
            description="CSP map colouring",
            default_example="australia",
            factory=_create_csp_demo,
            aliases=("csp", "csp_map"),
        ),
        DemoSpec(
            name="csp-delivery",
            title="CSP Delivery Scheduling",
            description="CSP delivery time-slot assignment",
            default_example="weekday_schedule",
            factory=_create_delivery_csp_demo,
            aliases=("delivery_csp", "csp_delivery"),
        ),
        DemoSpec(
            name="strips",
            title="STRIPS Planning",
            description="STRIPS planning",
            default_example="canonical_delivery",
            factory=_create_strips_demo,
        ),
    )


def _create_labyrinth_demo() -> BaseEducationalApp:
    from ai9414.labyrinth import LabyrinthDemo

    return LabyrinthDemo()


def _create_graph_dfs_demo() -> BaseEducationalApp:
    from ai9414.graph_dfs import GraphDfsDemo

    return GraphDfsDemo()


def _create_graph_bfs_demo() -> BaseEducationalApp:
    from ai9414.graph_bfs import GraphBfsDemo

    return GraphBfsDemo()


def _create_graph_gbfs_demo() -> BaseEducationalApp:
    from ai9414.graph_gbfs import GraphGbfsDemo

    return GraphGbfsDemo()


def _create_graph_astar_demo() -> BaseEducationalApp:
    from ai9414.graph_astar import GraphAStarDemo

    return GraphAStarDemo()


def _create_graph_ucs_demo() -> BaseEducationalApp:
    from ai9414.graph_ucs import GraphUcsDemo

    return GraphUcsDemo()


def _create_graph_bnb_demo() -> BaseEducationalApp:
    from ai9414.search import SearchDemo

    return SearchDemo()


def _create_logic_demo() -> BaseEducationalApp:
    from ai9414.logic import DpllDemo

    return DpllDemo()


def _create_uncertainty_demo() -> BaseEducationalApp:
    from ai9414.uncertainty import BeliefStateExplorer

    return BeliefStateExplorer()


def _create_foundation_models_demo() -> BaseEducationalApp:
    from ai9414.foundation_models import TokenisationExplorer

    return TokenisationExplorer()


def _create_csp_demo() -> BaseEducationalApp:
    from ai9414.csp import CSPDemo

    return CSPDemo()


def _create_delivery_csp_demo() -> BaseEducationalApp:
    from ai9414.delivery_csp import DeliveryCSPDemo

    return DeliveryCSPDemo()


def _create_strips_demo() -> BaseEducationalApp:
    from ai9414.strips import StripsDemo

    return StripsDemo()


def _list_logic_examples() -> Sequence[str]:
    from ai9414.logic.examples import build_examples

    return list(build_examples())
