"""Trace construction helpers for the tokenisation explorer."""

from __future__ import annotations

from typing import Any

from ai9414.core.models import TraceBundle, TraceStep, TraceSummary
from ai9414.foundation_models.models import TokenisationProblem, TokeniserMode
from ai9414.foundation_models.student import (
    BPELearningState,
    BPEPair,
    apply_bpe,
    build_bpe_learning_states,
    tokenize_characters,
    tokenize_words,
)

MODE_LABELS: dict[TokeniserMode, str] = {
    "character": "Character tokeniser",
    "word": "Word tokeniser",
    "bpe": "Learned BPE tokeniser",
}


def build_foundation_trace(
    problem: TokenisationProblem,
    *,
    custom_text_active: bool = False,
) -> TraceBundle:
    """Build the replay bundle for the foundation models tokenisation explorer."""

    bpe_states = build_bpe_learning_states(problem.corpus_texts, problem.num_merges)

    if problem.tokeniser_mode == "bpe":
        initial_state = _build_snapshot(
            problem,
            learning_state=bpe_states[0],
            custom_text_active=custom_text_active,
        )
        steps = [
            TraceStep(
                index=index,
                event_type="merge",
                label=_merge_step_label(state),
                annotation=_merge_step_annotation(state),
                teaching_note=(
                    "BPE starts from characters, counts adjacent pairs, then promotes one frequent pair at a time "
                    "into a reusable subword token."
                ),
                state_patch=_build_snapshot(
                    problem,
                    learning_state=state,
                    custom_text_active=custom_text_active,
                ),
            )
            for index, state in enumerate(bpe_states[1:])
        ]
    else:
        initial_state = _build_snapshot(
            problem,
            learning_state=bpe_states[-1],
            custom_text_active=custom_text_active,
        )
        steps = []

    return TraceBundle(
        app_type="foundation_models",
        trace_id="foundation-models-trace",
        is_complete=True,
        initial_state=initial_state,
        summary=TraceSummary(
            step_count=len(steps),
            result="tokenised",
        ),
        steps=steps,
    )


def _build_snapshot(
    problem: TokenisationProblem,
    *,
    learning_state: BPELearningState,
    custom_text_active: bool,
) -> dict[str, Any]:
    merges = list(learning_state["learned_merges"])
    current_tokens = _tokenise_with_mode(problem.text, problem.tokeniser_mode, merges)
    comparison = _build_comparison(
        problem.text, merges, problem.context_window, problem.tokeniser_mode
    )
    return {
        "example_title": problem.title,
        "example_subtitle": problem.subtitle,
        "algorithm_label": "Foundation Models Demo - Tokenisation Explorer",
        "algorithm_note": (
            "Character tokens include whitespace. The rule-based word tokeniser omits separators. "
            "Simplified BPE keeps leading whitespace and adds one word-local merge per replay step."
        ),
        "foundation_models": {
            "explorer_kind": "tokenisation",
            "mode": problem.tokeniser_mode,
            "mode_label": MODE_LABELS[problem.tokeniser_mode],
            "status": _status_text(
                problem.tokeniser_mode, learning_state, problem.num_merges
            ),
            "implementation_note": (
                "This explorer uses a simplified, deterministic BPE learner. It preserves leading whitespace "
                "inside pre-tokenised units but does not reproduce any particular production tokenizer."
            ),
            "whitespace_legend": "In token displays, ▁ marks a space, ⇥ a tab, and ↵ a line break.",
            "text": problem.text,
            "custom_text_active": custom_text_active,
            "overlay_segments": _build_overlay_segments(
                problem.text, problem.tokeniser_mode, merges
            ),
            "tokens": _build_token_rows(current_tokens),
            "stats": _build_stats(problem.text, current_tokens, problem.context_window),
            "comparison": comparison,
            "available_modes": [
                {"value": "character", "label": MODE_LABELS["character"]},
                {"value": "word", "label": MODE_LABELS["word"]},
                {"value": "bpe", "label": MODE_LABELS["bpe"]},
            ],
            "selected_corpus": problem.corpus_name,
            "context_window": problem.context_window,
            "num_merges": problem.num_merges,
            "bpe": {
                "corpus_name": problem.corpus_name,
                "merge_step": learning_state["merge_step"],
                "requested_merges": problem.num_merges,
                "applied_merge_count": len(learning_state["learned_merges"]),
                "learned_merges": [
                    _merge_descriptor(pair, index)
                    for index, pair in enumerate(
                        learning_state["learned_merges"], start=1
                    )
                ],
                "selected_pair": (
                    None
                    if learning_state["selected_pair"] is None
                    else {
                        "left": learning_state["selected_pair"][0],
                        "right": learning_state["selected_pair"][1],
                        "merged": "".join(learning_state["selected_pair"]),
                        "display_left": _display_token_text(
                            learning_state["selected_pair"][0]
                        ),
                        "display_right": _display_token_text(
                            learning_state["selected_pair"][1]
                        ),
                        "display_merged": _display_token_text(
                            "".join(learning_state["selected_pair"])
                        ),
                        "count": learning_state["selected_pair_count"],
                        "tied_candidate_count": learning_state["tied_candidate_count"],
                        "tie_break_rule": learning_state["tie_break_rule"],
                    }
                ),
                "pair_counts": [
                    {"pair": _pair_label(pair), "count": count}
                    for pair, count in learning_state["pair_counts"][:8]
                ],
                "segmented_corpus": [
                    _format_segmented_text(text_units)
                    for text_units in learning_state["segmented_corpus"]
                ],
                "trace_ready": problem.tokeniser_mode == "bpe",
            },
        },
    }


