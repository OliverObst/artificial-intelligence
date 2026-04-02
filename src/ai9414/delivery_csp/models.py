"""Domain models for the delivery time-slot CSP demo."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from ai9414.core.models import AI9414Model, SCHEMA_VERSION


class DeliverySlot(AI9414Model):
    id: str
    label: str
    order: int


class DeliveryRoom(AI9414Model):
    id: str
    label: str


class DeliveryTask(AI9414Model):
    id: str
    label: str
    short_label: str
    colour: str
    description: str = ""


class DeliveryValue(AI9414Model):
    id: str
    slot: str
    room: str
    label: str


ConstraintKind = Literal["precedence", "not_same_slot"]


class DeliveryConstraint(AI9414Model):
    kind: ConstraintKind
    left: str
    right: str
    label: str
    description: str


class DeliveryCspProblem(AI9414Model):
    """A small delivery-scheduling CSP."""

    title: str = "Delivery time-slot assignment"
    subtitle: str = "Assign each delivery to a room and time slot while respecting ordering and availability constraints."
    deliveries: list[DeliveryTask]
    slots: list[DeliverySlot]
    rooms: list[DeliveryRoom]
    values: list[DeliveryValue]
    domains: dict[str, list[str]]
    constraints: list[DeliveryConstraint] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _accept_variables_alias(cls, data: Any) -> Any:
        if isinstance(data, dict) and "variables" in data:
            copied = dict(data)
            copied.pop("variables", None)
            return copied
        return data

    @model_validator(mode="after")
    def _normalise(self) -> "DeliveryCspProblem":
        if not self.deliveries:
            raise ValueError("A delivery CSP must include at least one delivery.")
        if not self.slots:
            raise ValueError("A delivery CSP must include at least one time slot.")
        if not self.rooms:
            raise ValueError("A delivery CSP must include at least one room.")
        if not self.values:
            raise ValueError("A delivery CSP must include at least one candidate assignment value.")

        delivery_ids = [delivery.id for delivery in self.deliveries]
        if len(set(delivery_ids)) != len(delivery_ids):
            raise ValueError("Delivery ids must be unique.")
        slot_ids = {slot.id for slot in self.slots}
        room_ids = {room.id for room in self.rooms}
        value_ids = [value.id for value in self.values]
        if len(set(value_ids)) != len(value_ids):
            raise ValueError("Assignment value ids must be unique.")

        value_map = {value.id: value for value in self.values}
        for value in self.values:
            if value.slot not in slot_ids:
                raise ValueError(f"Unknown slot '{value.slot}' in assignment value '{value.id}'.")
            if value.room not in room_ids:
                raise ValueError(f"Unknown room '{value.room}' in assignment value '{value.id}'.")

        normalised_domains: dict[str, list[str]] = {}
        for delivery in self.deliveries:
            raw_domain = self.domains.get(delivery.id, value_ids)
            if not raw_domain:
                raise ValueError(f"Delivery '{delivery.id}' has an empty domain.")
            for value_id in raw_domain:
                if value_id not in value_map:
                    raise ValueError(f"Unknown assignment value '{value_id}' in the domain for '{delivery.id}'.")
            normalised_domains[delivery.id] = list(dict.fromkeys(raw_domain))
        self.domains = normalised_domains

        delivery_id_set = set(delivery_ids)
        for constraint in self.constraints:
            if constraint.left not in delivery_id_set or constraint.right not in delivery_id_set:
                raise ValueError(f"Constraint '{constraint.label}' references an unknown delivery.")
            if constraint.left == constraint.right:
                raise ValueError(f"Constraint '{constraint.label}' must relate two different deliveries.")

        return self

    def to_payload(self) -> dict[str, Any]:
        payload = self.model_dump()
        payload["variables"] = [delivery.id for delivery in self.deliveries]
        return payload

    def slot_order(self) -> dict[str, int]:
        return {slot.id: slot.order for slot in self.slots}

    def value_map(self) -> dict[str, DeliveryValue]:
        return {value.id: value for value in self.values}

    def delivery_map(self) -> dict[str, DeliveryTask]:
        return {delivery.id: delivery for delivery in self.deliveries}


class DeliveryCspExample(AI9414Model):
    title: str
    subtitle: str
    problem: DeliveryCspProblem


class DeliveryCspConfigData(AI9414Model):
    problem: DeliveryCspProblem


class DeliveryCspConfigModel(AI9414Model):
    schema_version: str = SCHEMA_VERSION
    app_type: str = "delivery_csp"
    options: dict[str, Any] = Field(default_factory=dict)
    data: DeliveryCspConfigData
