"""Named office-layout presets for the delivery DFS demo."""

from __future__ import annotations

from ai9414.delivery.models import DeliveryExample
from ai9414.labyrinth.models import LabyrinthDefinition


def build_examples() -> dict[str, DeliveryExample]:
    return {
        "four_rooms": DeliveryExample(
            name="four_rooms",
            title="Four-room office delivery",
            subtitle=(
                "A small office floor with four rooms. The robot starts in the top-left room "
                "and searches for a delivery location in the bottom-right room."
            ),
            labyrinth=LabyrinthDefinition(
                rows=17,
                cols=17,
                grid=[
                    "#################",
                    "#S      #       #",
                    "#               #",
                    "#       #       #",
                    "#       #       #",
                    "#       #       #",
                    "#       #       #",
                    "#       #       #",
                    "## ########### ##",
                    "#       #       #",
                    "#       #       #",
                    "#       #       #",
                    "#       #   E   #",
                    "#       #       #",
                    "#               #",
                    "#       #       #",
                    "#################",
                ],
                start=[1, 1],
                exit=[12, 12],
                size="four_rooms",
            ),
            metadata={"layout": "four-room office"},
        ),
        "corridor": DeliveryExample(
            name="corridor",
            title="Corridor office delivery",
            subtitle=(
                "A central corridor connects four offices. DFS explores the corridor and "
                "side rooms while searching for the delivery location."
            ),
            labyrinth=LabyrinthDefinition(
                rows=15,
                cols=21,
                grid=[
                    "#####################",
                    "#S    ##       ##   #",
                    "#     ##       ##   #",
                    "#     ##       ##   #",
                    "#     ##       ##   #",
                    "### ##### ### ##### #",
                    "###       # #       #",
                    "#########   #########",
                    "###       # #       #",
                    "### ##### ### ##### #",
                    "#     ##       ##   #",
                    "#     ##       ##   #",
                    "#     ##       ## E #",
                    "#     ##       ##   #",
                    "#####################",
                ],
                start=[1, 1],
                exit=[12, 18],
                size="corridor",
            ),
            metadata={"layout": "corridor office"},
        ),
    }
