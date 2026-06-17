"""Student-facing API for the Week 7 Bayes-filter corridor demo."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from ai9414.core import BaseEducationalApp
from ai9414.core.errors import AI9414Error
from ai9414.uncertainty.examples import build_examples, build_exercises, make_problem, to_zero_based_landmarks
from ai9414.uncertainty.models import CorridorProblem, MotionModel, SensorModel, UncertaintyConfigModel, UncertaintyExample
from ai9414.uncertainty.trace import (
    build_uncertainty_trace_from_problem,
    final_runtime_state,
    motion_entries,
)


class BayesFilterDemo(BaseEducationalApp):
    """Interactive corridor localisation demo for reasoning with uncertainty."""

    def __init__(
        self,
        *,
        example: str | None = None,
        problem: CorridorProblem | None = None,
        cells: int = 10,
        landmarks: dict[str, list[int]] | None = None,
        initial_belief: str | list[float] = "uniform",
        true_position: int | None = 6,
        sensor_hit: float = 0.8,
        sensor_false_alarm: float = 0.2,
        motion_success: float = 0.8,
        motion_stay: float = 0.1,
        motion_overshoot: float = 0.1,
        show_true_position: bool | None = None,
        mode: str = "demo",
        execution_mode: str = "precomputed",
    ) -> None:
        if execution_mode != "precomputed":
            raise AI9414Error(
                code="unsupported_action",
                message="BayesFilterDemo currently supports precomputed execution mode only.",
            )
        default_show_true = mode != "exercise" if show_true_position is None else show_true_position
        super().__init__(
            app_type="uncertainty",
            app_title="Bayes Filter Corridor",
            execution_mode="precomputed",
            mode=mode,
        )
        self.examples = build_examples()
        self.exercises = build_exercises()
        self.current_example: UncertaintyExample | None = None
        self.problem: CorridorProblem | None = None
        self.events: list[dict[str, Any]] = []
        self.options: dict[str, Any] = {"playback_speed": 1.0}
        self._rng = random.Random(7)

        if problem is not None:
            self.load_problem(problem)
        elif example is not None:
            self.load_example(example)
        else:
            belief = (
                [1.0 / cells for _ in range(cells)]
                if initial_belief == "uniform"
                else [float(value) for value in initial_belief]
            )
            self.load_problem(
                make_problem(
                    cells=cells,
                    landmarks=landmarks or {"door": [2, 6]},
                    initial_belief=belief,
                    true_position=true_position,
                    sensor_hit=sensor_hit,
                    sensor_false_alarm=sensor_false_alarm,
                    motion_success=motion_success,
                    motion_stay=motion_stay,
                    motion_overshoot=motion_overshoot,
                    show_true_position=default_show_true,
                )
            )
            self.example_name = None

    @classmethod
    def example(cls, name: str) -> "BayesFilterDemo":
        return cls(example=name)

    @classmethod
    def exercise(cls, name: str = "sensor_update") -> "BayesFilterDemo":
        app = cls(mode="exercise", show_true_position=False)
        app.load_exercise(name)
        return app

    def list_examples(self) -> list[str]:
        return list(self.examples.keys())

    def list_exercises(self) -> list[str]:
        return list(self.exercises.keys())

    def load_example(self, name: str) -> None:
        if name not in self.examples:
            raise AI9414Error(
                code="example_not_found",
                message=f"Example '{name}' was not found.",
                details={"available_examples": self.list_examples()},
            )
        self.example_name = name
        self.config_name = None
        self.current_example = self.examples[name]
        self.problem = CorridorProblem.model_validate(self.current_example.problem.model_dump())
        self.events = []
        self._rng = random.Random(self.problem.random_seed)
        self.reset_runtime()

    def load_exercise(self, name: str) -> None:
        if name not in self.exercises:
            raise AI9414Error(
                code="example_not_found",
                message=f"Exercise '{name}' was not found.",
                details={"available_exercises": self.list_exercises()},
            )
        self.example_name = name
        self.config_name = None
        self.current_example = self.exercises[name]
        self.problem = CorridorProblem.model_validate(self.current_example.problem.model_dump())
        self.events = []
        self._rng = random.Random(self.problem.random_seed)
        self.reset_runtime()

    def load_problem(self, problem: CorridorProblem) -> None:
        self.example_name = None
        self.config_name = None
        self.current_example = None
        self.problem = CorridorProblem.model_validate(problem.model_dump())
        self.events = []
        self._rng = random.Random(self.problem.random_seed)
        self.reset_runtime()

    def load_config(self, path: str) -> None:
        raw = self.load_base_config(path)
        config = UncertaintyConfigModel.model_validate(raw)
        self.example_name = None
        self.config_name = Path(path).name
        self.current_example = None
        self.problem = CorridorProblem.model_validate(config.data.problem.model_dump())
        self.options = {"playback_speed": 1.0}
        self.set_options(**config.options)
        self.events = []
        self._rng = random.Random(self.problem.random_seed)
        self.reset_runtime()

    def configure_corridor(
        self,
        *,
        cells: int,
        landmarks: dict[str, list[int]],
        initial_belief: str | list[float] = "uniform",
        true_position: int | None = None,
    ) -> None:
        belief = (
            [1.0 / cells for _ in range(cells)]
            if initial_belief == "uniform"
            else [float(value) for value in initial_belief]
        )
        self.load_problem(
            make_problem(
                cells=cells,
                landmarks=landmarks,
                initial_belief=belief,
                true_position=true_position,
                sensor_hit=self.problem.sensor_model.hit if self.problem else 0.8,
                sensor_false_alarm=self.problem.sensor_model.false_alarm if self.problem else 0.2,
                motion_success=self.problem.motion_model.success if self.problem else 0.8,
                motion_stay=self.problem.motion_model.stay if self.problem else 0.1,
                motion_overshoot=self.problem.motion_model.overshoot if self.problem else 0.1,
                show_true_position=self.problem.show_true_position if self.problem else True,
            )
        )

    def set_options(self, **kwargs: Any) -> None:
        allowed = {
            "playback_speed",
            "sensor_hit",
            "sensor_false_alarm",
            "motion_success",
            "motion_stay",
            "motion_overshoot",
            "show_true_position",
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

        if self.problem is None:
            return

        problem_patch: dict[str, Any] = {}
        if "sensor_hit" in kwargs or "sensor_false_alarm" in kwargs:
            problem_patch["sensor_model"] = SensorModel(
                hit=float(kwargs.get("sensor_hit", self.problem.sensor_model.hit)),
                false_alarm=float(kwargs.get("sensor_false_alarm", self.problem.sensor_model.false_alarm)),
            )
        if {"motion_success", "motion_stay", "motion_overshoot"} & set(kwargs):
            problem_patch["motion_model"] = normalised_motion_model(
                success=float(kwargs.get("motion_success", self.problem.motion_model.success)),
                stay=float(kwargs.get("motion_stay", self.problem.motion_model.stay)),
                overshoot=float(kwargs.get("motion_overshoot", self.problem.motion_model.overshoot)),
            )
        if "show_true_position" in kwargs:
            problem_patch["show_true_position"] = bool(kwargs["show_true_position"])
        if problem_patch:
            self.problem = self.problem.model_copy(update=problem_patch)
            self.reset_runtime()

    def build_initial_state(self) -> dict[str, Any]:
        if self.problem is None:
            raise AI9414Error(code="trace_generation_failed", message="No corridor problem is loaded.")
        bundle = build_uncertainty_trace_from_problem(
            self.problem,
            title=self._title(),
            subtitle=self._subtitle(),
            events=[],
        )
        data = {
            **bundle.initial_state,
            "playback_speed": self.options["playback_speed"],
            "options": {
                "playback_speed": self.options["playback_speed"],
                "sensor_hit": self.problem.sensor_model.hit,
                "sensor_false_alarm": self.problem.sensor_model.false_alarm,
                "motion_success": self.problem.motion_model.success,
                "motion_stay": self.problem.motion_model.stay,
                "motion_overshoot": self.problem.motion_model.overshoot,
                "show_true_position": self.problem.show_true_position,
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
        if self.problem is None:
            raise AI9414Error(code="trace_generation_failed", message="No corridor problem is loaded.")
        return build_uncertainty_trace_from_problem(
            self.problem,
            title=self._title(),
            subtitle=self._subtitle(),
            events=self.events,
            trace_id="uncertainty-custom",
        ).model_dump()

    def handle_app_command(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.problem is None:
            raise AI9414Error(code="trace_generation_failed", message="No corridor problem is loaded.")

        message = ""
        if command == "sense":
            landmark = str(payload.get("landmark") or self._default_landmark())
            present = bool(payload.get("present", True))
            self._append_event(
                {
                    "kind": "sense",
                    "landmark": landmark,
                    "present": present,
                    "sensor_model": self.problem.sensor_model.model_dump(),
                    "motion_model": self.problem.motion_model.model_dump(),
                }
            )
        elif command == "move":
            direction = str(payload.get("direction") or "right").lower()
            current_belief, current_true = final_runtime_state(self.problem, self.events)
            _ = current_belief
            true_after = self._sample_true_motion(current_true, direction)
            self._append_event(
                {
                    "kind": "move",
                    "direction": direction,
                    "true_position": true_after,
                    "sensor_model": self.problem.sensor_model.model_dump(),
                    "motion_model": self.problem.motion_model.model_dump(),
                }
            )
        elif command == "move_and_sense":
            direction = str(payload.get("direction") or "right").lower()
            if direction not in {"left", "right"}:
                raise AI9414Error(
                    code="invalid_action_payload",
                    message="Combined move-and-sense shortcuts support 'left' and 'right' only.",
                )
            landmark = str(payload.get("landmark") or "door")
            _, current_true = final_runtime_state(self.problem, self.events)
            true_after = self._sample_true_motion(current_true, direction)
            move_event = {
                "kind": "move",
                "direction": direction,
                "true_position": true_after,
                "sensor_model": self.problem.sensor_model.model_dump(),
                "motion_model": self.problem.motion_model.model_dump(),
            }
            moved_belief, moved_true = final_runtime_state(self.problem, [*self.events, move_event])
            present = self._sample_sensor_reading(moved_true, landmark, belief=moved_belief)
            sense_event = {
                "kind": "sense",
                "landmark": landmark,
                "present": present,
                "sensor_model": self.problem.sensor_model.model_dump(),
                "motion_model": self.problem.motion_model.model_dump(),
            }
            self.events.extend([move_event, sense_event])
            self.reset_runtime()
            reading = self._format_sensor_reading(landmark, present)
            message = (
                f"Moved {direction}, then sampled the {self._format_landmark(landmark)} sensor: "
                f"{reading}. Use Previous to inspect the motion prediction step."
            )
        elif command == "reset_belief":
            self._append_event(
                {
                    "kind": "reset_belief",
                    "sensor_model": self.problem.sensor_model.model_dump(),
                    "motion_model": self.problem.motion_model.model_dump(),
                }
            )
        elif command == "reset_true_position":
            self._append_event(
                {
                    "kind": "reset_true_position",
                    "true_position": self.problem.initial_true_position,
                    "sensor_model": self.problem.sensor_model.model_dump(),
                    "motion_model": self.problem.motion_model.model_dump(),
                }
            )
        elif command == "randomise_true_position":
            self._append_event(
                {
                    "kind": "randomise_true_position",
                    "true_position": self._rng.randrange(self.problem.cells),
                    "sensor_model": self.problem.sensor_model.model_dump(),
                    "motion_model": self.problem.motion_model.model_dump(),
                }
            )
        elif command == "reset_all":
            self.events = []
            self.reset_runtime()
        elif command == "randomise_corridor":
            self._randomise_corridor()
        elif command == "set_sensor_model":
            sensor = SensorModel(
                hit=float(payload.get("hit", self.problem.sensor_model.hit)),
                false_alarm=float(payload.get("false_alarm", self.problem.sensor_model.false_alarm)),
            )
            self.problem = self.problem.model_copy(update={"sensor_model": sensor})
            self._append_event(
                {
                    "kind": "set_sensor_model",
                    "sensor_model": sensor.model_dump(),
                    "motion_model": self.problem.motion_model.model_dump(),
                }
            )
        elif command == "set_motion_model":
            motion = normalised_motion_model(
                success=float(payload.get("success", self.problem.motion_model.success)),
                stay=float(payload.get("stay", self.problem.motion_model.stay)),
                overshoot=float(payload.get("overshoot", self.problem.motion_model.overshoot)),
            )
            self.problem = self.problem.model_copy(update={"motion_model": motion})
            self._append_event(
                {
                    "kind": "set_motion_model",
                    "sensor_model": self.problem.sensor_model.model_dump(),
                    "motion_model": motion.model_dump(),
                }
            )
        else:
            raise AI9414Error(
                code="unsupported_action",
                message=f"Uncertainty command '{command}' is not supported.",
            )

        self.ensure_runtime_ready()
        return {
            "ok": True,
            "state": self.build_state_payload(),
            "trace": self.get_trace_payload(),
            "trace_complete": True,
            "message": message,
        }

    def write_stub(self, path: str | Path = "week7_bayes_filter_stub.py") -> Path:
        output_path = Path(path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(WEEK7_BAYES_FILTER_STUB, encoding="utf-8")
        return output_path

    def reset_runtime(self) -> None:
        self.current_step = len(self.events)
        self._base_state_data = {}
        self._current_state_data = {}
        self._trace_bundle = None
        self._trace_cache_complete = False
        self.ensure_runtime_ready()

    def _append_event(self, event: dict[str, Any]) -> None:
        self.events.append(event)
        self.reset_runtime()

    def _title(self) -> str:
        return self.current_example.title if self.current_example else self.problem.title

    def _subtitle(self) -> str:
        return self.current_example.subtitle if self.current_example else self.problem.subtitle

    def _default_landmark(self) -> str:
        if not self.problem or not self.problem.landmark_types:
            return "door"
        return self.problem.landmark_types[0]

    def _sample_true_motion(self, true_position: int | None, direction: str) -> int | None:
        if true_position is None:
            return None
        entries = motion_entries(true_position, self.problem.motion_model, direction, self.problem.cells)
        draw = self._rng.random()
        cumulative = 0.0
        for entry in entries:
            cumulative += float(entry["probability"])
            if draw <= cumulative:
                return int(entry["destination_index"])
        return int(entries[-1]["destination_index"])

    def _sample_sensor_reading(self, true_position: int | None, landmark: str, *, belief: list[float]) -> bool:
        sampled_position = true_position
        if sampled_position is None:
            sampled_position = self._sample_position_from_belief(belief)
        landmark_cells = set(self.problem.landmarks.get(landmark, []))
        has_landmark = sampled_position in landmark_cells
        probability_present = self.problem.sensor_model.hit if has_landmark else self.problem.sensor_model.false_alarm
        return self._rng.random() <= probability_present

    def _sample_position_from_belief(self, belief: list[float]) -> int:
        draw = self._rng.random()
        cumulative = 0.0
        for index, probability in enumerate(belief):
            cumulative += float(probability)
            if draw <= cumulative:
                return index
        return len(belief) - 1

    def _format_landmark(self, landmark: str) -> str:
        return str(landmark).replace("_", " ")

    def _format_sensor_reading(self, landmark: str, present: bool) -> str:
        label = self._format_landmark(landmark)
        return f"sensed {label}" if present else f"sensed no {label}"

    def _randomise_corridor(self) -> None:
        cells = self.problem.cells if self.problem else 10
        count = 2 if cells < 12 else 3
        door_cells = sorted(self._rng.sample(range(1, cells + 1), count))
        extra = sorted(self._rng.sample([cell for cell in range(1, cells + 1) if cell not in door_cells], 1))
        self.problem = self.problem.model_copy(
            update={
                "landmarks": to_zero_based_landmarks({"door": door_cells, "sign": extra}, cells),
                "initial_true_position": self._rng.randrange(cells),
            }
        )
        self.events = []
        self.reset_runtime()


def normalised_motion_model(*, success: float, stay: float, overshoot: float) -> MotionModel:
    values = [max(0.0, float(success)), max(0.0, float(stay)), max(0.0, float(overshoot))]
    total = sum(values)
    if total <= 0.0:
        raise AI9414Error(
            code="invalid_option_value",
            message="At least one motion probability must be positive.",
        )
    return MotionModel(success=values[0] / total, stay=values[1] / total, overshoot=values[2] / total)


WEEK7_BAYES_FILTER_STUB = '''"""
Week 7: Reasoning with uncertainty
Bayes filter corridor exercise

