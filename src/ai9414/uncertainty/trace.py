"""Trace construction helpers for the reasoning-with-uncertainty demo."""

from __future__ import annotations

import copy
import math
from typing import Callable

from ai9414.core.models import TraceBundle, TraceStep, TraceSummary
from ai9414.uncertainty.models import UncertaintyExample, UncertaintyProblem

Belief = dict[str, float]
TransitionModel = dict[str, dict[str, float]]
ObservationModel = dict[str, dict[str, float]]
PredictFn = Callable[[Belief, TransitionModel], Belief]
UpdateFn = Callable[[Belief, str, ObservationModel], Belief]
StepFn = Callable[[Belief, TransitionModel, str, ObservationModel], Belief]

ALGORITHM_LABEL = "Bayes filter"
ALGORITHM_NOTE = (
    "A Bayes filter keeps a probability distribution over possible locations. "
    "Each step first predicts with the action model, then corrects with the observation model."
)


def build_uncertainty_trace(example: UncertaintyExample) -> TraceBundle:
    return build_uncertainty_trace_from_problem(
        example.problem,
        title=example.title,
        subtitle=example.subtitle,
    )


def build_uncertainty_trace_from_problem(
    problem: UncertaintyProblem,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    predict_fn: PredictFn | None = None,
    update_fn: UpdateFn | None = None,
    bayes_step_fn: StepFn | None = None,
    trace_id: str = "uncertainty-trace",
) -> TraceBundle:
    predict = predict_fn or reference_predict_belief
    update = update_fn or reference_update_belief
    bayes_step = bayes_step_fn or reference_bayes_filter_step

    room_ids = [room.id for room in problem.rooms]
    initial_belief = validate_belief_distribution(
        problem.initial_belief,
        room_ids,
        function_name="initial belief",
    )
    initial_snapshot = build_uncertainty_snapshot(
        problem,
        prior=initial_belief,
        predicted=initial_belief,
        observation_likelihoods={room_id: 1.0 for room_id in room_ids},
        unnormalised=initial_belief,
        posterior=initial_belief,
        normalisation_constant=1.0,
        current_action=None,
        current_observation=None,
        true_location=problem.initial_true_location,
        step_index=0,
        history=[],
        status="ready",
    )
    initial_state_payload = {
        "example_title": title or problem.title,
        "example_subtitle": subtitle or problem.subtitle,
        "algorithm_label": ALGORITHM_LABEL,
        "algorithm_note": ALGORITHM_NOTE,
        "uncertainty_problem": problem.model_dump(),
        "playback_speed": 1.0,
        **initial_snapshot,
    }

    steps: list[TraceStep] = []
    belief = initial_belief
    history: list[dict[str, object]] = []
    total_steps = len(problem.scripted_steps)

    for step_index, scenario_step in enumerate(problem.scripted_steps, start=1):
        transition_model = problem.transition_models[scenario_step.action]
        predicted = validate_belief_distribution(
            predict(copy.deepcopy(belief), copy.deepcopy(transition_model)),
            room_ids,
            function_name="predict_belief",
        )
        observation_likelihoods, unnormalised, normalisation_constant = compute_observation_terms(
            predicted,
            scenario_step.observation,
            problem.observation_model,
        )
        posterior = validate_belief_distribution(
            update(copy.deepcopy(predicted), scenario_step.observation, copy.deepcopy(problem.observation_model)),
            room_ids,
            function_name="update_belief",
        )
        combined = validate_belief_distribution(
            bayes_step(
                copy.deepcopy(belief),
                copy.deepcopy(transition_model),
                scenario_step.observation,
                copy.deepcopy(problem.observation_model),
            ),
            room_ids,
            function_name="bayes_filter_step",
        )
        if not beliefs_close(combined, posterior):
            raise ValueError(
                "bayes_filter_step must match the posterior returned by update_belief(predict_belief(...))."
            )

        most_likely_location = max(posterior, key=posterior.get)
        history.append(
            {
                "step_index": step_index,
                "action": scenario_step.action,
                "observation": scenario_step.observation,
                "true_location": scenario_step.true_location,
                "most_likely_location": most_likely_location,
                "most_likely_probability": posterior[most_likely_location],
                "note": scenario_step.note,
            }
        )
        snapshot = build_uncertainty_snapshot(
            problem,
            prior=belief,
            predicted=predicted,
            observation_likelihoods=observation_likelihoods,
            unnormalised=unnormalised,
            posterior=posterior,
            normalisation_constant=normalisation_constant,
            current_action=scenario_step.action,
            current_observation=scenario_step.observation,
            true_location=scenario_step.true_location,
            step_index=step_index,
            history=history,
            status="tracking" if step_index < total_steps else "posterior ready",
        )
        steps.append(
            TraceStep(
                index=len(steps),
                event_type="bayes_update",
                label=f"{format_action_label(scenario_step.action)} + {format_observation_label(scenario_step.observation)}",
                annotation=build_step_annotation(
                    prior=belief,
                    posterior=posterior,
                    action=scenario_step.action,
                    observation=scenario_step.observation,
                ),
                teaching_note=(
                    "Prediction uses the transition model; correction multiplies by the observation likelihoods and then normalises."
                ),
                state_patch=snapshot,
            )
        )
        belief = posterior

    return TraceBundle(
        app_type="uncertainty",
        trace_id=trace_id,
        is_complete=True,
        initial_state=initial_state_payload,
        summary=TraceSummary(step_count=len(steps), result="posterior ready"),
        steps=steps,
    )


