"""Replay construction for deterministic next-token decoding examples."""

from __future__ import annotations

import math
from typing import Any, Literal

from ai9414.core.models import TraceBundle, TraceStep, TraceSummary
from ai9414.foundation_models.decoding import (
    apply_temperature,
    greedy_select,
    renormalise,
    seeded_random_draw,
    seeded_sample,
    softmax,
    top_k_filter,
    top_p_filter,
)
from ai9414.foundation_models.models import DecodingProblem, DecodingRule

DecodingStage = Literal[
    "model_scores",
    "temperature",
    "filtering",
    "renormalisation",
    "selection",
]

STAGE_RANK: dict[DecodingStage, int] = {
    "model_scores": 0,
    "temperature": 1,
    "filtering": 2,
    "renormalisation": 3,
    "selection": 4,
}

RULE_LABELS: dict[DecodingRule, str] = {
    "greedy": "Greedy",
    "sampling": "Sampling",
    "top_k": "Top-k sampling",
    "top_p": "Top-p sampling",
}


def build_decoding_trace(problem: DecodingProblem) -> TraceBundle:
    """Build all transparent stages of one next-token decoding decision."""

    computation = _compute_decoding(problem)
    initial_state = _build_snapshot(problem, computation, "model_scores")
    stages: list[tuple[DecodingStage, str, str, str]] = [
        (
            "temperature",
            f"Apply temperature T={problem.options.temperature:g}",
            _temperature_annotation(problem),
            "Temperature transforms the distribution; it is not itself a token-selection rule.",
        ),
        (
            "filtering",
            _filter_label(problem),
            _filter_annotation(problem, computation),
            "Top-k keeps a fixed count, whereas top-p keeps the smallest threshold-reaching prefix.",
        ),
        (
            "renormalisation",
            "Renormalise retained probabilities",
            _renormalisation_annotation(computation),
            "Sampling requires the retained probabilities to sum to one after filtering.",
        ),
        (
            "selection",
            _selection_label(problem, computation),
            _selection_annotation(problem, computation),
            "The model supplies scores; the decoding rule determines how one candidate is selected.",
        ),
    ]
    steps = [
        TraceStep(
            index=index,
            event_type=stage,
            label=label,
            annotation=annotation,
            teaching_note=teaching_note,
            state_patch=_build_snapshot(problem, computation, stage),
        )
        for index, (stage, label, annotation, teaching_note) in enumerate(stages)
    ]

    return TraceBundle(
        app_type="foundation_models",
        trace_id="foundation-models-decoding-trace",
        is_complete=True,
        initial_state=initial_state,
        summary=TraceSummary(step_count=len(steps), result="token_selected"),
        steps=steps,
    )


def _compute_decoding(problem: DecodingProblem) -> dict[str, Any]:
    ranked_candidates = [
        candidate
        for _, candidate in sorted(
            enumerate(problem.candidates),
            key=lambda item: (-item[1].logit, item[0]),
        )
    ]
    logits = [candidate.logit for candidate in ranked_candidates]
    model_probabilities = softmax(logits)
    scaled_logits = apply_temperature(logits, problem.options.temperature)
    transformed_probabilities = softmax(scaled_logits)

    if problem.options.selection_rule == "top_k":
        filtered_probabilities = top_k_filter(
            transformed_probabilities, problem.options.top_k
        )
    elif problem.options.selection_rule == "top_p":
        filtered_probabilities = top_p_filter(
            transformed_probabilities, problem.options.top_p
        )
    else:
        filtered_probabilities = list(transformed_probabilities)

    retained_mass = math.fsum(filtered_probabilities)
    renormalised_probabilities = renormalise(filtered_probabilities)
    if problem.options.selection_rule == "greedy":
        random_draw = None
        selected_index = greedy_select(renormalised_probabilities)
    else:
        random_draw = seeded_random_draw(problem.options.seed)
        selected_index = seeded_sample(renormalised_probabilities, problem.options.seed)

    intervals: list[dict[str, float] | None] = []
    lower = 0.0
    for probability in renormalised_probabilities:
        if probability <= 0.0:
            intervals.append(None)
            continue
        upper = lower + probability
        intervals.append({"lower": lower, "upper": upper})
        lower = upper

    cumulative_probabilities: list[float] = []
    cumulative = 0.0
    for probability in transformed_probabilities:
        cumulative += probability
        cumulative_probabilities.append(cumulative)

    return {
        "candidates": ranked_candidates,
        "model_probabilities": model_probabilities,
        "scaled_logits": scaled_logits,
        "transformed_probabilities": transformed_probabilities,
        "cumulative_probabilities": cumulative_probabilities,
        "filtered_probabilities": filtered_probabilities,
        "retained_mass": retained_mass,
        "renormalised_probabilities": renormalised_probabilities,
        "selection_intervals": intervals,
        "random_draw": random_draw,
        "selected_index": selected_index,
    }


