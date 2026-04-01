"""Domain models for the STRIPS planning demo."""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model

CANONICAL_ROOMS: tuple[str, ...] = ("corridor", "mail_room", "office_a", "office_b", "lab")


class StripsProblem(AI9414Model):
    title: str = "Canonical delivery"
    subtitle: str = "A tiny office delivery task with one parcel, one keycard, and one locked door."
    rooms: list[str] = Field(default_factory=lambda: list(CANONICAL_ROOMS))
    robot_start: str = "corridor"
    parcel_start: str = "mail_room"
    keycard_start: str = "office_a"
    locked_edge: tuple[str, str] = ("corridor", "lab")
    door_locked: bool = True
    goal: list[tuple[str, ...]] = Field(default_factory=lambda: [("at", "parcel", "lab")])
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("rooms")
    @classmethod
    def validate_rooms(cls, value: list[str]) -> list[str]:
        normalised = [str(room).strip() for room in value]
        if len(set(normalised)) != len(normalised):
            raise ValueError("Room names must be unique.")
        if set(normalised) != set(CANONICAL_ROOMS):
            raise ValueError(
                "This teaching demo expects exactly these five rooms: corridor, mail_room, office_a, office_b, lab."
            )
        return normalised

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, value: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
        if not value:
            raise ValueError("At least one goal fact is required.")
        normalised: list[tuple[str, ...]] = []
        for raw_fact in value:
            fact = tuple(str(part).strip() for part in raw_fact)
            if len(fact) < 2 or not fact[0]:
                raise ValueError("Each goal fact must include a predicate and at least one argument.")
            normalised.append(fact)
        return normalised

    @model_validator(mode="after")
    def validate_problem(self) -> "StripsProblem":
        room_set = set(self.rooms)
        for room_name, field_name in (
            (self.robot_start, "robot_start"),
            (self.parcel_start, "parcel_start"),
            (self.keycard_start, "keycard_start"),
        ):
            if room_name not in room_set:
                raise ValueError(f"Field '{field_name}' must reference one of the known rooms.")

        left, right = self.locked_edge
        if "lab" not in {left, right}:
            raise ValueError("The teaching door must connect to the lab.")
        other_room = right if left == "lab" else left
        if other_room not in {"corridor", "office_b"}:
            raise ValueError("The lab door may connect only to the corridor or office_b in this demo.")
        for predicate, *args in self.goal:
            if predicate == "at" and len(args) == 2 and args[1] not in room_set:
                raise ValueError("Goal facts using 'at' must reference a known room.")
        return self


class StripsExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    problem: StripsProblem
    metadata: dict[str, Any] = Field(default_factory=dict)


class StripsConfigData(AI9414Model):
    problem: StripsProblem


class StripsConfigModel(BaseConfigModel):
    app_type: str = "strips"
    data: StripsConfigData

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {"playback_speed"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(unknown)}.")
        return value
