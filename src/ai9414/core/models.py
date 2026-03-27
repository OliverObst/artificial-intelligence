"""Shared JSON schema models for ai9414."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"

ModeLiteral = Literal["student", "solution"]
ExecutionModeLiteral = Literal["precomputed", "incremental"]


class AI9414Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Capabilities(AI9414Model):
    step: bool = True
    play: bool = True
    reset: bool = True
    set_options: bool = True
    solution_mode: bool = True
    config_files: bool = True


class AppManifest(AI9414Model):
    schema_version: str = SCHEMA_VERSION
    app_type: str
    app_title: str
    mode: ModeLiteral = "student"
    execution_mode: ExecutionModeLiteral = "precomputed"
    capabilities: Capabilities = Field(default_factory=Capabilities)


class SessionView(AI9414Model):
    current_step: int = 0


class SessionState(AI9414Model):
    schema_version: str = SCHEMA_VERSION
    app_type: str
    example_name: str | None = None
    config_name: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    view: SessionView = Field(default_factory=SessionView)
    data: dict[str, Any] = Field(default_factory=dict)


class TraceSummary(AI9414Model):
    step_count: int = 0
    result: str = "unknown"


class TraceStep(AI9414Model):
    index: int
    label: str
    annotation: str = ""
    teaching_note: str | None = None
    state_patch: dict[str, Any] = Field(default_factory=dict)


class TraceBundle(AI9414Model):
    schema_version: str = SCHEMA_VERSION
    app_type: str
    trace_id: str
    is_complete: bool = True
    summary: TraceSummary = Field(default_factory=TraceSummary)
    steps: list[TraceStep] = Field(default_factory=list)


class ActionRequest(AI9414Model):
    action: Literal[
        "reset",
        "rerun",
        "step_to",
        "next_step",
        "previous_step",
        "set_option",
        "load_example",
        "load_config",
    ]
    payload: dict[str, Any] = Field(default_factory=dict)


class StructuredError(AI9414Model):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ActionResponse(AI9414Model):
    ok: bool = True
    state: SessionState | dict[str, Any] | None = None
    trace: TraceBundle | dict[str, Any] | None = None
    new_step: TraceStep | dict[str, Any] | None = None
    trace_complete: bool | None = None
    error: StructuredError | None = None

