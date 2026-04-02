"""Domain models for the reasoning-with-uncertainty demo."""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model

CANONICAL_ROOMS: tuple[str, ...] = ("mail_room", "office_a", "corridor", "office_b", "lab")
CANONICAL_CONNECTIONS: tuple[tuple[str, str], ...] = (
    ("corridor", "mail_room"),
    ("corridor", "office_a"),
    ("corridor", "office_b"),
    ("corridor", "lab"),
)


class UncertaintyRoom(AI9414Model):
    id: str
    label: str
    charger: bool = False
    window: bool = False
    door_nearby: bool = False
    marker: str = "none"
    description: str = ""


class UncertaintyScenarioStep(AI9414Model):
    action: str
    observation: str
    true_location: str
    note: str = ""


class UncertaintyProblem(AI9414Model):
    title: str = "Office localisation"
    subtitle: str = "Track the robot with a Bayes filter while motion and sensing remain noisy."
    rooms: list[UncertaintyRoom]
    connections: list[tuple[str, str]] = Field(default_factory=lambda: list(CANONICAL_CONNECTIONS))
    initial_belief: dict[str, float]
    initial_true_location: str = "corridor"
    available_actions: list[str]
    observations: list[str]
    transition_models: dict[str, dict[str, dict[str, float]]]
    observation_model: dict[str, dict[str, float]]
    scripted_steps: list[UncertaintyScenarioStep]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("rooms")
    @classmethod
    def validate_rooms(cls, value: list[UncertaintyRoom]) -> list[UncertaintyRoom]:
        room_ids = [room.id for room in value]
        if len(set(room_ids)) != len(room_ids):
            raise ValueError("Room ids must be unique.")
        if set(room_ids) != set(CANONICAL_ROOMS):
            raise ValueError(
                "This teaching demo expects exactly these five rooms: mail_room, office_a, corridor, office_b, lab."
            )
        return value

    @field_validator("connections")
    @classmethod
    def validate_connections(cls, value: list[tuple[str, str]]) -> list[tuple[str, str]]:
        normalised = [tuple(str(part).strip() for part in edge) for edge in value]
        if len({tuple(sorted(edge)) for edge in normalised}) != len(normalised):
            raise ValueError("Connections must be unique.")
        return normalised

    @field_validator("available_actions")
    @classmethod
    def validate_available_actions(cls, value: list[str]) -> list[str]:
        actions = [str(action).strip() for action in value]
        if len(set(actions)) != len(actions):
            raise ValueError("Action names must be unique.")
        if not actions:
            raise ValueError("At least one action is required.")
        return actions

    @field_validator("observations")
    @classmethod
    def validate_observations(cls, value: list[str]) -> list[str]:
        observations = [str(observation).strip() for observation in value]
        if len(set(observations)) != len(observations):
            raise ValueError("Observation names must be unique.")
        if not observations:
            raise ValueError("At least one observation is required.")
        return observations

    @model_validator(mode="after")
    def validate_problem(self) -> "UncertaintyProblem":
        room_ids = {room.id for room in self.rooms}
        action_ids = set(self.available_actions)
        observation_ids = set(self.observations)

        if self.initial_true_location not in room_ids:
            raise ValueError("initial_true_location must reference a known room.")

        if set(self.initial_belief) != room_ids:
            raise ValueError("initial_belief must assign every room exactly once.")

        for action_name, transition_model in self.transition_models.items():
            if action_name not in action_ids:
                raise ValueError(f"Transition model '{action_name}' is not listed in available_actions.")
            if set(transition_model) != room_ids:
                raise ValueError(f"Transition model '{action_name}' must define every source room exactly once.")
            for source, destination_weights in transition_model.items():
                if set(destination_weights) != room_ids:
                    raise ValueError(
                        f"Transition model '{action_name}' for source '{source}' must define every destination room."
                    )

        if set(self.observation_model) != room_ids:
            raise ValueError("observation_model must define every room exactly once.")
        for room_id, likelihoods in self.observation_model.items():
            if set(likelihoods) != observation_ids:
                raise ValueError(f"observation_model for '{room_id}' must define every observation exactly once.")

        for step in self.scripted_steps:
            if step.action not in action_ids:
                raise ValueError(f"Scenario step action '{step.action}' is not listed in available_actions.")
            if step.observation not in observation_ids:
                raise ValueError(f"Scenario step observation '{step.observation}' is not listed in observations.")
            if step.true_location not in room_ids:
                raise ValueError(f"Scenario step true_location '{step.true_location}' is not a known room.")

        return self


class UncertaintyExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    problem: UncertaintyProblem
    metadata: dict[str, Any] = Field(default_factory=dict)


class UncertaintyConfigData(AI9414Model):
    problem: UncertaintyProblem


class UncertaintyConfigModel(BaseConfigModel):
    app_type: str = "uncertainty"
    data: UncertaintyConfigData

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {"playback_speed"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(unknown)}.")
        return value
