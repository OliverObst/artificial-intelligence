"""Deterministic sequence-search helpers for the decoding explorer."""

from __future__ import annotations

import math
from typing import Any

from ai9414.foundation_models.models import SequenceSearchExample, SequenceSearchNode


def build_sequence_search_comparison(
    example: SequenceSearchExample,
) -> dict[str, Any]:
    """Compare greedy decoding and beam search on one validated fixed tree."""

    nodes = list(example.nodes)
    node_by_id = {node.node_id: node for node in nodes}
    children: dict[str, list[SequenceSearchNode]] = {
        node.node_id: [] for node in nodes
    }
    for node in nodes:
        if node.parent_id is not None:
            children[node.parent_id].append(node)

    root = next(node for node in nodes if node.parent_id is None)
    cumulative_log_probability = {root.node_id: 0.0}
    depth = {root.node_id: 0}
    sequence_tokens: dict[str, list[str]] = {root.node_id: []}

    pending = [root]
    while pending:
        parent = pending.pop(0)
        for child in children[parent.node_id]:
            cumulative_log_probability[child.node_id] = (
                cumulative_log_probability[parent.node_id]
                + math.log(child.conditional_probability)
            )
            depth[child.node_id] = depth[parent.node_id] + 1
            sequence_tokens[child.node_id] = [
                *sequence_tokens[parent.node_id],
                child.token,
            ]
            pending.append(child)

    greedy_path = [root.node_id]
    current = root
    while children[current.node_id]:
        current = max(
            children[current.node_id],
            key=lambda node: node.conditional_probability,
        )
        greedy_path.append(current.node_id)

    active = [root.node_id]
    beam_steps: list[dict[str, Any]] = []
    beam_considered: set[str] = {root.node_id}
    beam_retained: set[str] = {root.node_id}
    step = 0
    while not all(node_by_id[node_id].terminal for node_id in active):
        step += 1
        candidates: list[str] = []
        for node_id in active:
            node = node_by_id[node_id]
            if node.terminal:
                candidates.append(node_id)
            else:
                candidates.extend(child.node_id for child in children[node_id])
        ranked = sorted(
            dict.fromkeys(candidates),
            key=lambda node_id: (-cumulative_log_probability[node_id], node_id),
        )
        active = ranked[: example.beam_width]
        beam_considered.update(ranked)
        beam_retained.update(active)
        beam_steps.append(
            {
                "step": step,
                "candidates": [
                    {
                        "node_id": node_id,
                        "rank": rank,
                        "retained": node_id in active,
                        "sequence": _sequence_text(sequence_tokens[node_id]),
                        "cumulative_log_probability": cumulative_log_probability[
                            node_id
                        ],
                        "cumulative_probability": math.exp(
                            cumulative_log_probability[node_id]
                        ),
                    }
                    for rank, node_id in enumerate(ranked, start=1)
                ],
                "retained_node_ids": list(active),
            }
        )

    beam_result_id = max(
        active,
        key=lambda node_id: cumulative_log_probability[node_id],
    )
    terminal_ids = [node.node_id for node in nodes if node.terminal]
    globally_best_id = max(
        terminal_ids,
        key=lambda node_id: cumulative_log_probability[node_id],
    )
    beam_path = _path_to_root(beam_result_id, node_by_id)

    node_rows = []
    for node in nodes:
        siblings = (
            [root]
            if node.parent_id is None
            else children[node.parent_id]
        )
        local_rank = sorted(
            siblings,
            key=lambda sibling: (-sibling.conditional_probability, sibling.node_id),
        ).index(node) + 1
        if node.node_id == root.node_id:
            beam_status = "start"
        elif node.node_id in beam_path:
            beam_status = "winning path"
        elif node.node_id in beam_retained:
            beam_status = "retained"
        elif node.node_id in beam_considered:
            beam_status = "pruned"
        else:
            beam_status = "not reached"
        node_rows.append(
            {
                "node_id": node.node_id,
                "parent_id": node.parent_id,
                "token": node.token,
                "display_text": _display_token_text(node.token),
                "accessible_label": _accessible_token_label(node.token),
                "conditional_probability": node.conditional_probability,
                "cumulative_log_probability": cumulative_log_probability[
                    node.node_id
                ],
                "cumulative_probability": math.exp(
                    cumulative_log_probability[node.node_id]
                ),
                "depth": depth[node.node_id],
                "sequence_tokens": sequence_tokens[node.node_id],
                "sequence": _sequence_text(sequence_tokens[node.node_id]),
                "terminal": node.terminal,
                "local_rank": local_rank,
                "on_greedy_path": node.node_id in greedy_path,
                "on_beam_path": node.node_id in beam_path,
                "globally_best": node.node_id == globally_best_id,
                "beam_status": beam_status,
            }
        )

    greedy_result_id = greedy_path[-1]
    return {
        "title": example.title,
        "subtitle": example.subtitle,
        "beam_width": example.beam_width,
        "root_id": root.node_id,
        "nodes": node_rows,
        "greedy_path": greedy_path,
        "beam_path": beam_path,
        "beam_steps": beam_steps,
        "greedy_result": _result_payload(
            greedy_result_id,
            sequence_tokens,
            cumulative_log_probability,
        ),
        "beam_result": _result_payload(
            beam_result_id,
            sequence_tokens,
            cumulative_log_probability,
        ),
        "globally_best_result": _result_payload(
            globally_best_id,
            sequence_tokens,
            cumulative_log_probability,
        ),
        "teaching_point": (
            "Greedy decoding commits to the locally most probable token. Beam search "
            "keeps several partial sequences and compares their cumulative scores, so "
            "it can recover a better complete sequence."
        ),
        "scores_are_precomputed": True,
    }


def _path_to_root(
    node_id: str, node_by_id: dict[str, SequenceSearchNode]
) -> list[str]:
    path: list[str] = []
    current: str | None = node_id
    while current is not None:
        path.append(current)
        current = node_by_id[current].parent_id
    path.reverse()
    return path


def _result_payload(
    node_id: str,
    sequence_tokens: dict[str, list[str]],
    cumulative_log_probability: dict[str, float],
) -> dict[str, Any]:
    log_probability = cumulative_log_probability[node_id]
    return {
        "node_id": node_id,
        "sequence_tokens": sequence_tokens[node_id],
        "sequence": _sequence_text(sequence_tokens[node_id]),
        "cumulative_log_probability": log_probability,
        "cumulative_probability": math.exp(log_probability),
    }


def _sequence_text(tokens: list[str]) -> str:
    return "".join(tokens).strip()


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
