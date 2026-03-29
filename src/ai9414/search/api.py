"""Student-facing API for the weighted graph search demo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai9414.core import BaseEducationalApp
from ai9414.core.errors import AI9414Error
from ai9414.search.configs import SearchConfigModel
from ai9414.search.examples import build_examples
from ai9414.search.models import SearchExample
from ai9414.search.trace import build_search_trace


class SearchDemo(BaseEducationalApp):
    """Precomputed weighted graph search demo with step-by-step replay."""

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
            app_title="Search Demo - Weighted Graph",
            execution_mode="precomputed",
            mode=mode,
        )
        self.node_count = node_count
        self.seed = seed
        self.examples = build_examples(node_count=node_count, seed=seed)
        self.example: SearchExample = self.examples["default_sparse_graph"]
        self.options = {"playback_speed": 1.0}
        self.load_example("default_sparse_graph")

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
        self.reset_runtime()

    def load_config(self, path: str) -> None:
        raw = self.load_base_config(path)
        config = SearchConfigModel.model_validate(raw)
        self.config_name = Path(path).name
        self.example_name = None
        self.options = {"playback_speed": 1.0}
        self.set_options(**config.options)
        self.example = SearchExample(
            name="custom_config",
            title=config.title,
            subtitle=config.data.subtitle,
            graph=config.data.graph,
        )
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
                    details={"allowed_range": [0.5, 2.0]},
                ) from exc
            if not 0.5 <= playback_speed <= 2.0:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="Playback speed must be between 0.5 and 2.0.",
                    details={"allowed_range": [0.5, 2.0]},
                )
            self.options["playback_speed"] = playback_speed

    def build_initial_state(self) -> dict[str, Any]:
        trace = build_search_trace(self.example)
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
                "example_title": self.example.title,
                "example_subtitle": self.example.subtitle,
                "playback_speed": self.options["playback_speed"],
            },
        }

    def build_trace(self) -> dict[str, Any]:
        if self._trace_bundle is None:
            self._trace_bundle = build_search_trace(self.example)
        return self._trace_bundle.model_dump()

    def reset_runtime(self) -> None:
        self.current_step = 0
        self._base_state_data = {}
        self._current_state_data = {}
        self._trace_bundle = None
        self._trace_cache_complete = False
        self.ensure_runtime_ready()
