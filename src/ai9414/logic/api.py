"""Student-facing API for the visual DPLL demo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai9414.core import BaseEducationalApp
from ai9414.core.errors import AI9414Error
from ai9414.logic.examples import build_examples
from ai9414.logic.models import LogicConfigModel, LogicExample, LogicProblem, VariableOrder
from ai9414.logic.parser import (
    extract_variables_from_clauses,
    formula_to_cnf_clauses,
    negate_formula_to_cnf_clauses,
)
from ai9414.logic.trace import build_logic_trace, build_logic_trace_from_problem


class DpllDemo(BaseEducationalApp):
    """Playback-first DPLL demo with curated examples and small Python-backed workflows."""

    def __init__(
        self,
        *,
        example: str | None = None,
        mode: str = "sat",
        ui_mode: str = "student",
        execution_mode: str = "precomputed",
    ) -> None:
        if execution_mode != "precomputed":
            raise AI9414Error(
                code="unsupported_action",
                message="DpllDemo currently supports precomputed execution mode only.",
            )
        super().__init__(
            app_type="logic",
            app_title="Logic Demo - Visual DPLL",
            execution_mode="precomputed",
            mode=ui_mode,
        )
        self.examples = build_examples()
        self.options: dict[str, Any] = {
            "playback_speed": 1.0,
            "unit_propagation": True,
            "pure_literals": False,
            "variable_order": "alphabetical",
            "problem_mode": mode,
        }
        self.example: LogicExample | None = None
        self.problem: LogicProblem | None = None
        default_example = example or self._first_example_for_mode(mode)
        self.load_example(default_example)

    def list_examples(self) -> list[str]:
        mode = self.options.get("problem_mode", "sat")
        return [
            name
            for name, example in self.examples.items()
            if example.problem.mode == mode
        ]

    def load_example(self, name: str) -> None:
        if name not in self.examples:
            raise AI9414Error(
                code="example_not_found",
                message=f"Example '{name}' was not found.",
                details={"available_examples": sorted(self.examples)},
            )
        example = self.examples[name]
        self.options["problem_mode"] = example.problem.mode
        self.example_name = name
        self.config_name = None
        self.example = example
        self.problem = example.problem
        self.reset_runtime()

    def load_config(self, path: str) -> None:
        raw = self.load_base_config(path)
        config = LogicConfigModel.model_validate(raw)
        self.example_name = None
        self.config_name = Path(path).name
        self.example = None
        self.options = {
            "playback_speed": 1.0,
            "unit_propagation": True,
            "pure_literals": False,
            "variable_order": "alphabetical",
            "problem_mode": config.data.mode,
        }
        self.set_options(**config.options)
        if config.data.mode == "sat":
            assert config.data.clauses is not None
            self.problem = LogicProblem(
                mode="sat",
                title=config.data.title,
                subtitle=config.data.subtitle,
                clauses=config.data.clauses,
            )
        else:
            self.problem = self._build_entailment_problem(
                title=config.data.title,
                subtitle=config.data.subtitle,
                formulas=config.data.kb_formulas,
                query=config.data.query or "",
            )
        self.reset_runtime()

    def load_cnf(self, clauses: list[list[str]], *, title: str = "Custom CNF", subtitle: str = "") -> None:
        self.example_name = None
        self.config_name = None
        self.example = None
        self.options["problem_mode"] = "sat"
        self.problem = LogicProblem(
            mode="sat",
            title=title,
            subtitle=subtitle or "A custom CNF loaded from Python.",
            clauses=clauses,
        )
        self.reset_runtime()

    def load_kb(
        self,
        *,
        formulas: list[str],
        query: str,
        title: str = "Custom entailment problem",
        subtitle: str = "",
    ) -> None:
        self.example_name = None
        self.config_name = None
        self.example = None
        self.options["problem_mode"] = "entailment"
        self.problem = self._build_entailment_problem(
            title=title,
            subtitle=subtitle or "A custom knowledge base loaded from Python.",
            formulas=formulas,
            query=query,
        )
        self.reset_runtime()

    def set_options(self, **kwargs: Any) -> None:
        allowed = {"playback_speed", "unit_propagation", "pure_literals", "variable_order", "problem_mode"}
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

        if "unit_propagation" in kwargs:
            self.options["unit_propagation"] = bool(kwargs["unit_propagation"])

        if "pure_literals" in kwargs:
            self.options["pure_literals"] = bool(kwargs["pure_literals"])

        if "variable_order" in kwargs:
            variable_order = str(kwargs["variable_order"])
            if variable_order not in {"alphabetical", "appearance"}:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="Variable order must be 'alphabetical' or 'appearance'.",
                )
            self.options["variable_order"] = variable_order

        if "problem_mode" in kwargs:
            problem_mode = str(kwargs["problem_mode"])
            if problem_mode not in {"sat", "entailment"}:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="Problem mode must be 'sat' or 'entailment'.",
                )
            self.options["problem_mode"] = problem_mode
            if self.problem is None or self.problem.mode != problem_mode or self.example_name is not None:
                self.load_example(self._first_example_for_mode(problem_mode))

    def set_speed(self, speed: float) -> None:
        self.set_options(playback_speed=speed)

    def build_initial_state(self) -> dict[str, Any]:
        bundle = self._build_bundle()
        self._trace_bundle = bundle
        data = {
            **bundle.initial_state,
            "logic_problem": self.problem.model_dump() if self.problem is not None else None,
            "playback_speed": self.options["playback_speed"],
            "live_python": {
                "backend_url": "http://127.0.0.1:9414/solve",
            },
            "options": {
                "unit_propagation": self.options["unit_propagation"],
                "pure_literals": self.options["pure_literals"],
                "variable_order": self.options["variable_order"],
                "problem_mode": self.options["problem_mode"],
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
            raise AI9414Error(code="trace_generation_failed", message="No logic problem is loaded.")
        if self.example is not None:
            return build_logic_trace(
                self.example,
                unit_propagation=self.options["unit_propagation"],
                pure_literals=self.options["pure_literals"],
                variable_order=self.options["variable_order"],
            )
        return build_logic_trace_from_problem(
            self.problem,
            title=self.problem.title,
            subtitle=self.problem.subtitle,
            unit_propagation=self.options["unit_propagation"],
            pure_literals=self.options["pure_literals"],
            variable_order=self.options["variable_order"],
        )

    def _first_example_for_mode(self, mode: str) -> str:
        for name, example in self.examples.items():
            if example.problem.mode == mode:
                return name
        raise AI9414Error(code="example_not_found", message=f"No examples are available for mode '{mode}'.")

    def _build_entailment_problem(
        self,
        *,
        title: str,
        subtitle: str,
        formulas: list[str],
        query: str,
    ) -> LogicProblem:
        clauses: list[list[str]] = []
        for formula in formulas:
            clauses.extend(formula_to_cnf_clauses(formula))
        clauses.extend(negate_formula_to_cnf_clauses(query))
        return LogicProblem(
            mode="entailment",
            title=title,
            subtitle=subtitle,
            clauses=clauses,
            variables=extract_variables_from_clauses(clauses),
            kb_formulas=formulas,
            query=query,
            entailment_target=f"KB and not ({query})",
            original_input=list(formulas) + [f"query: {query}"],
        )
