"""Curated Bayes-filter localisation examples."""

from __future__ import annotations

from collections import deque

from ai9414.uncertainty.models import (
    CANONICAL_CONNECTIONS,
    UncertaintyExample,
    UncertaintyProblem,
    UncertaintyRoom,
    UncertaintyScenarioStep,
)

ROOMS: list[UncertaintyRoom] = [
    UncertaintyRoom(
        id="mail_room",
        label="Mail room",
        charger=True,
        marker="amber",
        description="The mail room has a charger dock and orange floor tape.",
    ),
    UncertaintyRoom(
        id="office_a",
        label="Office A",
        window=True,
        marker="blue",
        description="Office A has a window and a blue floor marker.",
    ),
    UncertaintyRoom(
        id="corridor",
        label="Corridor",
        door_nearby=True,
        marker="yellow",
        description="The corridor sits at the centre and is the only place with a nearby door.",
    ),
    UncertaintyRoom(
        id="office_b",
        label="Office B",
        marker="green",
        description="Office B has no charger or window, but it does have a green floor marker.",
    ),
    UncertaintyRoom(
        id="lab",
        label="Lab",
        charger=True,
        window=True,
        marker="blue",
        description="The lab has both a charger dock and a window, and it shares the blue marker with Office A.",
    ),
]

OBSERVATIONS: list[str] = [
    "charger_detected",
    "window_detected",
    "door_nearby",
    "blue_marker",
    "green_marker",
]

BASE_SENSOR_MODEL: dict[str, dict[str, float]] = {
    "mail_room": {
        "charger_detected": 0.82,
        "window_detected": 0.08,
        "door_nearby": 0.06,
        "blue_marker": 0.12,
        "green_marker": 0.07,
    },
    "office_a": {
        "charger_detected": 0.09,
        "window_detected": 0.76,
        "door_nearby": 0.08,
        "blue_marker": 0.74,
        "green_marker": 0.05,
    },
    "corridor": {
        "charger_detected": 0.05,
        "window_detected": 0.08,
        "door_nearby": 0.88,
        "blue_marker": 0.12,
        "green_marker": 0.08,
    },
    "office_b": {
        "charger_detected": 0.07,
        "window_detected": 0.09,
        "door_nearby": 0.08,
        "blue_marker": 0.08,
        "green_marker": 0.84,
    },
    "lab": {
        "charger_detected": 0.77,
        "window_detected": 0.74,
        "door_nearby": 0.07,
        "blue_marker": 0.71,
        "green_marker": 0.05,
    },
}

AMBIGUOUS_SENSOR_MODEL: dict[str, dict[str, float]] = {
    **BASE_SENSOR_MODEL,
    "office_a": {
        "charger_detected": 0.08,
        "window_detected": 0.62,
        "door_nearby": 0.08,
        "blue_marker": 0.86,
        "green_marker": 0.05,
    },
    "lab": {
        "charger_detected": 0.71,
        "window_detected": 0.68,
        "door_nearby": 0.07,
        "blue_marker": 0.84,
        "green_marker": 0.04,
    },
}