def reference_predict_belief(belief: Belief, transition_model: TransitionModel) -> Belief:
    predicted = {destination: 0.0 for destination in next(iter(transition_model.values())).keys()}
    for source, source_probability in belief.items():
        for destination, transition_probability in transition_model[source].items():
            predicted[destination] += float(source_probability) * float(transition_probability)
    return predicted


def reference_update_belief(
    predicted_belief: Belief,
    observation: str,
    observation_model: ObservationModel,
) -> Belief:
    _, unnormalised, normalisation_constant = compute_observation_terms(
        predicted_belief,
        observation,
        observation_model,
    )
    if normalisation_constant <= 0:
        raise ValueError("Observation likelihoods sum to zero, so the posterior cannot be normalised.")
    return {
        location: value / normalisation_constant for location, value in unnormalised.items()
    }


def reference_bayes_filter_step(
    belief: Belief,
    transition_model: TransitionModel,
    observation: str,
    observation_model: ObservationModel,
) -> Belief:
    predicted = reference_predict_belief(belief, transition_model)
    return reference_update_belief(predicted, observation, observation_model)


def compute_observation_terms(
    predicted_belief: Belief,
    observation: str,
    observation_model: ObservationModel,
) -> tuple[dict[str, float], dict[str, float], float]:
    likelihoods = {
        location: float(observation_model[location][observation])
        for location in predicted_belief
    }
    unnormalised = {
        location: float(predicted_belief[location]) * likelihoods[location]
        for location in predicted_belief
    }
    normalisation_constant = sum(unnormalised.values())
    return likelihoods, unnormalised, normalisation_constant


def validate_belief_distribution(
    belief: Belief,
    room_ids: list[str],
    *,
    function_name: str,
) -> Belief:
    if not isinstance(belief, dict):
        raise ValueError(f"{function_name} must return a dictionary mapping rooms to probabilities.")
    if set(belief) != set(room_ids):
        raise ValueError(f"{function_name} must return every room exactly once.")

    validated: dict[str, float] = {}
    for room_id in room_ids:
        value = belief[room_id]
        if not isinstance(value, (int, float)):
            raise ValueError(f"{function_name} must return numeric probabilities.")
        value = float(value)
        if value < -1e-9:
            raise ValueError(f"{function_name} returned a negative probability for '{room_id}'.")
        validated[room_id] = 0.0 if abs(value) < 1e-12 else value

    total = sum(validated.values())
    if total <= 0:
        raise ValueError(f"{function_name} must assign positive mass to at least one room.")
    if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        raise ValueError(f"{function_name} must return a normalised belief distribution that sums to 1.")
    return validated


def beliefs_close(left: Belief, right: Belief, *, tolerance: float = 1e-6) -> bool:
    return all(math.isclose(left[key], right[key], rel_tol=tolerance, abs_tol=tolerance) for key in left)