def _tokenise_with_mode(
    text: str, mode: TokeniserMode, merges: list[BPEPair]
) -> list[str]:
    if mode == "character":
        return tokenize_characters(text)
    if mode == "word":
        return tokenize_words(text)
    return apply_bpe(text, merges)


def _build_comparison(
    text: str,
    merges: list[BPEPair],
    context_window: int,
    active_mode: TokeniserMode,
) -> list[dict[str, Any]]:
    comparison: list[dict[str, Any]] = []
    for mode in ("character", "word", "bpe"):
        tokens = _tokenise_with_mode(text, mode, merges)
        stats = _build_stats(text, tokens, context_window)
        comparison.append(
            {
                "mode": mode,
                "label": MODE_LABELS[mode],
                "token_count": stats["token_count"],
                "average_token_length": stats["average_token_length"],
                "context_usage": stats["context_usage"],
                "active": mode == active_mode,
            }
        )
    return comparison


def _build_overlay_segments(
    text: str, mode: TokeniserMode, merges: list[BPEPair]
) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    token_index = 0

    if mode == "character":
        for character in text:
            segments.append(
                {
                    "kind": "token",
                    "text": character,
                    "display_text": _display_token_text(character),
                    "accessible_label": _accessible_token_label(character),
                    "token_index": token_index,
                }
            )
            token_index += 1
        return segments

    if mode == "bpe":
        for token in apply_bpe(text, merges):
            segments.append(
                {
                    "kind": "token",
                    "text": token,
                    "display_text": _display_token_text(token),
                    "accessible_label": _accessible_token_label(token),
                    "token_index": token_index,
                }
            )
            token_index += 1
        return segments

    cursor = 0
    for match in tokenize_words_with_spans(text):
        start, end, token = match
        if start > cursor:
            segments.append({"kind": "whitespace", "text": text[cursor:start]})
        segments.append(
            {
                "kind": "token",
                "text": token,
                "display_text": _display_token_text(token),
                "accessible_label": _accessible_token_label(token),
                "token_index": token_index,
            }
        )
        token_index += 1
        cursor = end
    if cursor < len(text):
        segments.append({"kind": "whitespace", "text": text[cursor:]})
    return segments


def tokenize_words_with_spans(text: str) -> list[tuple[int, int, str]]:
    return [
        (match.start(), match.end(), match.group(0))
        for match in tokenize_words_pattern().finditer(text)
    ]


def tokenize_words_pattern():
    from ai9414.foundation_models.student import TOKEN_PATTERN

    return TOKEN_PATTERN


def _build_token_rows(tokens: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, token in enumerate(tokens):
        rows.append(
            {
                "index": index,
                "text": token,
                "display_text": _display_token_text(token),
                "accessible_label": _accessible_token_label(token),
            }
        )
    return rows


def _build_stats(text: str, tokens: list[str], context_window: int) -> dict[str, Any]:
    token_count = len(tokens)
    average_length = (
        0.0
        if token_count == 0
        else round(sum(len(token) for token in tokens) / token_count, 2)
    )
    return {
        "character_count": len(text),
        "token_count": token_count,
        "average_token_length": average_length,
        "context_window": context_window,
        "context_used": token_count,
        "context_remaining": max(context_window - token_count, 0),
        "context_usage": f"{token_count} / {context_window}",
        "token_budget_is_illustrative": True,
    }


def _status_text(
    mode: TokeniserMode, learning_state: BPELearningState, requested_merges: int
) -> str:
    if mode != "bpe":
        return "tokenised"
    if learning_state["merge_step"] == 0:
        return "ready to learn"
    if (
        learning_state["merge_step"] < requested_merges
        and learning_state["pair_counts"]
    ):
        return "learning merges"
    return "merges applied"


def _merge_step_label(state: BPELearningState) -> str:
    pair = state["selected_pair"]
    if pair is None:
        return "Initial segmentation"
    return (
        f"Merge {state['merge_step']}: {_display_token_text(pair[0])} + "
        f"{_display_token_text(pair[1])} -> {_display_token_text(pair[0] + pair[1])}"
    )


def _merge_step_annotation(state: BPELearningState) -> str:
    pair = state["selected_pair"]
    if pair is None:
        return "The corpus starts at character level, so every frequent adjacent pair is still visible."
    annotation = (
        f"The pair {_pair_label(pair)} appears {state['selected_pair_count']} time(s), "
        f"so the learner promotes it to the new token '{_display_token_text(pair[0] + pair[1])}'."
    )
    if state["tied_candidate_count"] > 1:
        annotation += (
            f" {state['tied_candidate_count']} pairs share that frequency; this deterministic demo then uses "
            "alphabetical symbol-pair order."
        )
    return annotation


def _merge_descriptor(pair: BPEPair, index: int) -> str:
    return f"{index}. {_pair_label(pair)} -> {_display_token_text(pair[0] + pair[1])}"


def _pair_label(pair: BPEPair) -> str:
    return f"{_display_token_text(pair[0])} + {_display_token_text(pair[1])}"


def _format_segmented_text(text_units: list[list[str]]) -> str:
    return "   |   ".join(
        " ".join(_display_token_text(symbol) for symbol in symbols)
        for symbols in text_units
    )


def _display_token_text(token: str) -> str:
    replacements = {
        " ": "▁",
        "\t": "⇥",
        "\n": "↵",
        "\r": "␍",
    }
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
