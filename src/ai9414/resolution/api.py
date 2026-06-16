"""Student-facing API for the visual resolution/refutation demo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai9414.core import BaseEducationalApp
from ai9414.core.errors import AI9414Error
from ai9414.core.models import ActionResponse
from ai9414.resolution.examples import build_examples
from ai9414.resolution.models import (
    ResolutionConfigModel,
    ResolutionExample,
    ResolutionProblem,
    ResolutionProofStep,
)
from ai9414.resolution.trace import build_resolution_trace, build_resolution_trace_from_problem


class ResolutionDemo(BaseEducationalApp):
    """Playback-first visual demo for propositional resolution refutation proofs."""

    def __init__(
        self,
        *,
        example: str | None = None,
        ui_mode: str = "student",
        execution_mode: str = "precomputed",
    ) -> None:
        if execution_mode != "precomputed":
            raise AI9414Error(
                code="unsupported_action",
                message="ResolutionDemo currently supports precomputed execution mode only.",
            )
        super().__init__(
            app_type="resolution",
            app_title="Logic Demo - Resolution Refutation",
            execution_mode="precomputed",
            mode=ui_mode,
        )
        self.examples = build_examples()
        self.options: dict[str, Any] = {"playback_speed": 1.0}
        self.example: ResolutionExample | None = None
        self.problem: ResolutionProblem | None = None
        self.load_example(example or "chain_refutation")

    def list_examples(self) -> list[str]:
        return list(self.examples)

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

    def load_config(self, path: str) -> None:
        raw = self.load_base_config(path)
        config = ResolutionConfigModel.model_validate(raw)
        self.example_name = None
        self.config_name = Path(path).name
        self.example = None
        self.options = {"playback_speed": 1.0}
        self.set_options(**config.options)
        self.problem = ResolutionProblem(
            title=config.data.title,
            subtitle=config.data.subtitle,
            clauses=config.data.clauses,
            steps=config.data.steps,
            query=config.data.query,
            entailment_target=config.data.entailment_target,
        )
        self.reset_runtime()

    def load_proof_attempt(
        self,
        clauses: list[list[str]],
        steps: list[dict[str, Any] | ResolutionProofStep],
        *,
        title: str = "Custom resolution proof",
        subtitle: str = "A custom refutation attempt loaded from Python.",
        query: str | None = None,
        entailment_target: str | None = None,
    ) -> None:
        proof_steps = [
            item if isinstance(item, ResolutionProofStep) else ResolutionProofStep.model_validate(item)
            for item in steps
        ]
        self.example_name = None
        self.config_name = None
        self.example = None
        self.problem = ResolutionProblem(
            title=title,
            subtitle=subtitle,
            clauses=clauses,
            steps=proof_steps,
            query=query,
            entailment_target=entailment_target,
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
            playback_speed = float(kwargs["playback_speed"])
            if not 0.5 <= playback_speed <= 5.0:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="Playback speed must be between 0.5 and 5.0.",
                    details={"allowed_range": [0.5, 5.0]},
                )
            self.options["playback_speed"] = playback_speed

    def build_initial_state(self) -> dict[str, Any]:
        bundle = self._build_bundle()
        self._trace_bundle = bundle
        data = {
            **bundle.initial_state,
            "playback_speed": self.options["playback_speed"],
            "options": dict(self.options),
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
        if command != "load_resolution_attempt":
            raise AI9414Error(
                code="unsupported_action",
                message=f"App command '{command}' is not supported by {self.app_type}.",
            )
        clauses = payload.get("clauses")
        steps = payload.get("steps")
        if isinstance(clauses, str):
            clauses = _parse_clause_lines(clauses)
        if isinstance(steps, str):
            steps = _parse_step_lines(steps)
        if not isinstance(clauses, list) or not isinstance(steps, list):
            raise AI9414Error(
                code="invalid_action_payload",
                message="Custom resolution attempts require clauses and steps.",
            )
        self.load_proof_attempt(
            clauses=clauses,
            steps=steps,
            title=str(payload.get("title") or "Custom resolution proof"),
            subtitle=str(payload.get("subtitle") or "A proof attempt entered in the browser."),
            query=payload.get("query") if isinstance(payload.get("query"), str) else None,
            entailment_target=(
                payload.get("entailment_target")
                if isinstance(payload.get("entailment_target"), str)
                else None
            ),
        )
        self.ensure_runtime_ready()
        return ActionResponse(
            state=self.build_state_payload(),
            trace=self.get_trace_payload(),
            trace_complete=True,
        ).model_dump()

    def reset_runtime(self) -> None:
        self.current_step = 0
        self._base_state_data = {}
        self._current_state_data = {}
        self._trace_bundle = None
        self._trace_cache_complete = False
        self.ensure_runtime_ready()

    def _build_bundle(self):
        if self.problem is None:
            raise AI9414Error(code="trace_generation_failed", message="No resolution problem is loaded.")
        if self.example is not None:
            return build_resolution_trace(self.example)
        return build_resolution_trace_from_problem(self.problem)


def _parse_clause_lines(text: str) -> list[list[str]]:
    clauses: list[list[str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for separator in ("<=", "=>", "->"):
            line = line.replace(separator, " ")
        line = line.replace("∨", "|").replace(" v ", "|").replace(" or ", "|").replace(",", "|")
        literals = [part.strip() for part in line.split("|") if part.strip()]
        if not literals:
            continue
        clauses.append(literals)
    if not clauses:
        raise AI9414Error(
            code="invalid_action_payload",
            message="Enter at least one clause.",
        )
    return clauses


def _parse_step_lines(text: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        line = line.replace("C", "").replace("c", "")
        parts = [part.strip() for part in line.replace(";", ",").split(",") if part.strip()]
        if len(parts) != 3:
            raise AI9414Error(
                code="invalid_action_payload",
                message="Each proof step must have three fields: left clause, right clause, pivot.",
                details={"bad_line": raw_line},
            )
        steps.append({"left": int(parts[0]), "right": int(parts[1]), "pivot": parts[2]})
    return steps
