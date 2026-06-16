"""Domain models for the resolution/refutation demo."""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model
from ai9414.logic.models import normalise_literal
from ai9414.logic.parser import extract_variables_from_clauses


def normalise_clause(clause: list[str]) -> list[str]:
    if not clause:
        raise ValueError("Initial clauses must not be empty.")
    seen: set[str] = set()
    normalised: list[str] = []
    for literal in clause:
        value = normalise_literal(literal)
        if value not in seen:
            seen.add(value)
            normalised.append(value)
    return normalised


def literal_variable(literal: str) -> str:
    value = normalise_literal(literal)
    return value[1:] if value.startswith("~") else value


def complement(literal: str) -> str:
    value = normalise_literal(literal)
    return value[1:] if value.startswith("~") else f"~{value}"


class ResolutionProofStep(AI9414Model):
    left: int
    right: int
    pivot: str
    note: str = ""

    @field_validator("left", "right")
    @classmethod
    def validate_clause_index(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Clause references are 1-based and must be positive.")
        return value

    @field_validator("pivot")
    @classmethod
    def validate_pivot(cls, value: str) -> str:
        return literal_variable(value)


class ResolutionProblem(AI9414Model):
    title: str
    subtitle: str = ""
    clauses: list[list[str]]
    steps: list[ResolutionProofStep] = Field(default_factory=list)
    query: str | None = None
    entailment_target: str | None = None
    original_input: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    visualisation: dict[str, Any] = Field(default_factory=dict)

    @field_validator("clauses")
    @classmethod
    def validate_clauses(cls, value: list[list[str]]) -> list[list[str]]:
        if not value:
            raise ValueError("At least one clause is required.")
        return [normalise_clause(clause) for clause in value]

    @model_validator(mode="after")
    def populate_variables(self) -> "ResolutionProblem":
        clause_variables = extract_variables_from_clauses(self.clauses)
        if self.variables:
            supplied = sorted(dict.fromkeys(self.variables))
            if supplied != clause_variables:
                raise ValueError("Variables must match the symbols appearing in the clauses.")
            self.variables = supplied
        else:
            self.variables = clause_variables
        return self


class ResolutionExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    problem: ResolutionProblem
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResolutionConfigData(AI9414Model):
    title: str = "Instructor-supplied resolution problem"
    subtitle: str = "Instructor-supplied clauses and proof attempt."
    clauses: list[list[str]]
    steps: list[ResolutionProofStep] = Field(default_factory=list)
    query: str | None = None
    entailment_target: str | None = None


class ResolutionConfigModel(BaseConfigModel):
    app_type: str = "resolution"
    data: ResolutionConfigData

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {"playback_speed"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(unknown)}.")
        return value
