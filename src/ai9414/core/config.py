"""Shared configuration loading helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import Field, ValidationError

from ai9414.core.errors import AI9414Error
from ai9414.core.models import AI9414Model, SCHEMA_VERSION


class BaseConfigModel(AI9414Model):
    schema_version: str = SCHEMA_VERSION
    app_type: str
    title: str
    options: dict[str, Any] = Field(default_factory=dict)
    data: dict[str, Any] = Field(default_factory=dict)


def load_json_config(path: str | Path) -> BaseConfigModel:
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise AI9414Error(
            code="invalid_configuration_file",
            message=f"Configuration file '{config_path.name}' does not exist.",
            details={"path": str(config_path)},
        )

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AI9414Error(
            code="invalid_configuration_file",
            message=(
                f"Configuration file '{config_path.name}' is invalid JSON: {exc.msg}."
            ),
            details={"path": str(config_path), "line": exc.lineno, "column": exc.colno},
        ) from exc

    try:
        return BaseConfigModel.model_validate(raw)
    except ValidationError as exc:
        raise AI9414Error(
            code="invalid_configuration_file",
            message=f"Configuration file '{config_path.name}' is invalid: {exc.errors()[0]['msg']}.",
            details={"path": str(config_path), "errors": exc.errors()},
        ) from exc

