"""Student-facing API for the reasoning-with-uncertainty demo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai9414.core import BaseEducationalApp
from ai9414.core.errors import AI9414Error
from ai9414.uncertainty.examples import build_examples
from ai9414.uncertainty.models import UncertaintyConfigModel, UncertaintyExample, UncertaintyProblem
from ai9414.uncertainty.trace import build_uncertainty_trace, build_uncertainty_trace_from_problem


class BeliefStateExplorer(BaseEducationalApp):
    """Playback-first Bayes-filter localisation demo with curated office scenarios and live Python solving."""

    def __init__(
        self,
        *,
        example: str | None = None,
        problem: UncertaintyProblem | None = None,
        mode: str = "student",
        execution_mode: str = "precomputed",
    ) -> None:
        if execution_mode != "precomputed":
            raise AI9414Error(
                code="unsupported_action",
                message="BeliefStateExplorer currently supports precomputed execution mode only.",
            )
        super().__init__(
            app_type="uncertainty",
            app_title="Reasoning with Uncertainty - Belief-State Explorer",
            execution_mode="precomputed",
            mode=mode,
        )
        self.examples = build_examples()
        self.example: UncertaintyExample | None = None
        self.problem: UncertaintyProblem | None = None
        self.options: dict[str, Any] = {"playback_speed": 1.0}

        if problem is not None:
            self.load_problem(problem)
        else:
            self.load_example(example or "office_localisation_basic")

    def list_examples(self) -> list[str]:
        return list(self.examples.keys())

    def load_example(self, name: str) -> None:
        if name not in self.examples:
            raise AI9414Error(
                code="example_not_found",
                message=f"Example '{name}' was not found.",
                details={"available_examples": sorted(self.examples)},
            )
        self.example_name = name
        self.config_name = None
        self.example = self.examples[name]
        self.problem = self.example.problem
        self.reset_runtime()

    def load_problem(self, problem: UncertaintyProblem) -> None:
        self.example_name = None
        self.config_name = None
        self.example = None
        self.problem = UncertaintyProblem.model_validate(problem.model_dump())
        self.reset_runtime()

    def load_config(self, path: str) -> None:
        raw = self.load_base_config(path)
        config = UncertaintyConfigModel.model_validate(raw)
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

    def set_belief(self, belief: dict[str, float]) -> None:
        if self.problem is None:
            raise AI9414Error(code="trace_generation_failed", message="No uncertainty problem is loaded.")
        self.problem = self.problem.model_copy(update={"initial_belief": dict(belief)})
        if self.example is not None:
            self.example = self.example.model_copy(update={"problem": self.problem})
        self.reset_runtime()

    def step(self, *, action: str | None = None) -> dict[str, Any]:
        self.ensure_runtime_ready()
        trace = self._ensure_complete_trace()
        if self.current_step >= len(trace.steps):
            return self.build_state_payload()
        if action is not None:
            expected = trace.steps[self.current_step].state_patch.get("uncertainty", {}).get("current_action")
            if expected and action != expected:
                raise AI9414Error(
                    code="invalid_option_value",
                    message=f"Expected action '{expected}' at the next replay step, not '{action}'.",
                )
        self.current_step += 1
        self._current_state_data = self._state_at_index(self.current_step)
        return self.build_state_payload()

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
            raise AI9414Error(code="trace_generation_failed", message="No uncertainty problem is loaded.")
        if self.example is not None:
            return build_uncertainty_trace(self.example)
        return build_uncertainty_trace_from_problem(
            self.problem,
            title=self.problem.title,
            subtitle=self.problem.subtitle,
            trace_id="uncertainty-custom",
        )