def _build_snapshot(
    problem: DecodingProblem,
    computation: dict[str, Any],
    stage: DecodingStage,
) -> dict[str, Any]:
    stage_rank = STAGE_RANK[stage]
    selected_index = computation["selected_index"]
    candidate_rows = []
    for index, candidate in enumerate(computation["candidates"]):
        candidate_rows.append(
            {
                "rank": index + 1,
                "token": candidate.token,
                "display_text": _display_token_text(candidate.token),
                "accessible_label": _accessible_token_label(candidate.token),
                "logit": candidate.logit,
                "model_probability": computation["model_probabilities"][index],
                "scaled_logit": (
                    computation["scaled_logits"][index]
                    if stage_rank >= STAGE_RANK["temperature"]
                    else None
                ),
                "transformed_probability": (
                    computation["transformed_probabilities"][index]
                    if stage_rank >= STAGE_RANK["temperature"]
                    else None
                ),
                "cumulative_probability": (
                    computation["cumulative_probabilities"][index]
                    if stage_rank >= STAGE_RANK["temperature"]
                    else None
                ),
                "retained": (
                    computation["filtered_probabilities"][index] > 0.0
                    if stage_rank >= STAGE_RANK["filtering"]
                    else None
                ),
                "renormalised_probability": (
                    computation["renormalised_probabilities"][index]
                    if stage_rank >= STAGE_RANK["renormalisation"]
                    else None
                ),
                "selection_interval": (
                    computation["selection_intervals"][index]
                    if stage_rank >= STAGE_RANK["selection"]
                    else None
                ),
                "selected": (
                    index == selected_index
                    if stage_rank >= STAGE_RANK["selection"]
                    else None
                ),
            }
        )

    selected_candidate = computation["candidates"][selected_index]
    options = problem.options.model_dump()
    return {
        "example_title": problem.title,
        "example_subtitle": problem.subtitle,
        "algorithm_label": "Foundation Models Demo - Decoding Explorer",
        "algorithm_note": (
            "Candidate logits are fixed teaching data. The replay applies temperature, filtering, "
            "renormalisation, and a deterministic or seeded selection rule locally."
        ),
        "foundation_models": {
            "explorer_kind": "decoding",
            "stage": stage,
            "status": _stage_status(stage),
            "context_tokens": [
                {
                    "index": index,
                    "text": token,
                    "display_text": _display_token_text(token),
                    "accessible_label": _accessible_token_label(token),
                }
                for index, token in enumerate(problem.context_tokens)
            ],
            "context_text": "".join(problem.context_tokens),
            "candidate_scores": candidate_rows,
            "selection_rule": problem.options.selection_rule,
            "selection_rule_label": RULE_LABELS[problem.options.selection_rule],
            "temperature": problem.options.temperature,
            "top_k": problem.options.top_k,
            "top_p": problem.options.top_p,
            "seed": problem.options.seed,
            "retained_count": sum(
                probability > 0.0
                for probability in computation["filtered_probabilities"]
            ),
            "retained_mass": (
                computation["retained_mass"]
                if stage_rank >= STAGE_RANK["filtering"]
                else None
            ),
            "random_draw": (
                computation["random_draw"]
                if stage_rank >= STAGE_RANK["selection"]
                else None
            ),
            "selected_token": (
                {
                    "rank": selected_index + 1,
                    "token": selected_candidate.token,
                    "display_text": _display_token_text(selected_candidate.token),
                    "accessible_label": _accessible_token_label(
                        selected_candidate.token
                    ),
                }
                if stage_rank >= STAGE_RANK["selection"]
                else None
            ),
            "available_selection_rules": [
                {"value": value, "label": label} for value, label in RULE_LABELS.items()
            ],
            "scores_are_precomputed": True,
            "arbitrary_text_supported": False,
            "implementation_note": (
                "This explorer does not run a language model. It uses curated, precomputed logits "
                "so every transformation and selection can be reproduced."
            ),
        },
        "options": {
            key: value for key, value in options.items() if key != "playback_speed"
        },
    }


