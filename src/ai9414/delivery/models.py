"""Models for the delivery DFS demo."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model
from ai9414.labyrinth.models import LabyrinthDefinition


class DeliveryExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    labyrinth: LabyrinthDefinition
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeliveryConfigData(AI9414Model):
    subtitle: str = "Instructor-supplied delivery office."
    labyrinth: LabyrinthDefinition


class DeliveryConfigModel(BaseConfigModel):
    app_type: str = "delivery"
    data: DeliveryConfigData
