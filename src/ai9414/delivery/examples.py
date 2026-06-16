"""Named office-layout presets for the delivery DFS demo."""

from __future__ import annotations

from ai9414.delivery.models import DeliveryExample
from ai9414.labyrinth.models import LabyrinthDefinition


PACMAN_MAZE_TEMPLATE = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "     #.##### ## #####.#     ",
    "     #.##          ##.#     ",
    "     #.## ###  ### ##.#     ",
    "######.## #      # ##.######",
    "      .   #      #   .      ",
    "######.## #      # ##.######",
    "     #.## ######## ##.#     ",
    "     #.##          ##.#     ",
    "     #.## ######## ##.#     ",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#...##.......S........##...#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################",
]

PACMAN_MAZE_DOTS = [
    [row_index, col_index]
    for row_index, row in enumerate(PACMAN_MAZE_TEMPLATE)
    for col_index, value in enumerate(row)
    if value == "."
]


def build_examples() -> dict[str, DeliveryExample]:
    return {
        "four_rooms": DeliveryExample(
            name="four_rooms",
            title="Four-room target delivery",
            subtitle=(
                "A small office floor with four rooms. The robot starts in the top-left room "
                "and searches for the coloured delivery target in the bottom-right room."
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
            goal_type="target",
            metadata={"layout": "four-room office"},
        ),
        "single_room": DeliveryExample(
            name="single_room",
            title="Single-room target delivery",
            subtitle=(
                "A compact 7 by 7 room with surrounding walls. The robot searches for the "
                "coloured delivery target in the same room."
            ),
            labyrinth=LabyrinthDefinition(
                rows=9,
                cols=9,
                grid=[
                    "#########",
                    "#S      #",
                    "#       #",
                    "#       #",
                    "#   E   #",
                    "#       #",
                    "#       #",
                    "#       #",
                    "#########",
                ],
                start=[1, 1],
                exit=[4, 4],
                size="single_room",
            ),
            goal_type="target",
            metadata={"layout": "single-room office"},
        ),
        "pacman": DeliveryExample(
            name="pacman",
            title="Pac-Man dot maze",
            subtitle=(
                "A larger Pac-Man-style corridor maze with collectible dots, thin internal walls, and no ghosts. "
                "The goal is to collect every dot."
            ),
            labyrinth=LabyrinthDefinition(
                rows=len(PACMAN_MAZE_TEMPLATE),
                cols=len(PACMAN_MAZE_TEMPLATE[0]),
                grid=PACMAN_MAZE_TEMPLATE,
                start=[23, 13],
                exit=[23, 13],
                collectibles=PACMAN_MAZE_DOTS,
                size="pacman",
            ),
            goal_type="collect_all",
            metadata={"layout": "pacman maze", "collectible_count": len(PACMAN_MAZE_DOTS)},
        ),
    }
