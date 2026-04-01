"""Student-facing API for the CSP map-colouring demo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai9414.core import BaseEducationalApp
from ai9414.core.errors import AI9414Error
from ai9414.csp.examples import build_examples
from ai9414.csp.models import CspConfigModel, CspExample, CspProblem, extend_colour_list
from ai9414.csp.trace import build_csp_trace, build_csp_trace_from_problem


class CSPDemo(BaseEducationalApp):
    """Playback-first CSP demo with curated map-colouring examples and live Python solving."""

    def __init__(
        self,
        *,
        example: str | None = None,
        problem: CspProblem | None = None,
        mode: str = "student",
        execution_mode: str = "precomputed",
    ) -> None:
        if execution_mode != "precomputed":
            raise AI9414Error(
                code="unsupported_action",
                message="CSPDemo currently supports precomputed execution mode only.",
            )
        super().__init__(
            app_type="csp",
            app_title="CSP Demo - Map Colouring",
            execution_mode="precomputed",
            mode=mode,
        )
        self.examples = build_examples()
        self.example: CspExample | None = None
        self.problem: CspProblem | None = None
        self.options: dict[str, Any] = {
            "playback_speed": 1.0,
            "algorithm": "backtracking_forward_checking",
            "variable_ordering": "fixed",
            "value_ordering": "default",
            "num_colours": 3,
            "random_seed": 7,
        }
        if problem is not None:
            self.load_problem(problem)
        else:
            self.load_example(example or "australia")

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
        self.options["num_colours"] = len(self.problem.colours)
        self.reset_runtime()

    def load_problem(self, problem: CspProblem) -> None:
        self.example_name = None
        self.config_name = None
        self.example = None
        self.problem = CspProblem.model_validate(problem.model_dump())
        self.options["num_colours"] = len(self.problem.colours)
        self.reset_runtime()

    def load_map_problem(
        self,
        *,
        regions: list[str],
        adjacency: dict[str, list[str]],
        colours: list[str],
        title: str = "Custom map-colouring CSP",
        subtitle: str = "A custom map loaded from Python.",
    ) -> None:
        self.load_problem(
            CspProblem(
                title=title,
                subtitle=subtitle,
                regions=regions,
                colours=colours,
                neighbours=adjacency,
            )
        )

    def load_config(self, path: str) -> None:
        raw = self.load_base_config(path)
        config = CspConfigModel.model_validate(raw)
        self.example_name = None
        self.config_name = Path(path).name
        self.example = None
        self.problem = config.data.problem
        self.options = {
            "playback_speed": 1.0,
            "algorithm": "backtracking_forward_checking",
            "variable_ordering": "fixed",
            "value_ordering": "default",
            "num_colours": len(self.problem.colours),
            "random_seed": 7,
        }
        self.set_options(**config.options)
        self.reset_runtime()

    def set_algorithm(self, name: str) -> None:
        self.set_options(algorithm=name)

    def set_variable_ordering(self, name: str) -> None:
        self.set_options(variable_ordering=name)

    def set_value_ordering(self, name: str) -> None:
        self.set_options(value_ordering=name)

    def set_num_colours(self, count: int) -> None:
        self.set_options(num_colours=count)

    def set_options(self, **kwargs: Any) -> None:
        allowed = {
            "playback_speed",
            "algorithm",
            "variable_ordering",
            "value_ordering",
            "num_colours",
            "random_seed",
        }
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

        if "algorithm" in kwargs:
            algorithm = str(kwargs["algorithm"])
            if algorithm != "backtracking_forward_checking":
                raise AI9414Error(
                    code="invalid_option_value",
                    message="The only supported CSP algorithm is 'backtracking_forward_checking'.",
                )
            self.options["algorithm"] = algorithm

        if "variable_ordering" in kwargs:
            variable_ordering = str(kwargs["variable_ordering"])
            if variable_ordering not in {"fixed", "first_unassigned", "mrv"}:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="Variable ordering must be 'fixed', 'first_unassigned', or 'mrv'.",
                )
            self.options["variable_ordering"] = variable_ordering

        if "value_ordering" in kwargs:
            value_ordering = str(kwargs["value_ordering"])
            if value_ordering not in {"default", "random"}:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="Value ordering must be 'default' or 'random'.",
                )
            self.options["value_ordering"] = value_ordering

        if "num_colours" in kwargs:
            num_colours = int(kwargs["num_colours"])
            if not 2 <= num_colours <= 4:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="The number of colours must be between 2 and 4.",
                    details={"allowed_range": [2, 4]},
                )
            self.options["num_colours"] = num_colours

        if "random_seed" in kwargs:
            self.options["random_seed"] = int(kwargs["random_seed"])

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
                "algorithm": self.options["algorithm"],
                "variable_ordering": self.options["variable_ordering"],
                "value_ordering": self.options["value_ordering"],
                "num_colours": self.options["num_colours"],
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

    def reset_runtime(self) -> None:
        self.current_step = 0
        self._base_state_data = {}
        self._current_state_data = {}
        self._trace_bundle = None
        self._trace_cache_complete = False
        self.ensure_runtime_ready()

    def _build_bundle(self):
        if self.problem is None:
            raise AI9414Error(code="trace_generation_failed", message="No CSP problem is loaded.")
        configured_problem = self._configured_problem()
        if self.example is not None:
            return build_csp_trace(
                CspExample(
                    title=self.example.title,
                    subtitle=self.example.subtitle,
                    problem=configured_problem,
                ),
                algorithm=self.options["algorithm"],
                variable_ordering=self.options["variable_ordering"],
                value_ordering=self.options["value_ordering"],
                random_seed=self.options["random_seed"],
            )
        return build_csp_trace_from_problem(
            configured_problem,
            title=configured_problem.title,
            subtitle=configured_problem.subtitle,
            algorithm=self.options["algorithm"],
            variable_ordering=self.options["variable_ordering"],
            value_ordering=self.options["value_ordering"],
            random_seed=self.options["random_seed"],
        )

    def _configured_problem(self) -> CspProblem:
        if self.problem is None:
            raise AI9414Error(code="trace_generation_failed", message="No CSP problem is loaded.")
        colour_count = int(self.options["num_colours"])
        colours = extend_colour_list(self.problem.colours, colour_count)
        domains = {region: list(colours) for region in self.problem.regions}
        return CspProblem(
            title=self.problem.title,
            subtitle=self.problem.subtitle,
            regions=list(self.problem.regions),
            colours=colours,
            neighbours=copy_neighbours(self.problem.neighbours),
            domains=domains,
            geometry=self.problem.geometry,
            colour_values=self.problem.colour_values,
        )


def copy_neighbours(neighbours: dict[str, list[str]]) -> dict[str, list[str]]:
    return {region: list(adjacent) for region, adjacent in neighbours.items()}