def build_examples() -> dict[str, UncertaintyExample]:
    examples = [
        UncertaintyExample(
            name="office_localisation_basic",
            title="Office localisation baseline",
            subtitle="Starts from a uniform belief, then combines motion and observation updates.",
            problem=UncertaintyProblem(
                title="Office localisation baseline",
                subtitle="An office layout with noisy motion and sensing.",
                rooms=ROOMS,
                connections=list(CANONICAL_CONNECTIONS),
                initial_belief=_uniform_belief(),
                initial_true_location="corridor",
                available_actions=_action_names(),
                observations=list(OBSERVATIONS),
                transition_models=_build_action_models(move_success=0.82, stay_probability=0.18),
                observation_model=BASE_SENSOR_MODEL,
                scripted_steps=[
                    UncertaintyScenarioStep(
                        action="move_to_mail_room",
                        observation="charger_detected",
                        true_location="mail_room",
                        note="One charger reading should still leave some probability on the lab.",
                    ),
                    UncertaintyScenarioStep(
                        action="move_to_corridor",
                        observation="door_nearby",
                        true_location="corridor",
                        note="The corridor is the clearest room for the door sensor.",
                    ),
                    UncertaintyScenarioStep(
                        action="move_to_office_a",
                        observation="window_detected",
                        true_location="office_a",
                        note="Window evidence should now favour Office A over the mail room and corridor.",
                    ),
                ],
            ),
        ),
        UncertaintyExample(
            name="office_localisation_motion_noise",
            title="Motion-noise spotlight",
            subtitle="Higher motion noise keeps the prediction step spread across several rooms.",
            problem=UncertaintyProblem(
                title="Motion-noise spotlight",
                subtitle="Extra motion noise weakens localisation even when the intended action is clear.",
                rooms=ROOMS,
                connections=list(CANONICAL_CONNECTIONS),
                initial_belief={
                    "mail_room": 0.05,
                    "office_a": 0.1,
                    "corridor": 0.55,
                    "office_b": 0.15,
                    "lab": 0.15,
                },
                initial_true_location="corridor",
                available_actions=_action_names(),
                observations=list(OBSERVATIONS),
                transition_models=_build_action_models(move_success=0.58, stay_probability=0.42),
                observation_model=BASE_SENSOR_MODEL,
                scripted_steps=[
                    UncertaintyScenarioStep(
                        action="move_to_lab",
                        observation="door_nearby",
                        true_location="corridor",
                        note="The first action fails, so the door observation reinforces that the robot probably stayed near the corridor.",
                    ),
                    UncertaintyScenarioStep(
                        action="move_to_lab",
                        observation="charger_detected",
                        true_location="lab",
                        note="A second attempt finally reaches the lab, but the belief should still remember the earlier uncertainty.",
                    ),
                    UncertaintyScenarioStep(
                        action="move_to_corridor",
                        observation="door_nearby",
                        true_location="corridor",
                        note="Prediction and correction now align, so the belief should reconcentrate on the corridor.",
                    ),
                ],
            ),
        ),
        UncertaintyExample(
            name="office_localisation_ambiguous_sensor",
            title="Ambiguous blue-marker sensor",
            subtitle="Office A and the lab share the same blue floor marker, so repeated evidence stays ambiguous until a better cue arrives.",
            problem=UncertaintyProblem(
                title="Ambiguous blue-marker sensor",
                subtitle="Blue-marker observations cannot by themselves tell Office A apart from the lab.",
                rooms=ROOMS,
                connections=list(CANONICAL_CONNECTIONS),
                initial_belief={
                    "mail_room": 0.1,
                    "office_a": 0.25,
                    "corridor": 0.3,
                    "office_b": 0.15,
                    "lab": 0.2,
                },
                initial_true_location="office_a",
                available_actions=_action_names(),
                observations=list(OBSERVATIONS),
                transition_models=_build_action_models(move_success=0.8, stay_probability=0.2),
                observation_model=AMBIGUOUS_SENSOR_MODEL,
                scripted_steps=[
                    UncertaintyScenarioStep(
                        action="move_to_office_a",
                        observation="blue_marker",
                        true_location="office_a",
                        note="Blue marker evidence supports both Office A and the lab.",
                    ),
                    UncertaintyScenarioStep(
                        action="move_to_corridor",
                        observation="door_nearby",
                        true_location="corridor",
                        note="A distinctive door observation finally breaks the Office A versus lab tie.",
                    ),
                    UncertaintyScenarioStep(
                        action="move_to_lab",
                        observation="charger_detected",
                        true_location="lab",
                        note="Once the robot reaches the lab, the charger signal should shift the posterior strongly towards it.",
                    ),
                ],
            ),
        ),
        UncertaintyExample(
            name="office_localisation_repeated_evidence",
            title="Repeated evidence sharpens belief",
            subtitle="Several moderate observations can localise the robot even when no single update is decisive.",
            problem=UncertaintyProblem(
                title="Repeated evidence sharpens belief",
                subtitle="The posterior narrows over several Bayes-filter steps rather than all at once.",
                rooms=ROOMS,
                connections=list(CANONICAL_CONNECTIONS),
                initial_belief=_uniform_belief(),
                initial_true_location="office_b",
                available_actions=_action_names(),
                observations=list(OBSERVATIONS),
                transition_models=_build_action_models(move_success=0.76, stay_probability=0.24),
                observation_model=BASE_SENSOR_MODEL,
                scripted_steps=[
                    UncertaintyScenarioStep(
                        action="move_to_office_b",
                        observation="green_marker",
                        true_location="office_b",
                        note="One green-marker reading is helpful, but it should not instantly collapse the belief to one state.",
                    ),
                    UncertaintyScenarioStep(
                        action="move_to_corridor",
                        observation="door_nearby",
                        true_location="corridor",
                        note="The corridor door sensor confirms the move and reduces leftover mass elsewhere.",
                    ),
                    UncertaintyScenarioStep(
                        action="move_to_lab",
                        observation="charger_detected",
                        true_location="lab",
                        note="The lab and mail room both have chargers, so the action model still matters.",
                    ),
                    UncertaintyScenarioStep(
                        action="move_to_lab",
                        observation="window_detected",
                        true_location="lab",
                        note="Repeated evidence now makes the lab the dominant hypothesis.",
                    ),
                ],
            ),
        ),
    ]
    return {example.name: example for example in examples}


def _uniform_belief() -> dict[str, float]:
    return {room.id: 0.2 for room in ROOMS}


def _action_names() -> list[str]:
    return [f"move_to_{room.id}" for room in ROOMS] + ["stay"]


def _build_action_models(*, move_success: float, stay_probability: float) -> dict[str, dict[str, dict[str, float]]]:
    room_ids = [room.id for room in ROOMS]
    adjacency = {room_id: set() for room_id in room_ids}
    for left, right in CANONICAL_CONNECTIONS:
        adjacency[left].add(right)
        adjacency[right].add(left)

    models: dict[str, dict[str, dict[str, float]]] = {}
    for target in room_ids:
        action_name = f"move_to_{target}"
        models[action_name] = {}
        for source in room_ids:
            distribution = {room_id: 0.0 for room_id in room_ids}
            if source == target:
                distribution[source] = 1.0
            else:
                next_room = _shortest_path_next_hop(adjacency, source, target)
                distribution[next_room] = move_success
                distribution[source] = stay_probability
            models[action_name][source] = distribution

    models["stay"] = {}
    for source in room_ids:
        distribution = {room_id: 0.0 for room_id in room_ids}
        distribution[source] = 0.9
        for neighbour in sorted(adjacency[source]):
            distribution[neighbour] += 0.1 / len(adjacency[source])
        models["stay"][source] = distribution
    return models


def _shortest_path_next_hop(adjacency: dict[str, set[str]], source: str, target: str) -> str:
    queue: deque[tuple[str, list[str]]] = deque([(source, [source])])
    visited = {source}
    while queue:
        node, path = queue.popleft()
        if node == target:
            return path[1] if len(path) > 1 else source
        for neighbour in sorted(adjacency[node]):
            if neighbour in visited:
                continue
            visited.add(neighbour)
            queue.append((neighbour, path + [neighbour]))
    return source
