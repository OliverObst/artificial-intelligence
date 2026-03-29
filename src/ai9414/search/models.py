"""Search-domain models for the weighted graph demo."""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model


def canonical_edge_id(u: str, v: str) -> str:
    left, right = sorted((u, v))
    return f"{left}--{right}"


class GraphNode(AI9414Model):
    id: str
    x: float
    y: float


class GraphEdge(AI9414Model):
    u: str
    v: str
    cost: float
    id: str | None = None

    @model_validator(mode="after")
    def populate_id(self) -> "GraphEdge":
        if self.u == self.v:
            raise ValueError("Graph edges must connect two distinct nodes.")
        if self.cost <= 0:
            raise ValueError("Graph edge costs must be positive.")
        self.id = canonical_edge_id(self.u, self.v)
        return self


class WeightedGraph(AI9414Model):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    start: str
    goal: str
    seed: int | None = None
    size: str | None = None

    @model_validator(mode="after")
    def validate_references(self) -> "WeightedGraph":
        node_ids = {node.id for node in self.nodes}
        if len(node_ids) != len(self.nodes):
            raise ValueError("Graph node ids must be unique.")
        if self.start not in node_ids or self.goal not in node_ids:
            raise ValueError("Start and goal must both reference existing nodes.")
        for edge in self.edges:
            if edge.u not in node_ids or edge.v not in node_ids:
                raise ValueError("Each edge endpoint must reference an existing node.")
        return self


class SearchTreeNode(AI9414Model):
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


class SearchExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    graph: WeightedGraph
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchConfigData(AI9414Model):
    subtitle: str = "Instructor-supplied weighted graph."
    graph: WeightedGraph


class SearchConfigModel(BaseConfigModel):
    app_type: str = "search"
    data: SearchConfigData

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {"playback_speed"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(unknown)}.")
        return value
