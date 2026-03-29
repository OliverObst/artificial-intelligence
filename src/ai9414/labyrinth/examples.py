"""Named labyrinth configuration presets."""

from __future__ import annotations

from ai9414.labyrinth.generator import generate_labyrinth
from ai9414.labyrinth.models import LabyrinthExample


def build_examples() -> dict[str, LabyrinthExample]:
    small = LabyrinthExample(
        name="small",
        title="Small configuration",
        subtitle="A compact generated maze configuration for quick DFS playback.",
        labyrinth=generate_labyrinth(size="small", seed=13),
        metadata={"difficulty": "small", "teaching_note": "Watch where DFS commits too early."},
    )
    medium = LabyrinthExample(
        name="medium",
        title="Medium configuration",
        subtitle="A medium generated maze configuration chosen to show visible backtracking.",
        labyrinth=generate_labyrinth(size="medium", seed=10),
        metadata={"difficulty": "medium", "teaching_note": "Notice how the maze view and tree view diverge."},
    )
    large = LabyrinthExample(
        name="large",
        title="Large configuration",
        subtitle="A larger generated maze configuration with a longer DFS trace and visible backtracking.",
        labyrinth=generate_labyrinth(size="large", seed=10),
        metadata={"difficulty": "large", "teaching_note": "Large mazes make DFS commitment and backtracking more obvious."},
    )
    return {small.name: small, medium.name: medium, large.name: large}
