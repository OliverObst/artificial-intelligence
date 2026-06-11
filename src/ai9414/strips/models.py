"""Domain models for the STRIPS planning demo."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model

CANONICAL_ROOMS: tuple[str, ...] = ("corridor", "mail_room", "office_a", "office_b", "lab")
CANONICAL_BLOCKS: tuple[str, ...] = ("a", "b", "c")


class StripsProblem(AI9414Model):
    title: str = "Canonical delivery"
    subtitle: str = "A tiny office delivery task with one parcel, one keycard, and one locked door."
    domain: Literal["delivery", "blocksworld"] = "delivery"
    rooms: list[str] = Field(default_factory=lambda: list(CANONICAL_ROOMS))
    robot_start: str = "corridor"
    parcel_start: str = "mail_room"
    keycard_start: str = "office_a"
    locked_edge: tuple[str, str] = ("corridor", "lab")
    door_locked: bool = True
    goal: list[tuple[str, ...]] = Field(default_factory=lambda: [("at", "parcel", "lab")])
    blocks: list[str] = Field(default_factory=lambda: list(CANONICAL_BLOCKS))
    initial_stacks: list[list[str]] = Field(default_factory=lambda: [["c", "a"], ["b"]])
    supports: list[str] = Field(default_factory=lambda: ["table"])
    initial_stack_supports: list[str] = Field(default_factory=list)
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
            if not fact or not fact[0]:
                raise ValueError("Each goal fact must include a predicate.")
            if len(fact) < 2 and fact[0] != "handempty":
                raise ValueError("Each non-handempty goal fact must include at least one argument.")
            normalised.append(fact)
        return normalised

    @field_validator("blocks")
    @classmethod
    def validate_blocks(cls, value: list[str]) -> list[str]:
        normalised = [str(block).strip().lower() for block in value]
        if len(set(normalised)) != len(normalised):
            raise ValueError("Block names must be unique.")
        if any(not block or block == "table" for block in normalised):
            raise ValueError("Block names must be non-empty and must not be 'table'.")
        return normalised

    @field_validator("initial_stacks")
    @classmethod
    def validate_initial_stacks(cls, value: list[list[str]]) -> list[list[str]]:
        normalised: list[list[str]] = []
        for stack in value:
            normalised_stack = [str(block).strip().lower() for block in stack]
            if not normalised_stack:
                continue
            normalised.append(normalised_stack)
        if not normalised:
            raise ValueError("At least one initial block stack is required.")
        return normalised

    @field_validator("supports")
    @classmethod
    def validate_supports(cls, value: list[str]) -> list[str]:
        normalised = [str(support).strip().lower() for support in value]
        if len(set(normalised)) != len(normalised):
            raise ValueError("Support names must be unique.")
        if any(not support for support in normalised):
            raise ValueError("Support names must be non-empty.")
        return normalised

    @field_validator("initial_stack_supports")
    @classmethod
    def validate_initial_stack_supports(cls, value: list[str]) -> list[str]:
        return [str(support).strip().lower() for support in value]

    @model_validator(mode="after")
    def validate_problem(self) -> "StripsProblem":
        if self.domain == "blocksworld":
            block_set = set(self.blocks)
            support_set = set(self.supports)
            if block_set & support_set:
                raise ValueError("Blocks and supports must use distinct names.")
            if not self.initial_stack_supports:
                if self.supports == ["table"]:
                    self.initial_stack_supports = ["table"] * len(self.initial_stacks)
                elif len(self.initial_stacks) <= len(self.supports):
                    self.initial_stack_supports = list(self.supports[: len(self.initial_stacks)])
            if len(self.initial_stack_supports) != len(self.initial_stacks):
                raise ValueError("initial_stack_supports must match the number of initial stacks.")
            if any(support not in support_set for support in self.initial_stack_supports):
                raise ValueError("initial_stack_supports must reference known supports.")
            if self.supports != ["table"] and len(set(self.initial_stack_supports)) != len(self.initial_stack_supports):
                raise ValueError("Non-table supports may hold at most one initial stack each.")
            seen: list[str] = [block for stack in self.initial_stacks for block in stack]
            if set(seen) != block_set or len(seen) != len(block_set):
                raise ValueError("initial_stacks must contain each configured block exactly once.")
            for predicate, *args in self.goal:
                if predicate not in {"on", "clear", "holding", "handempty"}:
                    raise ValueError("Blocks World goals may use only on, clear, holding, or handempty.")
                for arg in args:
                    if arg not in block_set and arg not in support_set:
                        raise ValueError("Blocks World goal facts must reference known blocks or supports.")
            return self

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
