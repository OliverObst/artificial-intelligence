"""Curated corridor examples for the Week 7 Bayes-filter demo."""

from __future__ import annotations

from ai9414.uncertainty.models import CorridorProblem, MotionModel, SensorModel, UncertaintyExample


def build_examples() -> dict[str, UncertaintyExample]:
    examples = [
        UncertaintyExample(
            name="two_doors",
            title="Two identical doors",
            subtitle="A uniform prior becomes ambiguous after one door reading, then motion and later evidence resolve it.",
            problem=make_problem(
                title="Two identical doors",
                subtitle="Default 10-cell corridor with doors at cells 2 and 6.",
                landmarks={"door": [2, 6]},
                true_position=6,
                scripted_events=[
                    {"kind": "sense", "landmark": "door", "present": True},
                    {"kind": "move", "direction": "right"},
                    {"kind": "sense", "landmark": "door", "present": False},
                ],
            ),
        ),
        UncertaintyExample(
            name="ambiguous_corridor",
            title="Ambiguous corridor",
            subtitle="Repeated landmark patterns keep belief split until a negative observation removes one hypothesis.",
            problem=make_problem(
                title="Ambiguous corridor",
                subtitle="Doors and signs repeat, so one observation is not enough.",
                cells=12,
                landmarks={"door": [3, 7, 11], "sign": [5, 9]},
                true_position=7,
                scripted_events=[
                    {"kind": "sense", "landmark": "door", "present": True},
                    {"kind": "move", "direction": "right"},
                    {"kind": "sense", "landmark": "sign", "present": False},
                    {"kind": "sense", "landmark": "door", "present": False},
                ],
            ),
        ),
        UncertaintyExample(
            name="bad_sensor",
            title="Bad sensor",
            subtitle="A weak sensor can make evidence barely useful or actively misleading.",
            problem=make_problem(
                title="Bad sensor",
                subtitle="The hit rate is no better than the false alarm rate.",
                landmarks={"door": [2, 6], "wall": [10]},
                true_position=6,
                sensor_hit=0.45,
                sensor_false_alarm=0.5,
                scripted_events=[
                    {"kind": "sense", "landmark": "door", "present": True},
                    {"kind": "sense", "landmark": "door", "present": True},
                    {"kind": "move", "direction": "right"},
                ],
            ),
        ),
        UncertaintyExample(
            name="slippery_floor",
            title="Slippery floor",
            subtitle="Uncertain actions spread probability mass even when the sensor is reliable.",
            problem=make_problem(
                title="Slippery floor",
                subtitle="Movement succeeds less often, so prediction remains broad.",
                landmarks={"door": [2, 6], "charger": [9]},
                true_position=2,
                motion_success=0.55,
                motion_stay=0.3,
                motion_overshoot=0.15,
                scripted_events=[
                    {"kind": "sense", "landmark": "door", "present": True},
                    {"kind": "move", "direction": "right"},
                    {"kind": "move", "direction": "right"},
                    {"kind": "sense", "landmark": "charger", "present": False},
                ],
            ),
        ),
        UncertaintyExample(
            name="confident_but_wrong",
            title="Confident but wrong",
            subtitle="A sharp prior and poor model can produce high confidence in the wrong cell.",
            problem=make_problem(
                title="Confident but wrong",
                subtitle="The prior starts sharply peaked away from the true position.",
                landmarks={"door": [2, 6], "sign": [4]},
                true_position=6,
                initial_belief=[0.03, 0.07, 0.05, 0.62, 0.08, 0.05, 0.04, 0.03, 0.02, 0.01],
                sensor_hit=0.62,
                sensor_false_alarm=0.32,
                motion_success=0.7,
                motion_stay=0.2,
                motion_overshoot=0.1,
                scripted_events=[
                    {"kind": "sense", "landmark": "sign", "present": True},
                    {"kind": "move", "direction": "right"},
                    {"kind": "sense", "landmark": "door", "present": True},
                ],
            ),
        ),
    ]
    return {example.name: example for example in examples}


def build_exercises() -> dict[str, UncertaintyExample]:
    base = make_problem(
        title="Bayes filter exercise",
        subtitle="Fill in the missing update rule and compare your result with the browser app.",
        landmarks={"door": [2, 4]},
        cells=5,
        true_position=None,
        show_true_position=False,
        scripted_events=[
            {"kind": "sense", "landmark": "door", "present": True},
            {"kind": "move", "direction": "right"},
            {"kind": "sense", "landmark": "door", "present": False},
        ],
    )
    exercises = [
        UncertaintyExample(
            name="normalise",
            title="Normalise a distribution",
            subtitle="Start by making probability values sum to 1.",
            problem=base,
        ),
        UncertaintyExample(
            name="sensor_update",
            title="Sensor update",
            subtitle="Use likelihoods to turn a prior into a posterior.",
            problem=base,
        ),
        UncertaintyExample(
            name="motion_update",
            title="Motion update",
            subtitle="Distribute probability mass with a noisy action model.",
            problem=base,
        ),
        UncertaintyExample(
            name="full_filter",
            title="Full Bayes filter",
            subtitle="Alternate prediction and correction over several steps.",
            problem=base,
        ),
        UncertaintyExample(
            name="bad_sensor",
            title="Bad sensor",
            subtitle="Diagnose what happens when likelihoods are not informative.",
            problem=make_problem(
                cells=5,
                landmarks={"door": [2, 4]},
                true_position=None,
                show_true_position=False,
                sensor_hit=0.5,
                sensor_false_alarm=0.5,
            ),
        ),
    ]
    return {exercise.name: exercise for exercise in exercises}


def make_problem(
    *,
    title: str = "Bayes Filter Corridor",
    subtitle: str = "Track a robot with noisy sensing and uncertain motion.",
    cells: int = 10,
    landmarks: dict[str, list[int]] | None = None,
    initial_belief: list[float] | None = None,
    true_position: int | None = 6,
    sensor_hit: float = 0.8,
    sensor_false_alarm: float = 0.2,
    motion_success: float = 0.8,
    motion_stay: float = 0.1,
    motion_overshoot: float = 0.1,
    show_true_position: bool = True,
    scripted_events: list[dict[str, object]] | None = None,
    random_seed: int = 7,
) -> CorridorProblem:
    return CorridorProblem(
        title=title,
        subtitle=subtitle,
        cells=cells,
        landmarks=to_zero_based_landmarks(landmarks or {"door": [2, 6]}, cells),
        initial_belief=initial_belief or [1.0 / cells for _ in range(cells)],
        initial_true_position=None if true_position is None else int(true_position) - 1,
        sensor_model=SensorModel(hit=sensor_hit, false_alarm=sensor_false_alarm),
        motion_model=MotionModel(
            success=motion_success,
            stay=motion_stay,
            overshoot=motion_overshoot,
        ),
        show_true_position=show_true_position,
        scripted_events=[
            dict(event)
            for event in (
                scripted_events
                if scripted_events is not None
                else [
                    {"kind": "sense", "landmark": "door", "present": True},
                    {"kind": "move", "direction": "right"},
                    {"kind": "sense", "landmark": "door", "present": False},
                ]
            )
        ],
        random_seed=random_seed,
    )


def to_zero_based_landmarks(landmarks: dict[str, list[int]], cells: int) -> dict[str, list[int]]:
    converted: dict[str, list[int]] = {}
    for name, indices in landmarks.items():
        converted[name] = [int(index) - 1 for index in indices]
    return converted