This file asks you to implement the two main operations used by a simple
Bayes filter:

1. sensor_update:
   Use noisy evidence to update a belief distribution.

2. motion_update:
   Use an uncertain action model to predict the next belief distribution.

The belief is a list of probabilities, one per corridor cell.
The probabilities should always sum to 1.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Corridor:
    cells: int
    door_cells: set[int]


@dataclass
class SensorModel:
    hit: float = 0.8
    false_alarm: float = 0.2


@dataclass
class MotionModel:
    success: float = 0.8
    stay: float = 0.1
    overshoot: float = 0.1


def normalise(values: list[float]) -> list[float]:
    """
    Return a new list whose values sum to 1.

    TODO:
    - compute the total
    - raise ValueError if the total is zero
    - divide each value by the total
    """
    raise NotImplementedError


def sensor_update(
    belief: list[float],
    corridor: Corridor,
    sensor: SensorModel,
    sees_door: bool,
) -> list[float]:
    """
    Update belief after observing whether the robot sees a door.

    If the robot is at a door cell:
        P(sees_door=True) = sensor.hit

    If the robot is not at a door cell:
        P(sees_door=True) = sensor.false_alarm

    TODO:
    - for each cell, compute the likelihood of the observation
    - multiply the old belief by that likelihood
    - normalise the result
    """
    raise NotImplementedError


