"""Maze generation helpers for the labyrinth demo."""

from __future__ import annotations

import random

from ai9414.labyrinth.models import LabyrinthDefinition

SIZE_DIMENSIONS = {
    "small": (13, 13),
    "medium": (21, 21),
    "large": (31, 31),
}


def generate_labyrinth(*, size: str = "small", seed: int = 1) -> LabyrinthDefinition:
    if size not in SIZE_DIMENSIONS:
        raise ValueError(f"Unknown labyrinth size '{size}'.")

    rows, cols = SIZE_DIMENSIONS[size]
    rng = random.Random(seed)
    grid = [["#" for _ in range(cols)] for _ in range(rows)]

    def carve(r: int, c: int) -> None:
        grid[r][c] = " "
        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
        rng.shuffle(directions)
        for dr, dc in directions:
            nr = r + dr
            nc = c + dc
            if not (1 <= nr < rows - 1 and 1 <= nc < cols - 1):
                continue
            if grid[nr][nc] != "#":
                continue
            grid[r + dr // 2][c + dc // 2] = " "
            carve(nr, nc)

    carve(1, 1)
    grid[1][1] = "S"
    grid[rows - 2][cols - 2] = "E"

    return LabyrinthDefinition(
        rows=rows,
        cols=cols,
        grid=["".join(row) for row in grid],
        start=[1, 1],
        exit=[rows - 2, cols - 2],
        seed=seed,
        size=size,
    )
