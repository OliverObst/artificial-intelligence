"""Named labyrinth configuration presets."""

from __future__ import annotations

from ai9414.labyrinth.generator import generate_labyrinth
from ai9414.labyrinth.models import LabyrinthExample


def build_examples() -> dict[str, LabyrinthExample]:
    small = LabyrinthExample(
        name="small",
        title="Small configuration",
        subtitle="A compact maze with a short DFS route and clear branch choices.",
        labyrinth=generate_labyrinth(size="small", seed=13),
        metadata={"difficulty": "small", "teaching_note": "DFS commits to one branch until it reaches a dead end or the exit."},
    )
    medium = LabyrinthExample(
        name="medium",
        title="Medium configuration",
        subtitle="A medium maze with visible backtracking through several side branches.",
        labyrinth=generate_labyrinth(size="medium", seed=10),
        metadata={"difficulty": "medium", "teaching_note": "Backtracking shortens the route in the maze while the tree keeps the full search history."},
    )
    large = LabyrinthExample(
        name="large",
        title="Large configuration",
        subtitle="A larger maze with longer DFS branches and more visible backtracking.",
        labyrinth=generate_labyrinth(size="large", seed=10),
        metadata={"difficulty": "large", "teaching_note": "Longer routes make DFS commitment and backtracking easier to spot."},
    )
    return {small.name: small, medium.name: medium, large.name: large}