def motion_update_right(
    belief: list[float],
    motion: MotionModel,
) -> list[float]:
    """
    Predict the next belief after the robot tries to move right.

    The motion model is:

    - success:   move one cell right
    - stay:      remain in the same cell
    - overshoot: move two cells right

    At the end of the corridor, clamp movement to the last cell.

    TODO:
    - create a new belief list filled with zeros
    - distribute probability mass from each old cell
    - return the new belief
    """
    raise NotImplementedError


def most_likely_cell(belief: list[float]) -> int:
    """
    Return the 1-based index of the most likely cell.
    """
    return max(range(len(belief)), key=lambda i: belief[i]) + 1


def assert_close(a: float, b: float, eps: float = 1e-6) -> None:
    assert abs(a - b) < eps, f"{a} != {b}"


def run_checks() -> None:
    corridor = Corridor(cells=5, door_cells={1, 3})
    sensor = SensorModel(hit=0.8, false_alarm=0.2)
    motion = MotionModel(success=0.8, stay=0.1, overshoot=0.1)

    belief = [0.2] * 5
    updated = sensor_update(belief, corridor, sensor, sees_door=True)

    assert_close(sum(updated), 1.0)

    expected = [
        0.04 / 0.44,
        0.16 / 0.44,
        0.04 / 0.44,
        0.16 / 0.44,
        0.04 / 0.44,
    ]

    for got, exp in zip(updated, expected):
        assert_close(got, exp)

    moved = motion_update_right(updated, motion)
    assert_close(sum(moved), 1.0)

    print("All checks passed.")


def run_demo() -> None:
    corridor = Corridor(cells=5, door_cells={1, 3})  # cells 2 and 4
    sensor = SensorModel(hit=0.8, false_alarm=0.2)
    motion = MotionModel(success=0.8, stay=0.1, overshoot=0.1)

    belief = [1 / corridor.cells] * corridor.cells

    print("Initial belief:")
    print(belief)

    belief = sensor_update(belief, corridor, sensor, sees_door=True)
    print("\\nAfter sensing a door:")
    print(belief)
    print("Most likely cell:", most_likely_cell(belief))

    belief = motion_update_right(belief, motion)
    print("\\nAfter moving right:")
    print(belief)
    print("Most likely cell:", most_likely_cell(belief))

    belief = sensor_update(belief, corridor, sensor, sees_door=False)
    print("\\nAfter sensing no door:")
    print(belief)
    print("Most likely cell:", most_likely_cell(belief))


if __name__ == "__main__":
    run_demo()
    # Uncomment once you have implemented the TODO functions:
    # run_checks()
'''
