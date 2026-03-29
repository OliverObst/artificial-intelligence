"""Domain models for the DPLL logic demo."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model
from ai9414.logic.parser import extract_variables_from_clauses

LogicMode = Literal["sat", "entailment"]
VariableOrder = Literal["alphabetical", "appearance"]


def normalise_literal(raw: str) -> str:
    text = str(raw).strip()
    if not text:
        raise ValueError("Literals must be non-empty strings.")
    if text.startswith("!"):
        text = f"~{text[1:]}"
    text = text.replace(" ", "")
    variable = text[1:] if text.startswith("~") else text
    if not variable or not variable.replace("_", "a").isalnum() or not variable[0].isalpha():
        raise ValueError(f"Literal '{raw}' is invalid.")
    return f"~{variable}" if text.startswith("~") else variable


class LogicProblem(AI9414Model):
    mode: LogicMode = "sat"
    title: str
    subtitle: str = ""
    clauses: list[list[str]]
    variables: list[str] = Field(default_factory=list)
    kb_formulas: list[str] = Field(default_factory=list)
    query: str | None = None
    entailment_target: str | None = None
    original_input: list[str] = Field(default_factory=list)

    @field_validator("clauses")
    @classmethod
    def validate_clauses(cls, value: list[list[str]]) -> list[list[str]]:
        if not value:
            raise ValueError("At least one clause is required.")
        normalised: list[list[str]] = []
        for clause in value:
            if not clause:
                raise ValueError("Clauses must not be empty.")
            normalised.append([normalise_literal(literal) for literal in clause])
        return normalised

    @model_validator(mode="after")
    def populate_variables(self) -> "LogicProblem":
        clause_variables = extract_variables_from_clauses(self.clauses)
        if self.variables:
            supplied = sorted(dict.fromkeys(self.variables))
            if supplied != clause_variables:
                raise ValueError("Variables must match the symbols appearing in the clauses.")
            self.variables = supplied
        else:
            self.variables = clause_variables

        if self.mode == "entailment":
            if not self.kb_formulas or self.query is None:
                raise ValueError("Entailment problems require knowledge-base formulas and a query.")
            if self.entailment_target is None:
                self.entailment_target = f"KB and not ({self.query})"
        return self


class DpllTreeNode(AI9414Model):
    tree_id: str
    graph_node: str
    parent: str | None = None
    depth: int
    path_cost: float = 0.0
    status: str = "active"
    order: int = 0
    x: float = 0.0
    y: float = 0.0
    terminal: bool = False
    assignment_text: str = ""
    reason: str = "start"


class LogicExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    problem: LogicProblem
    metadata: dict[str, Any] = Field(default_factory=dict)


class LogicConfigData(AI9414Model):
    mode: LogicMode = "sat"
    title: str = "Instructor-supplied DPLL problem"
    subtitle: str = "Instructor-supplied CNF formula."
    clauses: list[list[str]] | None = None
    kb_formulas: list[str] = Field(default_factory=list)
    query: str | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "LogicConfigData":
        if self.mode == "sat" and not self.clauses:
            raise ValueError("SAT configurations require 'clauses'.")
        if self.mode == "entailment" and (not self.kb_formulas or self.query is None):
            raise ValueError("Entailment configurations require 'kb_formulas' and 'query'.")
        return self


class LogicConfigModel(BaseConfigModel):
    app_type: str = "logic"
    data: LogicConfigData

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {"playback_speed", "unit_propagation", "pure_literals", "variable_order", "problem_mode"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(unknown)}.")
        return value