def build_uncertainty_snapshot(
    problem: UncertaintyProblem,
    *,
    prior: Belief,
    predicted: Belief,
    observation_likelihoods: dict[str, float],
    unnormalised: Belief,
    posterior: Belief,
    normalisation_constant: float,
    current_action: str | None,
    current_observation: str | None,
    true_location: str,
    step_index: int,
    history: list[dict[str, object]],
    status: str,
) -> dict[str, object]:
    rooms = [room.model_dump() for room in problem.rooms]
    room_ids = [room["id"] for room in rooms]
    rows = []
    for room in rooms:
        room_id = room["id"]
        rows.append(
            {
                "location": room_id,
                "label": room["label"],
                "prior": float(prior[room_id]),
                "predicted": float(predicted[room_id]),
                "likelihood": float(observation_likelihoods[room_id]),
                "unnormalised": float(unnormalised[room_id]),
                "posterior": float(posterior[room_id]),
            }
        )

    most_likely_location = max(posterior, key=posterior.get)
    transition_rows: list[dict[str, object]] = []
    if current_action is not None:
        transition_model = problem.transition_models[current_action]
        for room in rooms:
            source = room["id"]
            entries = [
                {
                    "location": destination,
                    "label": room_label(problem, destination),
                    "probability": float(probability),
                }
                for destination, probability in transition_model[source].items()
                if probability > 0
            ]
            transition_rows.append(
                {
                    "source": source,
                    "label": room["label"],
                    "entries": sorted(entries, key=lambda entry: (-entry["probability"], entry["label"])),
                }
            )

    return {
        "search": {
            "status": status,
            "result": status,
            "finished": step_index >= len(problem.scripted_steps),
        },
        "stats": {
            "step_index": step_index,
            "max_belief": float(posterior[most_likely_location]),
            "entropy": belief_entropy(posterior),
            "normalisation_constant": float(normalisation_constant),
        },
        "uncertainty": {
            "step_index": step_index,
            "total_steps": len(problem.scripted_steps),
            "rooms": rooms,
            "connections": [list(edge) for edge in problem.connections],
            "current_action": current_action,
            "current_observation": current_observation,
            "current_true_location": true_location,
            "prior_belief": ordered_distribution(room_ids, prior),
            "predicted_belief": ordered_distribution(room_ids, predicted),
            "observation_likelihoods": ordered_distribution(room_ids, observation_likelihoods),
            "unnormalised_posterior": ordered_distribution(room_ids, unnormalised),
            "posterior_belief": ordered_distribution(room_ids, posterior),
            "belief_rows": rows,
            "transition_rows": transition_rows,
            "history": copy.deepcopy(history),
            "most_likely_location": most_likely_location,
            "most_likely_label": room_label(problem, most_likely_location),
            "most_likely_probability": float(posterior[most_likely_location]),
            "normalisation_constant": float(normalisation_constant),
        },
    }


def ordered_distribution(room_ids: list[str], belief: dict[str, float]) -> dict[str, float]:
    return {room_id: float(belief[room_id]) for room_id in room_ids}


def room_label(problem: UncertaintyProblem, room_id: str) -> str:
    for room in problem.rooms:
        if room.id == room_id:
            return room.label
    return room_id.replace("_", " ")


def format_action_label(action: str) -> str:
    if action == "stay":
        return "Stay"
    if action.startswith("move_to_"):
        return "Move to " + action.removeprefix("move_to_").replace("_", " ")
    return action.replace("_", " ").title()


def format_observation_label(observation: str) -> str:
    return observation.replace("_", " ")


def build_step_annotation(
    *,
    prior: Belief,
    posterior: Belief,
    action: str,
    observation: str,
) -> str:
    prior_peak = max(prior, key=prior.get)
    posterior_peak = max(posterior, key=posterior.get)
    if prior_peak == posterior_peak:
        return (
            f"{format_action_label(action)} spreads the belief, then {format_observation_label(observation)} "
            f"reinforces {posterior_peak.replace('_', ' ')} as the leading hypothesis."
        )
    return (
        f"{format_action_label(action)} shifts probability mass away from {prior_peak.replace('_', ' ')}, "
        f"and {format_observation_label(observation)} leaves {posterior_peak.replace('_', ' ')} on top."
    )


def belief_entropy(belief: Belief) -> float:
    total = 0.0
    for probability in belief.values():
        if probability <= 0:
            continue
        total -= probability * math.log2(probability)
    return total
