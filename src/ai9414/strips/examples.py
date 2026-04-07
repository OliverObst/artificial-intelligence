"""Curated STRIPS planning examples."""

from __future__ import annotations

from ai9414.strips.models import StripsExample, StripsProblem


def build_examples() -> dict[str, StripsExample]:
    examples = [
        StripsExample(
            name="canonical_delivery",
            title="Canonical delivery",
            subtitle="Fetch the keycard, collect the parcel, unlock the lab door, and deliver the parcel.",
            problem=StripsProblem(
                title="Canonical delivery",
                subtitle="A compact office world with one parcel, one keycard, and one locked door.",
            ),
        ),
        StripsExample(
            name="robot_starts_mail_room",
            title="Robot starts in the mail room",
            subtitle="The parcel is nearby, but picking it up too early blocks the keycard action.",
            problem=StripsProblem(
                title="Robot starts in the mail room",
                subtitle="The parcel starts nearby, but collecting it too early blocks the keycard action.",
                robot_start="mail_room",
            ),
        ),
        StripsExample(
            name="keycard_in_office_b",
            title="Keycard moved to office B",
            subtitle="The same delivery goal now needs a different room order.",
            problem=StripsProblem(
                title="Keycard moved to office B",
                subtitle="Only the symbolic start state changed, but the optimal plan changes with it.",
                keycard_start="office_b",
            ),
        ),
        StripsExample(
            name="unlocked_lab",
            title="Unlocked-door baseline",
            subtitle="Without the lock, the plan no longer needs the keycard or the unlock action.",
            problem=StripsProblem(
                title="Unlocked-door baseline",
                subtitle="Without the lock, the plan no longer needs the keycard or unlock action.",
                door_locked=False,
            ),
        ),
        StripsExample(
            name="lab_via_office_b",
            title="Lab reachable through office B",
            subtitle="Changing the map connectivity changes the whole plan structure.",
            problem=StripsProblem(
                title="Lab reachable through office B",
                subtitle="The locked door now sits between office B and the lab rather than between the corridor and the lab.",
                locked_edge=("office_b", "lab"),
            ),
        ),
    ]
    return {example.name: example for example in examples}
