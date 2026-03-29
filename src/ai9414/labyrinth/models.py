"""Models for the labyrinth DFS demo."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model


class LabyrinthDefinition(AI9414Model):
    rows: int
    cols: int
    grid: list[str]
    start: list[int]
    exit: list[int]
    seed: int | None = None
    size: str | None = None

    @model_validator(mode="after")
    def validate_grid(self) -> "LabyrinthDefinition":
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("Labyrinth dimensions must be positive.")
        if len(self.grid) != self.rows:
            raise ValueError("Grid row count does not match 'rows'.")
        if any(len(row) != self.cols for row in self.grid):
            raise ValueError("Each grid row must match 'cols'.")
        start = tuple(self.start)
        exit_cell = tuple(self.exit)
        if len(start) != 2 or len(exit_cell) != 2:
            raise ValueError("Start and exit coordinates must have two integers.")
        if not (0 <= start[0] < self.rows and 0 <= start[1] < self.cols):
            raise ValueError("Start coordinate is outside the grid.")
        if not (0 <= exit_cell[0] < self.rows and 0 <= exit_cell[1] < self.cols):
            raise ValueError("Exit coordinate is outside the grid.")
        if self.grid[start[0]][start[1]] != "S":
            raise ValueError("The start coordinate must point to 'S'.")
        if self.grid[exit_cell[0]][exit_cell[1]] != "E":
            raise ValueError("The exit coordinate must point to 'E'.")
        return self


class LabyrinthTreeNode(AI9414Model):
    tree_id: str
    graph_node: str
    cell: list[int]
    parent: str | None = None
    depth: int
    path_cost: int
    status: str = "active"
    order: int = 0
    x: float = 0.0
    y: float = 0.0


class LabyrinthExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    labyrinth: LabyrinthDefinition
    metadata: dict[str, Any] = Field(default_factory=dict)


class LabyrinthConfigData(AI9414Model):
    subtitle: str = "Instructor-supplied labyrinth."
    labyrinth: LabyrinthDefinition


class LabyrinthConfigModel(BaseConfigModel):
    app_type: str = "labyrinth"
    data: LabyrinthConfigData
