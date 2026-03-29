"""Models for the spatial graph A* demo."""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model
from ai9414.search.models import WeightedGraph


class GraphAStarTreeNode(AI9414Model):
    tree_id: str
    graph_node: str
    parent: str | None = None
    depth: int
    path_cost: float
    status: str = "active"
    order: int = 0
    x: float = 0.0
    y: float = 0.0
    terminal: bool = False


class GraphAStarExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    graph: WeightedGraph
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphAStarConfigData(AI9414Model):
    subtitle: str = "Instructor-supplied weighted graph."
    graph: WeightedGraph


class GraphAStarConfigModel(BaseConfigModel):
    app_type: str = "graph_astar"
    data: GraphAStarConfigData

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {"playback_speed"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(unknown)}.")
        return value