def _temperature_annotation(problem: DecodingProblem) -> str:
    temperature = problem.options.temperature
    if temperature == 1.0:
        return "At T=1, dividing each logit by temperature leaves the model distribution unchanged."
    if temperature < 1.0:
        return f"T={temperature:g} sharpens the distribution by increasing relative logit gaps."
    return (
        f"T={temperature:g} flattens the distribution by reducing relative logit gaps."
    )


def _filter_label(problem: DecodingProblem) -> str:
    rule = problem.options.selection_rule
    if rule == "top_k":
        return f"Keep the top k={problem.options.top_k} candidates"
    if rule == "top_p":
        return f"Keep the smallest prefix reaching p={problem.options.top_p:g}"
    return f"Retain all candidates for {RULE_LABELS[rule].lower()}"


def _filter_annotation(problem: DecodingProblem, computation: dict[str, Any]) -> str:
    retained_tokens = [
        candidate.token
        for candidate, probability in zip(
            computation["candidates"],
            computation["filtered_probabilities"],
            strict=True,
        )
        if probability > 0.0
    ]
    token_list = ", ".join(retained_tokens)
    if problem.options.selection_rule == "top_p":
        return (
            f"The ranked prefix [{token_list}] is the smallest one whose cumulative "
            f"transformed probability reaches at least {problem.options.top_p:g}."
        )
    if problem.options.selection_rule == "top_k":
        return f"Top-k retains exactly the {len(retained_tokens)} leading candidates: {token_list}."
    return f"{RULE_LABELS[problem.options.selection_rule]} applies no probability filter, so every candidate remains."


def _renormalisation_annotation(computation: dict[str, Any]) -> str:
    retained_mass = computation["retained_mass"]
    return (
        f"The retained probabilities sum to {retained_mass:.6f}. Dividing each retained "
        "value by this mass produces a distribution that sums to one."
    )


def _selection_label(problem: DecodingProblem, computation: dict[str, Any]) -> str:
    token = computation["candidates"][computation["selected_index"]].token
    return f"Select '{_display_token_text(token)}' with {RULE_LABELS[problem.options.selection_rule]}"


def _selection_annotation(problem: DecodingProblem, computation: dict[str, Any]) -> str:
    selected_index = computation["selected_index"]
    token = _display_token_text(computation["candidates"][selected_index].token)
    if problem.options.selection_rule == "greedy":
        return f"Greedy decoding selects '{token}', the candidate with the highest transformed probability."
    interval = computation["selection_intervals"][selected_index]
    return (
        f"Seed {problem.options.seed} gives draw {computation['random_draw']:.6f}. "
        f"It falls in the cumulative interval [{interval['lower']:.6f}, "
        f"{interval['upper']:.6f}) assigned to '{token}', so that token is selected."
    )


def _stage_status(stage: DecodingStage) -> str:
    return {
        "model_scores": "model scores ready",
        "temperature": "temperature applied",
        "filtering": "candidates filtered",
        "renormalisation": "probabilities renormalised",
        "selection": "token selected",
    }[stage]


def _display_token_text(token: str) -> str:
    replacements = {" ": "▁", "\t": "⇥", "\n": "↵", "\r": "␍"}
    return "".join(replacements.get(character, character) for character in token)


def _accessible_token_label(token: str) -> str:
    replacements = {
        " ": "space",
        "\t": "tab",
        "\n": "line break",
        "\r": "carriage return",
    }
    parts: list[str] = []
    text_buffer: list[str] = []

    def flush_text() -> None:
        if text_buffer:
            parts.append("".join(text_buffer))
            text_buffer.clear()

    for character in token:
        if character in replacements:
            flush_text()
            parts.append(replacements[character])
        else:
            text_buffer.append(character)
    flush_text()
    return " ".join(parts)
