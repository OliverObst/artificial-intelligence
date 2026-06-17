"""Trace and reference update helpers for the Bayes-filter corridor demo."""

from __future__ import annotations

import copy
import math
from typing import Any, Callable
from uuid import uuid4

from ai9414.core.models import TraceBundle, TraceStep, TraceSummary
from ai9414.uncertainty.models import CorridorProblem, MotionModel, SensorModel, UncertaintyExample

Belief = list[float]
NormaliseFn = Callable[[list[float]], list[float]]
SensorUpdateFn = Callable[[list[float], CorridorProblem, SensorModel, bool, str], list[float]]
MotionUpdateFn = Callable[[list[float], MotionModel], list[float]]

ALGORITHM_LABEL = "Bayes filter"
ALGORITHM_NOTE = (
    "A Bayes filter keeps a whole probability distribution over possible states. "
    "Sensor updates usually concentrate belief; uncertain motion usually spreads it."
)
SENSOR_WARNING = (
    "This sensor is not informative. It is no better than, or worse than, a false alarm model."
)


def build_uncertainty_trace(
    example: UncertaintyExample,
    *,
    events: list[dict[str, Any]] | None = None,
) -> TraceBundle:
    return build_uncertainty_trace_from_problem(
        example.problem,
        title=example.title,
        subtitle=example.subtitle,
        events=events,
    )


def build_uncertainty_trace_from_problem(
    problem: CorridorProblem,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    events: list[dict[str, Any]] | None = None,
    normalise_fn: NormaliseFn | None = None,
    sensor_update_fn: SensorUpdateFn | None = None,
    motion_update_right_fn: MotionUpdateFn | None = None,
    trace_id: str | None = None,
) -> TraceBundle:
    operations = [dict(event) for event in (problem.scripted_events if events is None else events)]
    belief = validate_belief(problem.initial_belief, problem.cells, function_name="initial_belief")
    true_position = problem.initial_true_position
    active_sensor = problem.sensor_model
    active_motion = problem.motion_model
    history = [reset_history_entry(problem, belief)]

    initial_snapshot = build_snapshot(
        problem,
        prior=belief,
        predicted=belief,
        likelihoods=[1.0 for _ in belief],
        unnormalised=belief,
        posterior=belief,
        normalisation_constant=1.0,
        current_operation="reset",
        current_action=None,
        current_observation=None,
        true_position=true_position,
        step_index=0,
        total_steps=len(operations),
        history=history,
        sensor_model=active_sensor,
        motion_model=active_motion,
        transition_rows=[],
        explanation={
            "title": "Initial belief",
            "formula": "P(location = x)",
            "body": "The robot starts with a prior belief distribution over corridor cells.",
        },
        status="ready",
    )
    initial_state = {
        "example_title": title or problem.title,
        "example_subtitle": subtitle or problem.subtitle,
        "algorithm_label": ALGORITHM_LABEL,
        "algorithm_note": ALGORITHM_NOTE,
        "uncertainty_problem": problem.model_dump(),
        "playback_speed": 1.0,
        "live_python": {"backend_url": "http://127.0.0.1:9414/solve"},
        **initial_snapshot,
    }

    steps: list[TraceStep] = []
    for step_index, operation in enumerate(operations, start=1):
        result = apply_operation(
            problem,
            belief,
            true_position,
            operation,
            normalise_fn=normalise_fn,
            sensor_update_fn=sensor_update_fn,
            motion_update_right_fn=motion_update_right_fn,
            sensor_model=active_sensor,
            motion_model=active_motion,
        )
        active_sensor = result["sensor_model"]
        active_motion = result["motion_model"]
        belief = result["posterior"]
        true_position = result["true_position"]
        history.append(
            build_history_entry(
                step_index=step_index,
                operation=operation,
                label=result["label"],
                summary=result["annotation"],
                before=result["prior"],
                after=result["posterior"],
                true_position=true_position,
                sensor_model=active_sensor,
                motion_model=active_motion,
            )
        )
        snapshot = build_snapshot(
            problem,
            prior=result["prior"],
            predicted=result["predicted"],
            likelihoods=result["likelihoods"],
            unnormalised=result["unnormalised"],
            posterior=result["posterior"],
            normalisation_constant=result["normalisation_constant"],
            current_operation=result["operation_name"],
            current_action=result["current_action"],
            current_observation=result["current_observation"],
            true_position=true_position,
            step_index=step_index,
            total_steps=len(operations),
            history=history,
            sensor_model=active_sensor,
            motion_model=active_motion,
            transition_rows=result["transition_rows"],
            explanation=result["explanation"],
            status="tracking",
        )
        steps.append(
            TraceStep(
                index=len(steps),
                event_type=result["event_type"],
                label=result["label"],
                annotation=result["annotation"],
                teaching_note=result["teaching_note"],
                state_patch=snapshot,
            )
        )

    return TraceBundle(
        app_type="uncertainty",
        trace_id=trace_id or f"uncertainty-{uuid4().hex[:8]}",
        is_complete=True,
        initial_state=initial_state,
        summary=TraceSummary(step_count=len(steps), result="ready" if not steps else "posterior ready"),
        steps=steps,
    )


