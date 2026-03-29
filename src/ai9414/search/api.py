"""Student-facing API for the spatial graph branch-and-bound demo."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from ai9414.core import ActionResponse, BaseEducationalApp
from ai9414.core.errors import AI9414Error
from ai9414.search.configs import SearchConfigModel
from ai9414.search.examples import build_examples
from ai9414.search.generator import SIZE_NODE_COUNTS, generate_weighted_graph
from ai9414.search.models import SearchExample, WeightedGraph
from ai9414.search.solver import solve_weighted_graph
from ai9414.search.trace import build_search_trace, build_search_trace_from_definition


class SearchDemo(BaseEducationalApp):
    """Playback-first spatial graph branch-and-bound demo with optional live Python solving."""

    _MIN_EVENT_COUNTS_BY_SIZE = {
        "small": {"prune": 1, "backtrack": 2},
        "large": {"prune": 4, "backtrack": 6},
    }

    def __init__(
        self,
        *,
        node_count: int = 16,
        seed: int = 7,
        mode: str = "student",
        execution_mode: str = "precomputed",
    ) -> None:
        if execution_mode != "precomputed":
            raise AI9414Error(
                code="unsupported_action",
                message="SearchDemo currently supports precomputed execution mode only.",
            )
        super().__init__(
            app_type="search",
            app_title="Search Demo - Graph Branch-and-Bound",
            execution_mode="precomputed",
            mode=mode,
        )
        self.node_count = node_count
        self.seed = seed
        self.examples = build_examples()
        self.example: SearchExample | None = self.examples["small"]
        self.graph: WeightedGraph = self.example.graph
        self.options = {"playback_speed": 1.0}
        self.generated_size = self.graph.size or "small"
        self.generated_seed = self.graph.seed or 17
        self.load_example("small")

    def list_examples(self) -> list[str]:
        return list(self.examples.keys())

    def load_example(self, name: str) -> None:
        if name not in self.examples:
            raise AI9414Error(
                code="example_not_found",
                message=f"Example '{name}' was not found.",
                details={"available_examples": self.list_examples()},
            )
        self.example_name = name
        self.config_name = None
        self.example = self.examples[name]
        self.graph = self.example.graph
        self.generated_size = self.graph.size or "small"
        self.generated_seed = self.graph.seed or 17
        self.reset_runtime()

    def load_config(self, path: str) -> None:
        raw = self.load_base_config(path)
        config = SearchConfigModel.model_validate(raw)
        self.config_name = Path(path).name
        self.example_name = None
        self.example = None
        self.options = {"playback_speed": 1.0}
        self.set_options(**config.options)
        self.graph = config.data.graph
        self.generated_size = self.graph.size or "small"
        self.generated_seed = self.graph.seed or 1
        self.reset_runtime()

    def set_options(self, **kwargs: Any) -> None:
        allowed = {"playback_speed"}
        unknown = sorted(set(kwargs) - allowed)
        if unknown:
            raise AI9414Error(
                code="invalid_option_value",
                message=f"Unknown option(s): {', '.join(unknown)}.",
                details={"allowed_options": sorted(allowed)},
            )

        if "playback_speed" in kwargs:
            try:
                playback_speed = float(kwargs["playback_speed"])
            except (TypeError, ValueError) as exc:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="Playback speed must be a number.",
                    details={"allowed_range": [0.5, 5.0]},
                ) from exc
            if not 0.5 <= playback_speed <= 5.0:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="Playback speed must be between 0.5 and 5.0.",
                    details={"allowed_range": [0.5, 5.0]},
                )
            self.options["playback_speed"] = playback_speed

    def build_initial_state(self) -> dict[str, Any]:
        trace = self._build_bundle()
        self._trace_bundle = trace
        base_data = trace.initial_state
        return {
            "schema_version": "1.0",
            "app_type": self.app_type,
            "example_name": self.example_name,
            "config_name": self.config_name,
            "options": self.options,
            "view": {"current_step": self.current_step},
            "data": {
                **base_data,
                "playback_speed": self.options["playback_speed"],
                "live_python": {
                    "size": self.generated_size,
                    "seed": self.generated_seed,
                    "available_sizes": sorted(SIZE_NODE_COUNTS),
                    "backend_url": "http://127.0.0.1:9414/solve",
                },
            },
        }

    def build_trace(self) -> dict[str, Any]:
        if self._trace_bundle is None:
            self._trace_bundle = self._build_bundle()
        return self._trace_bundle.model_dump()

    def handle_app_command(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        if command != "generate_graph":
            raise AI9414Error(
                code="unsupported_action",
                message=f"Search command '{command}' is not supported.",
            )

        size = str(payload.get("size", "small"))
        seed_payload = payload.get("seed")
        seed = int(seed_payload) if seed_payload is not None else None
        self.example = None
        self.example_name = None
        self.config_name = None
        self.graph, selected_seed = self._generate_with_branch_and_bound_visibility(size=size, seed=seed)
        self.generated_size = size
        self.generated_seed = selected_seed
        self.reset_runtime()
        return ActionResponse(
            state=self.build_state_payload(),
            trace=self.get_trace_payload(),
            trace_complete=True,
        ).model_dump()

    def _build_bundle(self):
        if self.example is None:
            return build_search_trace_from_definition(
                self.graph,
                title="Generated weighted graph",
                subtitle=(
                    "A generated weighted graph solved with built-in branch-and-bound playback. "
                    "Switch to live Python mode to compare it with your own solver."
                ),
            )
        return build_search_trace(self.example)

    def _generate_with_branch_and_bound_visibility(
        self,
        *,
        size: str,
        seed: int | None,
    ) -> tuple[WeightedGraph, int]:
        if seed is not None:
            return generate_weighted_graph(size=size, seed=seed), seed

        minimums = self._MIN_EVENT_COUNTS_BY_SIZE.get(size, {"prune": 0, "backtrack": 0})
        chosen_graph: WeightedGraph | None = None
        chosen_seed: int | None = None

        for _ in range(200):
            candidate_seed = random.randint(1, 999_999)
            candidate = generate_weighted_graph(size=size, seed=candidate_seed)
            result = solve_weighted_graph(candidate)
            event_counts = {
                "prune": sum(1 for step in result.raw_steps if step.event_type == "prune"),
                "backtrack": sum(1 for step in result.raw_steps if step.event_type == "backtrack"),
            }
            chosen_graph = candidate
            chosen_seed = candidate_seed
            if all(event_counts[name] >= minimums[name] for name in minimums):
                return candidate, candidate_seed

        if chosen_graph is None or chosen_seed is None:
            raise AI9414Error(
                code="generation_failed",
                message="Could not generate a weighted graph with the required playback properties.",
            )
        return chosen_graph, chosen_seed

    def reset_runtime(self) -> None:
        self.current_step = 0
        self._base_state_data = {}
        self._current_state_data = {}
        self._trace_bundle = None
        self._trace_cache_complete = False
        self.ensure_runtime_ready()
