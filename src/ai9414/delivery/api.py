"""Student-facing delivery DFS demo API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai9414.core import BaseEducationalApp
from ai9414.core.errors import AI9414Error
from ai9414.delivery.examples import build_examples
from ai9414.delivery.models import DeliveryConfigModel, DeliveryExample
from ai9414.delivery.solver import ACTION_ORDER_LABELS
from ai9414.delivery.trace import build_delivery_trace, build_delivery_trace_from_definition
from ai9414.labyrinth.models import LabyrinthDefinition


class DeliveryDemo(BaseEducationalApp):
    """Playback-first delivery DFS demo with fixed office layouts."""

    def __init__(self, *, mode: str = "student", execution_mode: str = "precomputed") -> None:
        if execution_mode != "precomputed":
            raise AI9414Error(
                code="unsupported_action",
                message="DeliveryDemo currently supports precomputed execution mode only.",
            )
        super().__init__(
            app_type="delivery",
            app_title="Search Demo - Delivery DFS",
            execution_mode="precomputed",
            mode=mode,
        )
        self.examples = build_examples()
        self.example: DeliveryExample | None = self.examples["four_rooms"]
        self.labyrinth: LabyrinthDefinition = self.example.labyrinth
        self.options = {"playback_speed": 1.0, "action_order": "straight_left_right", "random_seed": 7}
        self.load_example("four_rooms")

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
        self.labyrinth = self.example.labyrinth
        self.reset_runtime()

    def load_config(self, path: str) -> None:
        raw = self.load_base_config(path)
        config = DeliveryConfigModel.model_validate(raw)
        self.example_name = None
        self.config_name = Path(path).name
        self.example = None
        self.labyrinth = config.data.labyrinth
        self.options = {"playback_speed": 1.0, "action_order": "straight_left_right", "random_seed": 7}
        self.set_options(**config.options)
        self.reset_runtime()

    def set_options(self, **kwargs: Any) -> None:
        allowed = {"playback_speed", "action_order", "random_seed"}
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
        if "action_order" in kwargs:
            action_order = str(kwargs["action_order"])
            if action_order not in ACTION_ORDER_LABELS:
                raise AI9414Error(
                    code="invalid_option_value",
                    message=(
                        "Action order must be 'straight_left_right', "
                        "'straight_right_left', or 'random'."
                    ),
                    details={"allowed_values": sorted(ACTION_ORDER_LABELS)},
                )
            self.options["action_order"] = action_order
            self.reset_runtime()
        if "random_seed" in kwargs:
            self.options["random_seed"] = int(kwargs["random_seed"])
            self.reset_runtime()

    def build_initial_state(self) -> dict[str, Any]:
        bundle = self._build_bundle()
        self._trace_bundle = bundle
        data = {
            **bundle.initial_state,
            "playback_speed": self.options["playback_speed"],
            "live_python": {
                "backend_url": "http://127.0.0.1:9414/solve",
            },
            "options": {
                "action_order": self.options["action_order"],
                "random_seed": self.options["random_seed"],
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

    def handle_app_command(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        _ = payload
        raise AI9414Error(
            code="unsupported_action",
            message=f"Delivery command '{command}' is not supported.",
        )

    def _build_bundle(self):
        if self.example is None:
            return build_delivery_trace_from_definition(
                self.labyrinth,
                title="Instructor-supplied delivery office",
                subtitle="A fixed office layout for DFS reachability.",
                goal_type="target",
                action_order=self.options["action_order"],
                random_seed=self.options["random_seed"],
            )
        return build_delivery_trace(
            self.example,
            action_order=self.options["action_order"],
            random_seed=self.options["random_seed"],
        )

    def reset_runtime(self) -> None:
        self.current_step = 0
        self._base_state_data = {}
        self._current_state_data = {}
        self._trace_bundle = None
        self._trace_cache_complete = False
        self.ensure_runtime_ready()