def apply_operation(
    problem: CorridorProblem,
    belief: Belief,
    true_position: int | None,
    operation: dict[str, Any],
    *,
    normalise_fn: NormaliseFn | None = None,
    sensor_update_fn: SensorUpdateFn | None = None,
    motion_update_right_fn: MotionUpdateFn | None = None,
    sensor_model: SensorModel | None = None,
    motion_model: MotionModel | None = None,
) -> dict[str, Any]:
    kind = str(operation.get("kind") or operation.get("command") or "").strip().lower()
    active_sensor = SensorModel.model_validate(operation.get("sensor_model") or sensor_model or problem.sensor_model)
    active_motion = MotionModel.model_validate(operation.get("motion_model") or motion_model or problem.motion_model)
    prior = validate_belief(belief, problem.cells, function_name="prior belief")

    if kind == "sense":
        landmark = str(operation.get("landmark") or "door")
        present = bool(operation.get("present", True))
        likelihoods, unnormalised, normalisation_constant = compute_sensor_terms(
            problem,
            prior,
            active_sensor,
            landmark,
            present,
        )
        if sensor_update_fn is None:
            posterior = reference_sensor_update(prior, problem, active_sensor, present, landmark)
        else:
            posterior = sensor_update_fn(copy.deepcopy(prior), problem, active_sensor, present, landmark)
        if normalise_fn is not None:
            posterior = normalise_fn([value * 1.0 for value in posterior])
        posterior = validate_belief(posterior, problem.cells, function_name="sensor_update")
        expected = reference_normalise(unnormalised)
        if not beliefs_close(posterior, expected):
            raise ValueError("sensor_update returned a distribution that does not match the Bayes sensor update.")
        label = f"Sense {'no ' if not present else ''}{format_landmark(landmark)}"
        annotation = sensor_annotation(problem, posterior, landmark, present)
        return {
            "event_type": "sensor_update",
            "operation_name": "sensor_update",
            "label": label,
            "annotation": annotation,
            "teaching_note": "Multiply the prior by the observation likelihood, then normalise.",
            "prior": prior,
            "predicted": prior,
            "likelihoods": likelihoods,
            "unnormalised": unnormalised,
            "normalisation_constant": normalisation_constant,
            "posterior": posterior,
            "true_position": true_position,
            "current_action": None,
            "current_observation": f"{'no_' if not present else ''}{landmark}",
            "transition_rows": [],
            "sensor_model": active_sensor,
            "motion_model": active_motion,
            "explanation": sensor_explanation(problem, active_sensor, landmark, present),
        }

    if kind == "move":
        direction = str(operation.get("direction") or "right").strip().lower()
        if direction not in {"left", "right", "stay"}:
            raise ValueError("Move direction must be 'left', 'right', or 'stay'.")
        posterior, transition_rows = reference_motion_update(
            prior,
            active_motion,
            direction=direction,
            return_rows=True,
        )
        if motion_update_right_fn is not None and direction == "right":
            student_posterior = motion_update_right_fn(copy.deepcopy(prior), active_motion)
            student_posterior = validate_belief(
                student_posterior,
                problem.cells,
                function_name="motion_update_right",
            )
            if not beliefs_close(student_posterior, posterior):
                raise ValueError("motion_update_right returned a distribution that does not match the reference update.")
        posterior = validate_belief(posterior, problem.cells, function_name="motion_update")
        new_true_position = operation.get("true_position")
        if new_true_position is None:
            new_true_position = simulate_true_motion(
                true_position,
                active_motion,
                direction,
                cells=problem.cells,
            )
        label = f"Move {direction}"
        annotation = motion_annotation(posterior, direction)
        return {
            "event_type": "motion_update",
            "operation_name": "motion_update",
            "label": label,
            "annotation": annotation,
            "teaching_note": "The action model redistributes probability mass before the next observation.",
            "prior": prior,
            "predicted": posterior,
            "likelihoods": [1.0 for _ in prior],
            "unnormalised": posterior,
            "normalisation_constant": sum(posterior),
            "posterior": posterior,
            "true_position": None if new_true_position is None else int(new_true_position),
            "current_action": f"move_{direction}",
            "current_observation": None,
            "transition_rows": transition_rows,
            "sensor_model": active_sensor,
            "motion_model": active_motion,
            "explanation": motion_explanation(active_motion, direction),
        }

    if kind == "reset_belief":
        posterior = list(problem.initial_belief)
        return neutral_operation_result(
            problem,
            prior=prior,
            posterior=posterior,
            true_position=true_position,
            sensor_model=active_sensor,
            motion_model=active_motion,
            operation_name="reset_belief",
            label="Reset belief to uniform",
            annotation="The belief distribution has been reset to the initial prior.",
        )

    if kind in {"reset_true_position", "randomise_true_position"}:
        next_true = operation.get("true_position", problem.initial_true_position)
        return neutral_operation_result(
            problem,
            prior=prior,
            posterior=prior,
            true_position=None if next_true is None else int(next_true),
            sensor_model=active_sensor,
            motion_model=active_motion,
            operation_name=kind,
            label="Reset true position" if kind == "reset_true_position" else "Randomise true position",
            annotation="The hidden true position changed, but the robot's belief did not.",
        )

    if kind == "set_sensor_model":
        return neutral_operation_result(
            problem,
            prior=prior,
            posterior=prior,
            true_position=true_position,
            sensor_model=active_sensor,
            motion_model=active_motion,
            operation_name="set_sensor_model",
            label="Update sensor model",
            annotation="Future sensor updates will use the new likelihood parameters.",
        )

    if kind == "set_motion_model":
        return neutral_operation_result(
            problem,
            prior=prior,
            posterior=prior,
            true_position=true_position,
            sensor_model=active_sensor,
            motion_model=active_motion,
            operation_name="set_motion_model",
            label="Update motion model",
            annotation="Future motion updates will use the new transition parameters.",
        )

    raise ValueError(f"Unsupported uncertainty operation '{kind}'.")


