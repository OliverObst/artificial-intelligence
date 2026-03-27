"""Placeholder app used to prove the Phase 1 platform contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from ai9414.core import BaseEducationalApp
from ai9414.core.errors import AI9414Error
from ai9414.core.models import TraceBundle, TraceStep, TraceSummary

EXAMPLES: dict[str, dict[str, Any]] = {
    "count_to_three": {
        "title": "Count to Three",
        "data": {"target": 3, "step_size": 1},
        "options": {"pace": "normal"},
    },
    "count_by_twos": {
        "title": "Count by Twos",
        "data": {"target": 8, "step_size": 2},
        "options": {"pace": "normal"},
    },
}


class PlaceholderDemo(BaseEducationalApp):
    """Dummy implementation that demonstrates both execution modes."""

    def __init__(self, execution_mode: str = "precomputed") -> None:
        super().__init__(
            app_type="placeholder",
            app_title="AI9414 Placeholder Demo",
            execution_mode=execution_mode,
        )
        self.example = copy_example("count_to_three")
        self.options = dict(self.example["options"])
        self.load_example("count_to_three")

    def list_examples(self) -> list[str]:
        return sorted(EXAMPLES.keys())

    def load_example(self, name: str) -> None:
        if name not in EXAMPLES:
            raise AI9414Error(
                code="example_not_found",
                message=f"Example '{name}' was not found.",
                details={"available_examples": self.list_examples()},
            )
        self.example_name = name
        self.config_name = None
        self.example = copy_example(name)
        self.options = dict(self.example.get("options", {}))
        self.reset_runtime()

    def load_config(self, path: str) -> None:
        config = self.load_base_config(path)
        options = dict(config.get("options", {}))
        self.set_options(**options)
        self.example_name = None
        self.config_name = Path(path).name
        self.example = {
            "title": config["title"],
            "data": {
                "target": int(config["data"].get("target", 3)),
                "step_size": int(config["data"].get("step_size", 1)),
            },
            "options": options,
        }
        self.options = options
        self.reset_runtime()

    def set_options(self, **kwargs: Any) -> None:
        allowed = {"pace"}
        unknown = sorted(set(kwargs) - allowed)
        if unknown:
            raise AI9414Error(
                code="invalid_option_value",
                message=f"Unknown option(s): {', '.join(unknown)}.",
                details={"allowed_options": sorted(allowed)},
            )

        if "pace" in kwargs:
            pace = kwargs["pace"]
            if pace not in {"slow", "normal", "fast"}:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="Invalid pace. Allowed values: slow, normal, fast.",
                    details={"allowed_values": ["slow", "normal", "fast"]},
                )
            self.options["pace"] = pace

    def build_initial_state(self) -> dict[str, Any]:
        target = int(self.example["data"]["target"])
        step_size = int(self.example["data"]["step_size"])
        return {
            "schema_version": "1.0",
            "app_type": self.app_type,
            "example_name": self.example_name,
            "options": self.options,
            "view": {"current_step": self.current_step},
            "data": {
                "counter": 0,
                "target": target,
                "step_size": step_size,
                "history": [0],
                "status": "ready",
                "pace": self.options.get("pace", "normal"),
            },
        }

    def build_trace(self) -> dict[str, Any]:
        target = int(self.example["data"]["target"])
        step_size = int(self.example["data"]["step_size"])
        steps: list[dict[str, Any]] = []
        counter = 0
        history = [0]
        index = 0
        while counter < target:
            counter = min(counter + step_size, target)
            history = history + [counter]
            steps.append(
                {
                    "index": index,
                    "label": f"Advance to {counter}",
                    "annotation": f"The demo increments the counter to {counter}.",
                    "teaching_note": "Phase 1 uses predictable placeholder data only.",
                    "state_patch": {
                        "counter": counter,
                        "history": history,
                        "status": "complete" if counter >= target else "running",
                    },
                }
            )
            index += 1

        return TraceBundle(
            app_type=self.app_type,
            trace_id=f"placeholder-{uuid4().hex[:8]}",
            is_complete=True,
            summary=TraceSummary(step_count=len(steps), result="success"),
            steps=steps,
        ).model_dump()

    def next_incremental_step(self) -> TraceStep | None:
        current = int(self._current_state_data["counter"])
        target = int(self._current_state_data["target"])
        step_size = int(self._current_state_data["step_size"])
        if current >= target:
            return None

        next_value = min(current + step_size, target)
        history = list(self._current_state_data["history"]) + [next_value]
        return TraceStep(
            index=len(self._trace_bundle.steps),
            label=f"Advance to {next_value}",
            annotation=f"The demo increments the counter to {next_value}.",
            teaching_note="Incremental mode computes one step per action.",
            state_patch={
                "counter": next_value,
                "history": history,
                "status": "complete" if next_value >= target else "running",
            },
        )

    def reset_runtime(self) -> None:
        self.current_step = 0
        self._base_state_data = {}
        self._current_state_data = {}
        self._trace_bundle = None
        self._trace_cache_complete = False
        self.ensure_runtime_ready()


def copy_example(name: str) -> dict[str, Any]:
    source = EXAMPLES[name]
    return {
        "title": source["title"],
        "data": dict(source["data"]),
        "options": dict(source["options"]),
    }
