"""Models for the spatial graph DFS demo."""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model


class SpatialGraphNode(AI9414Model):
    id: str
    x: float
    y: float


class SpatialGraphEdge(AI9414Model):
    u: str
    v: str
    id: str | None = None

    @model_validator(mode="after")
    def populate_id(self) -> "SpatialGraphEdge":
        if self.u == self.v:
            raise ValueError("Graph edges must connect two distinct nodes.")
        left, right = sorted((self.u, self.v))
        self.id = f"{left}--{right}"
        return self


class SpatialGraphDefinition(AI9414Model):
    nodes: list[SpatialGraphNode]
    edges: list[SpatialGraphEdge]
    start: str
    goal: str
    seed: int | None = None
    size: str | None = None

    @model_validator(mode="after")
    def validate_references(self) -> "SpatialGraphDefinition":
        node_ids = {node.id for node in self.nodes}
        if len(node_ids) != len(self.nodes):
            raise ValueError("Graph node ids must be unique.")
        if self.start not in node_ids or self.goal not in node_ids:
            raise ValueError("Start and goal must reference existing nodes.")
        edge_ids = set()
        for edge in self.edges:
            if edge.u not in node_ids or edge.v not in node_ids:
                raise ValueError("Each graph edge must reference existing nodes.")
            if edge.id in edge_ids:
                raise ValueError("Graph edges must be unique.")
            edge_ids.add(edge.id)
        return self


class GraphDfsTreeNode(AI9414Model):
    tree_id: str
    graph_node: str
    parent: str | None = None
    depth: int
    path_cost: int
    status: str = "active"
    order: int = 0
    x: float = 0.0
    y: float = 0.0


class GraphDfsExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    graph: SpatialGraphDefinition
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphDfsConfigData(AI9414Model):
    subtitle: str = "Instructor-supplied spatial graph."
    graph: SpatialGraphDefinition


class GraphDfsConfigModel(BaseConfigModel):
    app_type: str = "graph_dfs"
    data: GraphDfsConfigData

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {"playback_speed"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(unknown)}.")
        return value