def neutral_operation_result(
    problem: CorridorProblem,
    *,
    prior: Belief,
    posterior: Belief,
    true_position: int | None,
    sensor_model: SensorModel,
    motion_model: MotionModel,
    operation_name: str,
    label: str,
    annotation: str,
) -> dict[str, Any]:
    return {
        "event_type": operation_name,
        "operation_name": operation_name,
        "label": label,
        "annotation": annotation,
        "teaching_note": "This operation changes the demo state without applying a Bayes update.",
        "prior": list(prior),
        "predicted": list(posterior),
        "likelihoods": [1.0 for _ in posterior],
        "unnormalised": list(posterior),
        "normalisation_constant": sum(posterior),
        "posterior": list(posterior),
        "true_position": true_position,
        "current_action": None,
        "current_observation": None,
        "transition_rows": [],
        "sensor_model": sensor_model,
        "motion_model": motion_model,
        "explanation": {
            "title": label,
            "formula": "Belief remains normalised.",
            "body": annotation,
        },
    }


def reference_normalise(values: list[float]) -> list[float]:
    total = sum(float(value) for value in values)
    if total <= 0.0:
        raise ValueError("Cannot normalise values whose total is zero.")
    return [float(value) / total for value in values]


def reference_sensor_update(
    belief: Belief,
    corridor: CorridorProblem,
    sensor: SensorModel,
    sees_landmark: bool,
    landmark: str = "door",
) -> Belief:
    _, unnormalised, _ = compute_sensor_terms(corridor, belief, sensor, landmark, sees_landmark)
    return reference_normalise(unnormalised)


