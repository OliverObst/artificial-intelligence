"""Curated STRIPS planning examples."""

from __future__ import annotations

from ai9414.strips.models import StripsExample, StripsProblem


def build_delivery_examples() -> dict[str, StripsExample]:
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


def build_blocksworld_examples() -> dict[str, StripsExample]:
    examples = [
        _build_tower_example(3),
        _build_tower_example(4),
        _build_tower_example(5),
        StripsExample(
            name="sussman_anomaly",
            title="Blocks World: Sussman anomaly",
            subtitle="The goal on(a, b) and on(b, c) cannot be solved by permanently achieving one subgoal first.",
            problem=StripsProblem(
                title="Blocks World: Sussman anomaly",
                subtitle=(
                    "A classic STRIPS planning example where interacting subgoals require temporarily moving block a."
                ),
                domain="blocksworld",
                blocks=["a", "b", "c"],
                initial_stacks=[["c", "a"], ["b"]],
                goal=[("on", "a", "b"), ("on", "b", "c")],
                metadata={
                    "config_name": "sussman_anomaly",
                    "stack_order": "Each stack is listed from bottom to top.",
                },
            ),
        ),
        _build_hanoi_example(5),
        _build_hanoi_example(6),
    ]
    return {example.name: example for example in examples}


def build_examples() -> dict[str, StripsExample]:
    return {
        **build_delivery_examples(),
        **build_blocksworld_examples(),
    }


def _build_tower_example(num_blocks: int) -> StripsExample:
    blocks = [chr(ord("a") + index) for index in range(num_blocks)]
    goal = [("on", blocks[index], blocks[index - 1]) for index in range(1, len(blocks))]
    initial_stacks = _tower_initial_stacks(blocks)
    stack_copy = (
        f"Start with {num_blocks} blocks arranged across three table stacks."
        if num_blocks in {4, 5}
        else f"Start with {num_blocks} separate table blocks."
    )
    return StripsExample(
        name=f"{num_blocks}_block_tower",
        title=f"{num_blocks}-block tower",
        subtitle=f"{stack_copy} Build one ordered tower.",
        problem=StripsProblem(
            title=f"{num_blocks}-block tower",
            subtitle=(
                f"A straightforward Blocks World planning task with {num_blocks} blocks. "
                "The goal tower is ordered alphabetically from bottom to top."
            ),
            domain="blocksworld",
            blocks=blocks,
            initial_stacks=initial_stacks,
            goal=goal,
            metadata={
                "stack_order": "Each stack is listed from bottom to top.",
                "teaching_note": "This is a solvable warm-up before the interacting-subgoal examples.",
            },
        ),
    )


def _tower_initial_stacks(blocks: list[str]) -> list[list[str]]:
    if len(blocks) == 4:
        return [[blocks[0], blocks[3]], [blocks[1]], [blocks[2]]]
    if len(blocks) == 5:
        return [[blocks[0], blocks[4]], [blocks[1], blocks[3]], [blocks[2]]]
    return [[block] for block in blocks]


def _build_hanoi_example(num_discs: int) -> StripsExample:
    blocks = [f"d{index}" for index in range(1, num_discs + 1)]
    initial_stack = list(reversed(blocks))
    goal = [("on", f"d{num_discs}", "right_peg")]
    goal.extend(("on", f"d{index}", f"d{index + 1}") for index in range(num_discs - 1, 0, -1))
    return StripsExample(
        name=f"hanoi_{num_discs}_discs",
        title=f"Tower of Hanoi ({num_discs} discs)",
        subtitle=(
            f"Move an ordered {num_discs}-disc tower from the left peg to the right peg without placing a larger disc on a smaller one."
        ),
        problem=StripsProblem(
            title=f"Tower of Hanoi ({num_discs} discs)",
            subtitle=(
                "A Blocks World encoding with three named supports. The size rule prevents larger discs from being stacked on smaller discs."
            ),
            domain="blocksworld",
            blocks=blocks,
            supports=["left_peg", "middle_peg", "right_peg"],
            initial_stacks=[initial_stack],
            initial_stack_supports=["left_peg"],
            goal=goal,
            metadata={
                "smaller_on_larger": True,
                "block_sizes": {block: index for index, block in enumerate(blocks, start=1)},
                "stack_order": "Each stack is listed from bottom to top.",
                "hanoi_disc_moves": (2**num_discs) - 1,
                "expected_strips_actions": 2 * ((2**num_discs) - 1),
            },
        ),
    )
