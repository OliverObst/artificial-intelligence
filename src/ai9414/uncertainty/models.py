"""Domain models for the Week 7 Bayes-filter corridor demo."""

from __future__ import annotations

import math
from typing import Any

from pydantic import Field, field_validator, model_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model


class SensorModel(AI9414Model):
    """Binary landmark sensor model."""

    hit: float = 0.8
    false_alarm: float = 0.2

    @model_validator(mode="after")
    def validate_probabilities(self) -> "SensorModel":
        for name, value in (("hit", self.hit), ("false_alarm", self.false_alarm)):
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"Sensor {name} probability must be between 0 and 1.")
        return self

    @property
    def informative(self) -> bool:
        return self.hit > self.false_alarm


class MotionModel(AI9414Model):
    """Simple uncertain motion model for left/right movement."""

    success: float = 0.8
    stay: float = 0.1
    overshoot: float = 0.1

    @model_validator(mode="after")
    def validate_probabilities(self) -> "MotionModel":
        values = [float(self.success), float(self.stay), float(self.overshoot)]
        if any(value < 0.0 for value in values):
            raise ValueError("Motion probabilities must not be negative.")
        total = sum(values)
        if total <= 0.0:
            raise ValueError("At least one motion probability must be positive.")
        if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
            raise ValueError("Motion probabilities must sum to 1.")
        return self


class CorridorProblem(AI9414Model):
    """One-dimensional corridor localisation problem.

    Positions and landmark lists are stored internally as zero-based indices.
    The browser payload also includes one-based labels for students.
    """

    title: str = "Bayes Filter Corridor"
    subtitle: str = "Track a robot by updating a belief distribution with noisy sensing and uncertain motion."
    cells: int = 10
    landmarks: dict[str, list[int]] = Field(default_factory=lambda: {"door": [1, 5]})
    initial_belief: list[float] = Field(default_factory=list)
    initial_true_position: int | None = 5
    sensor_model: SensorModel = Field(default_factory=SensorModel)
    motion_model: MotionModel = Field(default_factory=MotionModel)
    show_true_position: bool = True
    scripted_events: list[dict[str, Any]] = Field(default_factory=list)
    random_seed: int = 7
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("cells")
    @classmethod
    def validate_cell_count(cls, value: int) -> int:
        cells = int(value)
        if not 2 <= cells <= 30:
            raise ValueError("The corridor must contain between 2 and 30 cells.")
        return cells

    @model_validator(mode="after")
    def validate_problem(self) -> "CorridorProblem":
        normalised_landmarks: dict[str, list[int]] = {}
        for raw_name, raw_indices in self.landmarks.items():
            name = str(raw_name).strip().lower().replace(" ", "_")
            if not name:
                raise ValueError("Landmark names must not be empty.")
            indices = [int(index) for index in raw_indices]
            if len(set(indices)) != len(indices):
                raise ValueError(f"Landmark '{name}' contains duplicate cells.")
            for index in indices:
                if not 0 <= index < self.cells:
                    raise ValueError(
                        f"Landmark '{name}' index {index} is outside the zero-based corridor range."
                    )
            normalised_landmarks[name] = sorted(indices)
        self.landmarks = normalised_landmarks

        if self.initial_belief:
            if len(self.initial_belief) != self.cells:
                raise ValueError("initial_belief must contain one probability per cell.")
            cleaned = [float(value) for value in self.initial_belief]
            if any(value < -1e-9 for value in cleaned):
                raise ValueError("initial_belief must not contain negative probabilities.")
            total = sum(cleaned)
            if total <= 0:
                raise ValueError("initial_belief must assign positive mass.")
            if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
                raise ValueError("initial_belief must sum to 1.")
            self.initial_belief = [0.0 if abs(value) < 1e-12 else value for value in cleaned]
        else:
            self.initial_belief = [1.0 / self.cells for _ in range(self.cells)]

        if self.initial_true_position is not None:
            position = int(self.initial_true_position)
            if not 0 <= position < self.cells:
                raise ValueError("initial_true_position is outside the zero-based corridor range.")
            self.initial_true_position = position

        return self

    @property
    def landmark_types(self) -> list[str]:
        return sorted(self.landmarks.keys())


class UncertaintyExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    problem: CorridorProblem
    metadata: dict[str, Any] = Field(default_factory=dict)


class UncertaintyConfigData(AI9414Model):
    problem: CorridorProblem


class UncertaintyConfigModel(BaseConfigModel):
    app_type: str = "uncertainty"
    data: UncertaintyConfigData

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "playback_speed",
            "sensor_hit",
            "sensor_false_alarm",
            "motion_success",
            "motion_stay",
            "motion_overshoot",
            "show_true_position",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(unknown)}.")
        return value