def reference_motion_update(
    belief: Belief,
    motion: MotionModel,
    *,
    direction: str = "right",
    return_rows: bool = False,
) -> Belief | tuple[Belief, list[dict[str, Any]]]:
    cells = len(belief)
    next_belief = [0.0 for _ in range(cells)]
    rows: list[dict[str, Any]] = []
    for source, probability in enumerate(belief):
        entries = motion_entries(source, motion, direction, cells)
        for entry in entries:
            next_belief[entry["destination_index"]] += probability * entry["probability"]
        rows.append(
            {
                "source_index": source,
                "source_cell": source + 1,
                "entries": [
                    {
                        "destination_index": entry["destination_index"],
                        "destination_cell": entry["destination_index"] + 1,
                        "probability": entry["probability"],
                        "label": entry["label"],
                        "mass": probability * entry["probability"],
                    }
                    for entry in entries
                ],
            }
        )
    next_belief = validate_belief(next_belief, cells, function_name="motion_update")
    if return_rows:
        return next_belief, rows
    return next_belief


def reference_motion_update_right(belief: Belief, motion: MotionModel) -> Belief:
    return reference_motion_update(belief, motion, direction="right")  # type: ignore[return-value]


def compute_sensor_terms(
    problem: CorridorProblem,
    belief: Belief,
    sensor: SensorModel,
    landmark: str,
    present: bool,
) -> tuple[list[float], list[float], float]:
    landmark_cells = set(problem.landmarks.get(landmark, []))
    likelihoods: list[float] = []
    for index in range(problem.cells):
        has_landmark = index in landmark_cells
        if has_landmark:
            likelihood = sensor.hit if present else 1.0 - sensor.hit
        else:
            likelihood = sensor.false_alarm if present else 1.0 - sensor.false_alarm
        likelihoods.append(float(likelihood))
    unnormalised = [float(probability) * likelihood for probability, likelihood in zip(belief, likelihoods)]
    normalisation_constant = sum(unnormalised)
    return likelihoods, unnormalised, normalisation_constant


def motion_entries(source: int, motion: MotionModel, direction: str, cells: int) -> list[dict[str, Any]]:
    if direction == "stay":
        return [{"destination_index": source, "probability": 1.0, "label": "stay"}]

    sign = 1 if direction == "right" else -1
    raw_entries = [
        (source + sign, motion.success, "success"),
        (source, motion.stay, "stay"),
        (source + 2 * sign, motion.overshoot, "overshoot"),
    ]
    merged: dict[int, dict[str, Any]] = {}
    for destination, probability, label in raw_entries:
        clamped = clamp(destination, 0, cells - 1)
        if clamped not in merged:
            merged[clamped] = {"destination_index": clamped, "probability": 0.0, "label": label}
        merged[clamped]["probability"] += float(probability)
        if merged[clamped]["label"] != label:
            merged[clamped]["label"] = "boundary clamp"
    return list(merged.values())


def simulate_true_motion(
    true_position: int | None,
    motion: MotionModel,
    direction: str,
    *,
    cells: int,
) -> int | None:
    if true_position is None:
        return None
    entries = motion_entries(true_position, motion, direction, cells)
    best = max(entries, key=lambda entry: (entry["probability"], -abs(entry["destination_index"] - true_position)))
    return int(best["destination_index"])


def validate_belief(belief: list[float], cells: int, *, function_name: str) -> Belief:
    if not isinstance(belief, list):
        raise ValueError(f"{function_name} must return a list of probabilities.")
    if len(belief) != cells:
        raise ValueError(f"{function_name} must return exactly {cells} probabilities.")
    cleaned = [float(value) for value in belief]
    if any(value < -1e-9 for value in cleaned):
        raise ValueError(f"{function_name} returned a negative probability.")
    cleaned = [0.0 if abs(value) < 1e-12 else value for value in cleaned]
    total = sum(cleaned)
    if total <= 0:
        raise ValueError(f"{function_name} must assign positive probability mass.")
    if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        raise ValueError(f"{function_name} must return a normalised belief distribution that sums to 1.")
    return cleaned


def beliefs_close(left: Belief, right: Belief, *, tolerance: float = 1e-6) -> bool:
    return len(left) == len(right) and all(
        math.isclose(left[index], right[index], rel_tol=tolerance, abs_tol=tolerance)
        for index in range(len(left))
    )


