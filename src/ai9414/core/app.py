"""Shared abstract app model for ai9414."""

from __future__ import annotations

import copy
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from uuid import uuid4

from ai9414.core.config import load_json_config
from ai9414.core.errors import AI9414Error
from ai9414.core.models import (
    ActionRequest,
    ActionResponse,
    AppManifest,
    Capabilities,
    ExecutionModeLiteral,
    SessionState,
    TraceBundle,
    TraceStep,
    TraceSummary,
)


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


class BaseEducationalApp(ABC):
    """Abstract base class for all ai9414 topic apps."""

    def __init__(
        self,
        *,
        app_type: str,
        app_title: str,
        execution_mode: ExecutionModeLiteral = "precomputed",
        mode: str = "student",
    ) -> None:
        self.app_type = app_type
        self.app_title = app_title
        self.execution_mode = execution_mode
        self.mode = mode
        self.session_id = uuid4().hex
        self.example_name: str | None = None
        self.config_name: str | None = None
        self.options: dict[str, Any] = {}
        self.current_step = 0
        self._base_state_data: dict[str, Any] = {}
        self._current_state_data: dict[str, Any] = {}
        self._trace_bundle: TraceBundle | None = None
        self._trace_cache_complete = False
        self._recent_errors: list[dict[str, Any]] = []

    @abstractmethod
    def load_example(self, name: str) -> None:
        """Load a curated example and reset runtime state."""

    @abstractmethod
    def load_config(self, path: str) -> None:
        """Load an instructor-supplied configuration file."""

    @abstractmethod
    def set_options(self, **kwargs: Any) -> None:
        """Apply stable student-facing options."""

    @abstractmethod
    def build_initial_state(self) -> dict[str, Any]:
        """Build the base state for the current example or config."""

    @abstractmethod
    def build_trace(self) -> dict[str, Any]:
        """Build the complete trace bundle for the current state."""

    def list_examples(self) -> list[str]:
        return []

    def show(self) -> None:
        from ai9414.core.server import launch_app

        launch_app(self)

    def capabilities(self) -> Capabilities:
        return Capabilities()

    def build_manifest(self) -> dict[str, Any]:
        return AppManifest(
            app_type=self.app_type,
            app_title=self.app_title,
            mode=self.mode,
            execution_mode=self.execution_mode,
            capabilities=self.capabilities(),
        ).model_dump()

    def build_state_payload(self) -> dict[str, Any]:
        self.ensure_runtime_ready()
        state = SessionState(
            app_type=self.app_type,
            example_name=self.example_name,
            config_name=self.config_name,
            options=copy.deepcopy(self.options),
            view={"current_step": self.current_step},
            data=copy.deepcopy(self._current_state_data),
        )
        return state.model_dump()

    def get_trace_payload(self) -> dict[str, Any]:
        self.ensure_runtime_ready()
        if self.execution_mode == "precomputed":
            return self._trace_bundle.model_dump()
        return self._trace_bundle.model_dump()

    def get_recent_errors(self) -> dict[str, Any]:
        return {"ok": True, "errors": copy.deepcopy(self._recent_errors)}

    def export_trace(self, path: str | Path) -> Path:
        self.ensure_runtime_ready()
        trace = self._ensure_complete_trace()
        output_path = Path(path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(trace.model_dump(), indent=2), encoding="utf-8")
        return output_path

    def export_solution_bundle(self, path: str | Path) -> Path:
        from importlib import resources

        self.ensure_runtime_ready()
        trace_path = self.export_trace(Path(path) / "trace.json")
        output_dir = trace_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        solution_root = resources.files("ai9414.frontend").joinpath("solution")
        for asset_name in ("index.html", "style.css", "app.js"):
            source = solution_root.joinpath(asset_name)
            destination = output_dir / asset_name
            destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

        student_root = resources.files("ai9414.frontend").joinpath("student")
        assets_dir = output_dir / "student-assets"
        assets_dir.mkdir(exist_ok=True)
        for asset_name in ("style.css",):
            source = student_root.joinpath(asset_name)
            destination = assets_dir / asset_name
            destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

        return output_dir

    def save_state(self, path: str | Path) -> Path:
        output_path = Path(path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self.build_state_payload(), indent=2),
            encoding="utf-8",
        )
        return output_path

    def load_state(self, path: str | Path) -> None:
        state_path = Path(path).expanduser().resolve()
        raw = json.loads(state_path.read_text(encoding="utf-8"))
        self.options = dict(raw.get("options", {}))
        self.current_step = int(raw.get("view", {}).get("current_step", 0))
        self._current_state_data = dict(raw.get("data", {}))

    def ensure_runtime_ready(self) -> None:
        if not self._base_state_data:
            self._base_state_data = copy.deepcopy(self.build_initial_state().get("data", {}))

        if self.execution_mode == "precomputed":
            if self._trace_bundle is None:
                self._trace_bundle = TraceBundle.model_validate(self.build_trace())
                self._trace_bundle.summary = TraceSummary(
                    step_count=len(self._trace_bundle.steps),
                    result=self._trace_bundle.summary.result or "success",
                )
                self._trace_cache_complete = True
            self._current_state_data = self._state_at_index(self.current_step)
            return

        if self._trace_bundle is None:
            self._trace_bundle = TraceBundle(
                app_type=self.app_type,
                trace_id=f"{self.app_type}-{uuid4().hex[:8]}",
                is_complete=False,
                summary=TraceSummary(step_count=0, result="in_progress"),
                steps=[],
            )
            self._current_state_data = copy.deepcopy(self._base_state_data)

    def reset(self) -> None:
        self._base_state_data = copy.deepcopy(self.build_initial_state().get("data", {}))
        self.current_step = 0
        if self.execution_mode == "precomputed":
            self._current_state_data = self._state_at_index(0)
            return
        self._trace_bundle = TraceBundle(
            app_type=self.app_type,
            trace_id=f"{self.app_type}-{uuid4().hex[:8]}",
            is_complete=False,
            summary=TraceSummary(step_count=0, result="in_progress"),
            steps=[],
        )
        self._current_state_data = copy.deepcopy(self._base_state_data)
        self._trace_cache_complete = False

    def next_incremental_step(self) -> TraceStep | None:
        raise AI9414Error(
            code="unsupported_action",
            message="This app does not implement incremental stepping.",
        )

    def complete_incremental_trace(self) -> TraceBundle:
        self.ensure_runtime_ready()
        while not self._trace_bundle.is_complete:
            step = self.next_incremental_step()
            if step is None:
                self._trace_bundle.is_complete = True
                self._trace_bundle.summary.result = "success"
                break
            self._append_incremental_step(step)
        return self._trace_bundle

    def handle_action(self, request_data: dict[str, Any]) -> dict[str, Any]:
        try:
            request = ActionRequest.model_validate(request_data)
            self.ensure_runtime_ready()
            action = request.action
            payload = request.payload

            if action == "reset":
                self.reset()
                return ActionResponse(
                    state=self.build_state_payload(),
                    trace=self.get_trace_payload(),
                    trace_complete=self._trace_bundle.is_complete,
                ).model_dump()

            if action == "rerun":
                self.reset()
                if self.execution_mode == "incremental":
                    self.complete_incremental_trace()
                return ActionResponse(
                    state=self.build_state_payload(),
                    trace=self.get_trace_payload(),
                    trace_complete=self._trace_bundle.is_complete,
                ).model_dump()

            if action == "previous_step":
                self.current_step = max(self.current_step - 1, 0)
                self._current_state_data = self._state_at_index(self.current_step)
                return ActionResponse(state=self.build_state_payload()).model_dump()

            if action == "step_to":
                index = int(payload.get("index", 0))
                if self.execution_mode == "precomputed":
                    max_index = len(self._trace_bundle.steps)
                    self.current_step = max(0, min(index, max_index))
                    self._current_state_data = self._state_at_index(self.current_step)
                    return ActionResponse(state=self.build_state_payload()).model_dump()
                while self.current_step < index and not self._trace_bundle.is_complete:
                    self._perform_incremental_step()
                self.current_step = min(index, len(self._trace_bundle.steps))
                self._current_state_data = self._state_at_index(self.current_step)
                return ActionResponse(
                    state=self.build_state_payload(),
                    trace=self.get_trace_payload(),
                    trace_complete=self._trace_bundle.is_complete,
                ).model_dump()

            if action == "next_step":
                if self.execution_mode == "precomputed":
                    self.current_step = min(self.current_step + 1, len(self._trace_bundle.steps))
                    self._current_state_data = self._state_at_index(self.current_step)
                    return ActionResponse(state=self.build_state_payload()).model_dump()
                new_step = self._perform_incremental_step()
                self._current_state_data = self._state_at_index(self.current_step)
                return ActionResponse(
                    state=self.build_state_payload(),
                    new_step=new_step.model_dump() if new_step else None,
                    trace_complete=self._trace_bundle.is_complete,
                ).model_dump()

            if action == "set_option":
                self.set_options(**payload)
                self.reset()
                return ActionResponse(
                    state=self.build_state_payload(),
                    trace=self.get_trace_payload(),
                    trace_complete=self._trace_bundle.is_complete,
                ).model_dump()

            if action == "load_example":
                name = payload.get("name")
                if not isinstance(name, str):
                    raise AI9414Error(
                        code="invalid_action_payload",
                        message="Action 'load_example' requires a string payload field 'name'.",
                    )
                self.load_example(name)
                self.ensure_runtime_ready()
                return ActionResponse(
                    state=self.build_state_payload(),
                    trace=self.get_trace_payload(),
                    trace_complete=self._trace_bundle.is_complete,
                ).model_dump()

            if action == "load_config":
                path = payload.get("path")
                if not isinstance(path, str):
                    raise AI9414Error(
                        code="invalid_action_payload",
                        message="Action 'load_config' requires a string payload field 'path'.",
                    )
                self.load_config(path)
                self.ensure_runtime_ready()
                return ActionResponse(
                    state=self.build_state_payload(),
                    trace=self.get_trace_payload(),
                    trace_complete=self._trace_bundle.is_complete,
                ).model_dump()

            raise AI9414Error(
                code="unsupported_action",
                message=f"Action '{action}' is not supported.",
            )
        except AI9414Error as exc:
            self._record_error(exc)
            return exc.to_payload()
        except Exception as exc:  # pragma: no cover - defensive guard
            wrapped = AI9414Error(
                code="trace_generation_failed",
                message=str(exc),
                details={"exception_type": type(exc).__name__},
            )
            self._record_error(wrapped)
            return wrapped.to_payload()

    def _perform_incremental_step(self) -> TraceStep | None:
        step = self.next_incremental_step()
        if step is None:
            self._trace_bundle.is_complete = True
            self._trace_bundle.summary.result = "success"
            return None
        self._append_incremental_step(step)
        return step

    def _append_incremental_step(self, step: TraceStep) -> None:
        self._trace_bundle.steps.append(step)
        self._trace_bundle.summary.step_count = len(self._trace_bundle.steps)
        self.current_step = len(self._trace_bundle.steps)
        self._current_state_data = _deep_merge(
            copy.deepcopy(self._current_state_data),
            step.state_patch,
        )

    def _ensure_complete_trace(self) -> TraceBundle:
        self.ensure_runtime_ready()
        if self.execution_mode == "precomputed":
            return self._trace_bundle
        return self.complete_incremental_trace()

    def _state_at_index(self, index: int) -> dict[str, Any]:
        state = copy.deepcopy(self._base_state_data)
        for step in self._trace_bundle.steps[:index]:
            _deep_merge(state, step.state_patch)
        return state

    def _record_error(self, error: AI9414Error) -> None:
        payload = error.to_payload()["error"]
        self._recent_errors.append(payload)
        self._recent_errors = self._recent_errors[-10:]

    def load_base_config(self, path: str | Path) -> dict[str, Any]:
        config = load_json_config(path)
        if config.app_type != self.app_type:
            raise AI9414Error(
                code="invalid_configuration_file",
                message=(
                    f"Configuration file '{Path(path).name}' targets app type '{config.app_type}', "
                    f"not '{self.app_type}'."
                ),
                details={"expected_app_type": self.app_type, "actual_app_type": config.app_type},
            )
        return config.model_dump()
