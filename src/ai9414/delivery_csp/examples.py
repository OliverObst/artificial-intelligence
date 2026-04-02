"""Curated delivery time-slot CSP examples."""

from __future__ import annotations

from ai9414.delivery_csp.models import (
    DeliveryConstraint,
    DeliveryCspExample,
    DeliveryCspProblem,
    DeliveryRoom,
    DeliverySlot,
    DeliveryTask,
    DeliveryValue,
)


def _shared_slots() -> list[DeliverySlot]:
    return [
        DeliverySlot(id="slot_1", label="09:00", order=0),
        DeliverySlot(id="slot_2", label="11:00", order=1),
        DeliverySlot(id="slot_3", label="14:00", order=2),
    ]


def _shared_rooms() -> list[DeliveryRoom]:
    return [
        DeliveryRoom(id="dock", label="Dock"),
        DeliveryRoom(id="clinic", label="Clinic"),
    ]


def _shared_values() -> list[DeliveryValue]:
    return [
        DeliveryValue(id="slot_1_dock", slot="slot_1", room="dock", label="09:00 @ Dock"),
        DeliveryValue(id="slot_1_clinic", slot="slot_1", room="clinic", label="09:00 @ Clinic"),
        DeliveryValue(id="slot_2_dock", slot="slot_2", room="dock", label="11:00 @ Dock"),
        DeliveryValue(id="slot_2_clinic", slot="slot_2", room="clinic", label="11:00 @ Clinic"),
        DeliveryValue(id="slot_3_dock", slot="slot_3", room="dock", label="14:00 @ Dock"),
        DeliveryValue(id="slot_3_clinic", slot="slot_3", room="clinic", label="14:00 @ Clinic"),
    ]


def build_examples() -> dict[str, DeliveryCspExample]:
    """Return curated delivery-scheduling CSP examples."""

    slots = _shared_slots()
    rooms = _shared_rooms()
    values = _shared_values()

    deliveries = [
        DeliveryTask(id="meds", label="Medicine crate", short_label="M", colour="#c75b4a", description="Must reach the clinic after pathology."),
        DeliveryTask(id="path", label="Pathology samples", short_label="P", colour="#4d79ab", description="Should be processed before the medicine crate."),
        DeliveryTask(id="food", label="Catering trolley", short_label="F", colour="#4f8b63", description="Cannot arrive in the same slot as pathology."),
        DeliveryTask(id="linen", label="Fresh linen", short_label="L", colour="#c7a233", description="Dock-only delivery because the cart is too wide."),
        DeliveryTask(id="waste", label="Waste pickup", short_label="W", colour="#8b674f", description="Clinic-only delivery because it requires the secure room."),
    ]

    examples = {
        "weekday_schedule": DeliveryCspExample(
            title="CSP Demo - Delivery Time Slots",
            subtitle="Five deliveries, three time slots, and room-specific availability. Watch how ordering and slot conflicts prune future options.",
            problem=DeliveryCspProblem(
                title="Weekday delivery schedule",
                subtitle="Assign each delivery to a room and time slot.",
                deliveries=deliveries,
                slots=slots,
                rooms=rooms,
                values=values,
                domains={
                    "meds": ["slot_2_clinic", "slot_3_clinic"],
                    "path": ["slot_1_clinic", "slot_2_clinic"],
                    "food": ["slot_1_dock", "slot_2_dock", "slot_3_dock"],
                    "linen": ["slot_1_dock", "slot_2_dock"],
                    "waste": ["slot_2_clinic", "slot_3_clinic"],
                },
                constraints=[
                    DeliveryConstraint(
                        kind="precedence",
                        left="path",
                        right="meds",
                        label="Pathology before medicine",
                        description="The pathology samples must arrive before the medicine crate.",
                    ),
                    DeliveryConstraint(
                        kind="not_same_slot",
                        left="path",
                        right="food",
                        label="Pathology and catering separate",
                        description="Pathology and catering cannot use the same time slot.",
                    ),
                    DeliveryConstraint(
                        kind="precedence",
                        left="linen",
                        right="waste",
                        label="Linen before waste",
                        description="Fresh linen should arrive before the waste pickup.",
                    ),
                ],
            ),
        ),
        "precedence_chain": DeliveryCspExample(
            title="CSP Demo - Delivery Precedence Chain",
            subtitle="A tighter scheduling example where precedence constraints drive most of the pruning.",
            problem=DeliveryCspProblem(
                title="Precedence chain",
                subtitle="Ordering constraints dominate this schedule.",
                deliveries=deliveries,
                slots=slots,
                rooms=rooms,
                values=values,
                domains={
                    "meds": ["slot_2_clinic", "slot_3_clinic"],
                    "path": ["slot_1_clinic", "slot_2_clinic"],
                    "food": ["slot_2_dock", "slot_3_dock"],
                    "linen": ["slot_1_dock", "slot_2_dock"],
                    "waste": ["slot_2_clinic", "slot_3_clinic"],
                },
                constraints=[
                    DeliveryConstraint(
                        kind="precedence",
                        left="linen",
                        right="food",
                        label="Linen before catering",
                        description="Fresh linen must arrive before catering.",
                    ),
                    DeliveryConstraint(
                        kind="precedence",
                        left="food",
                        right="waste",
                        label="Catering before waste",
                        description="Catering must finish before waste pickup.",
                    ),
                    DeliveryConstraint(
                        kind="precedence",
                        left="path",
                        right="meds",
                        label="Pathology before medicine",
                        description="The pathology samples must arrive before the medicine crate.",
                    ),
                ],
            ),
        ),
        "room_pressure_unsat": DeliveryCspExample(
            title="CSP Demo - Room Pressure (Unsatisfiable)",
            subtitle="This schedule fails because too many deliveries require the same room and ordering leaves no legal arrangement.",
            problem=DeliveryCspProblem(
                title="Room pressure",
                subtitle="A deliberately unsatisfiable scheduling CSP.",
                deliveries=deliveries,
                slots=slots,
                rooms=rooms,
                values=values,
                domains={
                    "meds": ["slot_2_clinic", "slot_3_clinic"],
                    "path": ["slot_1_clinic", "slot_2_clinic"],
                    "food": ["slot_2_clinic", "slot_3_clinic"],
                    "linen": ["slot_1_dock", "slot_2_dock"],
                    "waste": ["slot_2_clinic", "slot_3_clinic"],
                },
                constraints=[
                    DeliveryConstraint(
                        kind="precedence",
                        left="path",
                        right="meds",
                        label="Pathology before medicine",
                        description="The pathology samples must arrive before the medicine crate.",
                    ),
                    DeliveryConstraint(
                        kind="precedence",
                        left="meds",
                        right="waste",
                        label="Medicine before waste",
                        description="Medicine must be delivered before the waste pickup.",
                    ),
                    DeliveryConstraint(
                        kind="not_same_slot",
                        left="food",
                        right="waste",
                        label="Food and waste separate",
                        description="Food and waste cannot share the same time slot.",
                    ),
                ],
            ),
        ),
    }

    return examples