def build_snapshot(
    problem: CorridorProblem,
    *,
    prior: Belief,
    predicted: Belief,
    likelihoods: Belief,
    unnormalised: Belief,
    posterior: Belief,
    normalisation_constant: float,
    current_operation: str,
    current_action: str | None,
    current_observation: str | None,
    true_position: int | None,
    step_index: int,
    total_steps: int,
    history: list[dict[str, Any]],
    sensor_model: SensorModel,
    motion_model: MotionModel,
    transition_rows: list[dict[str, Any]],
    explanation: dict[str, str],
    status: str,
) -> dict[str, Any]:
    rows = build_cell_rows(problem, prior, predicted, likelihoods, unnormalised, posterior, true_position)
    most_likely_index = max(range(len(posterior)), key=lambda index: posterior[index])
    entropy = belief_entropy(posterior)
    total_probability = sum(posterior)
    warning = ""
    if not sensor_model.informative:
        warning = SENSOR_WARNING
    elif not math.isclose(total_probability, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        warning = "Warning: belief does not sum to 1. Check the update rule."
    return {
        "search": {
            "status": status,
            "result": status,
            "finished": True,
        },
        "stats": {
            "step_index": step_index,
            "max_belief": float(posterior[most_likely_index]),
            "entropy": entropy,
            "normalisation_constant": float(normalisation_constant),
            "total_probability": float(total_probability),
        },
        "uncertainty": {
            "app_kind": "bayes_filter_corridor",
            "step_index": step_index,
            "total_steps": total_steps,
            "cell_count": problem.cells,
            "cells": rows,
            "landmarks": copy.deepcopy(problem.landmarks),
            "landmark_types": problem.landmark_types,
            "current_operation": current_operation,
            "current_action": current_action,
            "current_observation": current_observation,
            "current_true_position": true_position,
            "show_true_position": problem.show_true_position,
            "prior_belief": list(prior),
            "predicted_belief": list(predicted),
            "observation_likelihoods": list(likelihoods),
            "unnormalised_posterior": list(unnormalised),
            "posterior_belief": list(posterior),
            "belief_rows": rows,
            "operation_table": rows,
            "transition_rows": transition_rows,
            "history": copy.deepcopy(history),
            "most_likely_index": most_likely_index,
            "most_likely_cell": most_likely_index + 1,
            "most_likely_label": f"Cell {most_likely_index + 1}",
            "most_likely_probability": float(posterior[most_likely_index]),
            "weak_maximum": posterior[most_likely_index] < 0.5,
            "normalisation_constant": float(normalisation_constant),
            "total_probability": float(total_probability),
            "sensor_model": sensor_model.model_dump(),
            "motion_model": motion_model.model_dump(),
            "warning": warning,
            "explanation": explanation,
        },
    }


def build_cell_rows(
    problem: CorridorProblem,
    prior: Belief,
    predicted: Belief,
    likelihoods: Belief,
    unnormalised: Belief,
    posterior: Belief,
    true_position: int | None,
) -> list[dict[str, Any]]:
    most_likely_index = max(range(len(posterior)), key=lambda index: posterior[index])
    rows = []
    for index in range(problem.cells):
        landmarks = [name for name, indices in problem.landmarks.items() if index in indices]
        rows.append(
            {
                "index": index,
                "cell": index + 1,
                "label": f"Cell {index + 1}",
                "landmarks": landmarks,
                "landmark_label": ", ".join(format_landmark(name) for name in landmarks) or "none",
                "prior": float(prior[index]),
                "predicted": float(predicted[index]),
                "likelihood": float(likelihoods[index]),
                "unnormalised": float(unnormalised[index]),
                "posterior": float(posterior[index]),
                "is_true_position": true_position == index,
                "is_most_likely": most_likely_index == index,
            }
        )
    return rows


def reset_history_entry(problem: CorridorProblem, belief: Belief) -> dict[str, Any]:
    return {
        "step_index": 0,
        "label": "Reset",
        "summary": "Uniform belief" if is_uniform(belief) else "Initial belief",
        "operation": "reset",
        "belief_before": list(belief),
        "belief_after": list(belief),
        "most_likely_cell": max(range(problem.cells), key=lambda index: belief[index]) + 1,
        "most_likely_probability": max(belief),
        "true_position": problem.initial_true_position,
    }


def build_history_entry(
    *,
    step_index: int,
    operation: dict[str, Any],
    label: str,
    summary: str,
    before: Belief,
    after: Belief,
    true_position: int | None,
    sensor_model: SensorModel,
    motion_model: MotionModel,
) -> dict[str, Any]:
    most_likely_index = max(range(len(after)), key=lambda index: after[index])
    return {
        "step_index": step_index,
        "label": label,
        "summary": summary,
        "operation": copy.deepcopy(operation),
        "belief_before": list(before),
        "belief_after": list(after),
        "most_likely_cell": most_likely_index + 1,
        "most_likely_probability": float(after[most_likely_index]),
        "true_position": true_position,
        "sensor_model": sensor_model.model_dump(),
        "motion_model": motion_model.model_dump(),
    }


def sensor_explanation(
    problem: CorridorProblem,
    sensor: SensorModel,
    landmark: str,
    present: bool,
) -> dict[str, str]:
    landmark_label = format_landmark(landmark)
    observed = landmark_label if present else f"no {landmark_label}"
    return {
        "title": "Sensor update",
        "formula": f"new_belief(x) proportional to P(sees_{landmark} | x) times old_belief(x)",
        "body": (
            f"The robot observed {observed}. Cells with {landmark_label} receive likelihood "
            f"{sensor.hit:.2f} when the landmark is seen and {1.0 - sensor.hit:.2f} when it is not. "
            f"Other cells use the false alarm model {sensor.false_alarm:.2f} or {1.0 - sensor.false_alarm:.2f}."
        ),
    }


def motion_explanation(motion: MotionModel, direction: str) -> dict[str, str]:
    if direction == "stay":
        return {
            "title": "Motion update",
            "formula": "new_belief(x) = old_belief(x)",
            "body": "The robot stayed still, so probability mass remains in the same cells.",
        }
    return {
        "title": "Motion update",
        "formula": "new_belief(x') = sum_x P(x' | action, x) old_belief(x)",
        "body": (
            f"The robot intended to move {direction}. From each old cell, {motion.success:.2f} of the mass "
            f"moves one cell, {motion.stay:.2f} stays in place, and {motion.overshoot:.2f} moves one extra cell. "
            "Movement beyond the corridor boundary is clamped."
        ),
    }


def sensor_annotation(problem: CorridorProblem, posterior: Belief, landmark: str, present: bool) -> str:
    top_cells = top_cell_labels(posterior, limit=2)
    verb = "seen" if present else "not seen"
    return f"{format_landmark(landmark).title()} was {verb}; belief now favours {top_cells}."


def motion_annotation(posterior: Belief, direction: str) -> str:
    top_cells = top_cell_labels(posterior, limit=2)
    if direction == "stay":
        return f"Staying keeps the belief in place; the leading cells are {top_cells}."
    return f"The move {direction} shifted and spread belief; the leading cells are {top_cells}."


def top_cell_labels(belief: Belief, *, limit: int = 2) -> str:
    ordered = sorted(range(len(belief)), key=lambda index: belief[index], reverse=True)[:limit]
    return " and ".join(f"cell {index + 1} (P = {belief[index]:.2f})" for index in ordered)


def format_landmark(landmark: str) -> str:
    return str(landmark).replace("_", " ")


def is_uniform(belief: Belief) -> bool:
    return bool(belief) and all(math.isclose(value, belief[0], abs_tol=1e-9) for value in belief)


def belief_entropy(belief: Belief) -> float:
    entropy = 0.0
    for probability in belief:
        if probability > 0:
            entropy -= probability * math.log2(probability)
    return entropy


def clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(value, upper))


def final_runtime_state(problem: CorridorProblem, events: list[dict[str, Any]]) -> tuple[Belief, int | None]:
    belief = list(problem.initial_belief)
    true_position = problem.initial_true_position
    sensor_model = problem.sensor_model
    motion_model = problem.motion_model
    for event in events:
        result = apply_operation(
            problem,
            belief,
            true_position,
            event,
            sensor_model=sensor_model,
            motion_model=motion_model,
        )
        belief = result["posterior"]
        true_position = result["true_position"]
        sensor_model = result["sensor_model"]
        motion_model = result["motion_model"]
    return belief, true_position

