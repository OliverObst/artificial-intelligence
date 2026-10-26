"""
Week 7: Reasoning with uncertainty
Bayes filter corridor exercise

This file asks you to implement the two main operations used by a simple
Bayes filter:

1. sensor_update:
   Use noisy evidence to update a belief distribution.

2. motion_update:
   Use an uncertain action model to predict the next belief distribution.

The belief is a list of probabilities, one per corridor cell.
The probabilities should always sum to 1.

Run this file to start the live browser solver on port 9414.
Use --demo for the standalone five-cell example or --check for local checks.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass


@dataclass
class Corridor:
    cells: int
    door_cells: set[int]


@dataclass
class SensorModel:
    hit: float = 0.8
    false_alarm: float = 0.2


@dataclass
class MotionModel:
    success: float = 0.8
    stay: float = 0.1
    overshoot: float = 0.1


def normalise(values: list[float]) -> list[float]:
    """
    Return a new list whose values sum to 1.

    TODO:
    - compute the total
    - raise ValueError if the total is zero
    - divide each value by the total
    """
    raise NotImplementedError("Implement normalise in week7_bayes_filter_stub.py first.")


def sensor_update(
    belief: list[float],
    corridor: Corridor,
    sensor: SensorModel,
    sees_door: bool,
) -> list[float]:
    """
    Update belief after observing whether the robot sees a door.

    If the robot is at a door cell:
        P(sees_door=True) = sensor.hit

    If the robot is not at a door cell:
        P(sees_door=True) = sensor.false_alarm

    TODO:
    - for each cell, compute the likelihood of the observation
    - multiply the old belief by that likelihood
    - normalise the result
    """
    raise NotImplementedError("Implement sensor_update in week7_bayes_filter_stub.py first.")


def motion_update_right(
    belief: list[float],
    motion: MotionModel,
) -> list[float]:
    """
    Predict the next belief after the robot tries to move right.

    The motion model is:

    - success:   move one cell right
    - stay:      remain in the same cell
    - overshoot: move two cells right

    At the end of the corridor, clamp movement to the last cell.

    TODO:
    - create a new belief list filled with zeros
    - distribute probability mass from each old cell
    - return the new belief
    """
    raise NotImplementedError("Implement motion_update_right in week7_bayes_filter_stub.py first.")


def most_likely_cell(belief: list[float]) -> int:
    """
    Return the first 1-based maximum; use most_likely_cells to keep ties.
    """
    return max(range(len(belief)), key=lambda i: belief[i]) + 1


def most_likely_cells(belief: list[float]) -> list[int]:
    peak = max(belief)
    return [i + 1 for i, value in enumerate(belief) if math.isclose(value, peak)]


def assert_close(a: float, b: float, eps: float = 1e-6) -> None:
    assert abs(a - b) < eps, f"{a} != {b}"


def run_checks() -> None:
    corridor = Corridor(cells=5, door_cells={1, 3})
    sensor = SensorModel(hit=0.8, false_alarm=0.2)
    motion = MotionModel(success=0.8, stay=0.1, overshoot=0.1)

    belief = [0.2] * 5
    updated = sensor_update(belief, corridor, sensor, sees_door=True)

    assert_close(sum(updated), 1.0)

    expected = [
        0.04 / 0.44,
        0.16 / 0.44,
        0.04 / 0.44,
        0.16 / 0.44,
        0.04 / 0.44,
    ]

    for got, exp in zip(updated, expected, strict=True):
        assert_close(got, exp)

    moved = motion_update_right(updated, motion)
    assert_close(sum(moved), 1.0)

    expected_motion = [1 / 110, 12 / 110, 34 / 110, 16 / 110, 47 / 110]
    for got, exp in zip(moved, expected_motion, strict=True):
        assert_close(got, exp)

    final = sensor_update(moved, corridor, sensor, sees_door=False)
    expected_final = [1 / 89, 3 / 89, 34 / 89, 4 / 89, 47 / 89]
    for got, exp in zip(final, expected_final, strict=True):
        assert_close(got, exp)

    for got, exp in zip(normalise([1, 2, 1]), [0.25, 0.5, 0.25], strict=True):
        assert_close(got, exp)
    try:
        normalise([0.0, 0.0])
    except ValueError:
        pass
    else:
        raise AssertionError("normalise must reject a zero total.")

    print("All checks passed.")


def run_demo() -> None:
    corridor = Corridor(cells=5, door_cells={1, 3})  # cells 2 and 4
    sensor = SensorModel(hit=0.8, false_alarm=0.2)
    motion = MotionModel(success=0.8, stay=0.1, overshoot=0.1)

    belief = [1 / corridor.cells] * corridor.cells

    print("Initial belief:")
    print(belief)

    belief = sensor_update(belief, corridor, sensor, sees_door=True)
    print("\nAfter sensing a door:")
    print(belief)
    print("Most likely cells:", most_likely_cells(belief))

    belief = motion_update_right(belief, motion)
    print("\nAfter moving right:")
    print(belief)
    print("Most likely cells:", most_likely_cells(belief))

    belief = sensor_update(belief, corridor, sensor, sees_door=False)
    print("\nAfter sensing no door:")
    print(belief)
    print("Most likely cells:", most_likely_cells(belief))


def sensor_update_for_browser(belief, problem, sensor, sees_landmark, landmark="door"):
    """Adapt the browser's selected landmark to the four-argument exercise."""
    corridor = Corridor(cells=problem.cells, door_cells=set(problem.landmarks.get(landmark, [])))
    return sensor_update(belief, corridor, sensor, sees_landmark)


def run_live(port: int = 9414) -> None:
    from ai9414.uncertainty import run_uncertainty_solver

    run_uncertainty_solver(
        normalise_fn=normalise,
        sensor_update_fn=sensor_update_for_browser,
        motion_update_right_fn=motion_update_right,
        port=port,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Week 7 Bayes-filter exercise")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true", help="Run the standalone five-cell example")
    mode.add_argument("--check", action="store_true", help="Check the three implemented functions")
    parser.add_argument("--port", type=int, default=9414, help="Live solver port (default: 9414)")
    args = parser.parse_args()
    if args.demo:
        run_demo()
    elif args.check:
        run_checks()
    else:
        run_live(args.port)


if __name__ == "__main__":
    main()
