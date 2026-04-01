"""Student-facing API for the STRIPS planning demo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai9414.core import BaseEducationalApp
from ai9414.core.errors import AI9414Error
from ai9414.strips.examples import build_examples
from ai9414.strips.models import StripsConfigModel, StripsExample, StripsProblem
from ai9414.strips.trace import build_strips_trace, build_strips_trace_from_problem


class StripsDemo(BaseEducationalApp):
    """Playback-first STRIPS planning demo with curated office examples and live Python solving."""

    def __init__(
        self,
        *,
        problem: str | StripsProblem | None = None,
        mode: str = "student",
        execution_mode: str = "precomputed",
    ) -> None:
        if execution_mode != "precomputed":
            raise AI9414Error(
                code="unsupported_action",
                message="StripsDemo currently supports precomputed execution mode only.",
            )
        super().__init__(
            app_type="strips",
            app_title="Planning Demo - STRIPS Delivery",
            execution_mode="precomputed",
            mode=mode,
        )
        self.examples = build_examples()
        self.example: StripsExample | None = None
        self.problem: StripsProblem | None = None
        self.options: dict[str, Any] = {"playback_speed": 1.0}

        if isinstance(problem, StripsProblem):
            self.load_problem(problem)
        else:
            self.load_example(problem or "canonical_delivery")

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
        self.problem = self.example.problem
        self.reset_runtime()

    def load_problem(self, problem: StripsProblem) -> None:
        self.example_name = None
        self.config_name = None
        self.example = None
        self.problem = StripsProblem.model_validate(problem.model_dump())
        self.reset_runtime()

    def load_config(self, path: str) -> None:
        raw = self.load_base_config(path)
        config = StripsConfigModel.model_validate(raw)
        self.example_name = None
        self.config_name = Path(path).name
        self.example = None
        self.problem = config.data.problem
        self.options = {"playback_speed": 1.0}
        self.set_options(**config.options)
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
            playback_speed = float(kwargs["playback_speed"])
            if not 0.5 <= playback_speed <= 5.0:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="Playback speed must be between 0.5 and 5.0.",
                    details={"allowed_range": [0.5, 5.0]},
                )
            self.options["playback_speed"] = playback_speed

    def solve(self) -> dict[str, Any]:
        self.ensure_runtime_ready()
        return self.get_trace_payload()

    def build_initial_state(self) -> dict[str, Any]:
        bundle = self._build_bundle()
        self._trace_bundle = bundle
        data = {
            **bundle.initial_state,
            "playback_speed": self.options["playback_speed"],
            "live_python": {
                "backend_url": "http://127.0.0.1:9414/solve",
            },
        }
        return {
            "schema_version": "1.0",
            "app_type": self.app_type,
            "example_name": self.example_name,
            "config_name": self.config_name,
            "options": self.options,
            "view": {"current_step": self.current_step},
            "data": data,
        }

    def build_trace(self) -> dict[str, Any]:
        if self._trace_bundle is None:
            self._trace_bundle = self._build_bundle()
        return self._trace_bundle.model_dump()

    def reset_runtime(self) -> None:
        self.current_step = 0
        self._base_state_data = {}
        self._current_state_data = {}
        self._trace_bundle = None
        self._trace_cache_complete = False
        self.ensure_runtime_ready()

    def _build_bundle(self):
        if self.problem is None:
            raise AI9414Error(code="trace_generation_failed", message="No STRIPS problem is loaded.")
        if self.example is not None:
            return build_strips_trace(self.example)
        return build_strips_trace_from_problem(
            self.problem,
            title=self.problem.title,
            subtitle=self.problem.subtitle,
        )
