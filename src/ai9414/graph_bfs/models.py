"""Models for the spatial graph BFS demo."""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model
from ai9414.graph_dfs.models import SpatialGraphDefinition


class GraphBfsTreeNode(AI9414Model):
    tree_id: str
    graph_node: str
    parent: str | None = None
    depth: int
    path_cost: int
    status: str = "active"
    order: int = 0
    x: float = 0.0
    y: float = 0.0


class GraphBfsExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    graph: SpatialGraphDefinition
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphBfsConfigData(AI9414Model):
    subtitle: str = "Instructor-supplied spatial graph."
    graph: SpatialGraphDefinition


class GraphBfsConfigModel(BaseConfigModel):
    app_type: str = "graph_bfs"
    data: GraphBfsConfigData

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {"playback_speed"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(unknown)}.")
        return value
