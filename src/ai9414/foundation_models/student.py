"""Student-facing tokenisation helpers for the foundation models explorer."""

from __future__ import annotations

import re
from collections import Counter
from typing import TypedDict

TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
PRETOKEN_PATTERN = re.compile(r"\s*\w+|\s*[^\w\s]|\s+$", re.UNICODE)

BPEPair = tuple[str, str]
SegmentedCorpus = list[list[list[str]]]
TIE_BREAK_RULE = "highest frequency, then alphabetical symbol-pair order"


class BPELearningState(TypedDict):
    merge_step: int
    learned_merges: list[BPEPair]
    pair_counts: list[tuple[BPEPair, int]]
    selected_pair: BPEPair | None
    selected_pair_count: int | None
    tied_candidate_count: int
    tie_break_rule: str
    segmented_corpus: SegmentedCorpus


def tokenize_characters(text: str) -> list[str]:
    """Return every character, including whitespace, as a token."""

    return list(str(text))


def tokenize_words(text: str) -> list[str]:
    """Return a simple rule-based word tokenisation with punctuation split out."""

    return TOKEN_PATTERN.findall(str(text))


def tokenize_bpe_units(text: str) -> list[str]:
    """Split text into word-local BPE units while retaining leading whitespace.

    This deliberately small teaching implementation learns merges within each
    pre-tokenised unit. Whitespace preceding a word or punctuation mark remains
    in that unit, so a learned subword may visibly include a word boundary.
    """

    return PRETOKEN_PATTERN.findall(str(text))


def learn_bpe_merges(corpus: list[str], num_merges: int) -> list[BPEPair]:
    """Learn a small deterministic sequence of BPE-style merges from a corpus."""

    states = build_bpe_learning_states(corpus, num_merges)
    return list(states[-1]["learned_merges"])


def apply_bpe(text: str, merges: list[BPEPair]) -> list[str]:
    """Apply a learned BPE merge list to a new text and return its token sequence."""

    tokens: list[str] = []
    for unit in tokenize_bpe_units(text):
        symbols = list(unit)
        for pair in merges:
            symbols = _merge_symbol_pair(symbols, pair)
        tokens.extend(symbols)
    return tokens


def build_bpe_learning_states(
    corpus: list[str], num_merges: int
) -> list[BPELearningState]:
    """Return each deterministic state in the simplified BPE learning process."""

    segmented_corpus = _initialise_segmented_corpus(corpus)
    states: list[BPELearningState] = [
        {
            "merge_step": 0,
            "learned_merges": [],
            "pair_counts": _sorted_pair_counts(segmented_corpus),
            "selected_pair": None,
            "selected_pair_count": None,
            "tied_candidate_count": 0,
            "tie_break_rule": TIE_BREAK_RULE,
            "segmented_corpus": _clone_segmented_corpus(segmented_corpus),
        }
    ]

    learned_merges: list[BPEPair] = []
    for merge_index in range(max(0, int(num_merges))):
        pair_counts = _sorted_pair_counts(segmented_corpus)
        if not pair_counts:
            break

        selected_pair, selected_count = pair_counts[0]
        tied_candidate_count = sum(count == selected_count for _, count in pair_counts)
        learned_merges.append(selected_pair)
        segmented_corpus = [
            [_merge_symbol_pair(symbols, selected_pair) for symbols in text_units]
            for text_units in segmented_corpus
        ]
        states.append(
            {
                "merge_step": merge_index + 1,
                "learned_merges": list(learned_merges),
                "pair_counts": pair_counts,
                "selected_pair": selected_pair,
                "selected_pair_count": selected_count,
                "tied_candidate_count": tied_candidate_count,
                "tie_break_rule": TIE_BREAK_RULE,
                "segmented_corpus": _clone_segmented_corpus(segmented_corpus),
            }
        )

    if len(states) == 1 and num_merges > 0:
        states[0]["pair_counts"] = []
    return states


def _initialise_segmented_corpus(corpus: list[str]) -> SegmentedCorpus:
    return [[list(unit) for unit in tokenize_bpe_units(text)] for text in corpus]


def _sorted_pair_counts(segmented_corpus: SegmentedCorpus) -> list[tuple[BPEPair, int]]:
    pair_counts: Counter[BPEPair] = Counter()
    for text_units in segmented_corpus:
        for symbols in text_units:
            pair_counts.update(zip(symbols, symbols[1:]))
    return sorted(
        pair_counts.items(),
        key=lambda item: (-item[1], item[0][0], item[0][1]),
    )


def _merge_symbol_pair(symbols: list[str], pair: BPEPair) -> list[str]:
    if len(symbols) < 2:
        return list(symbols)

    merged: list[str] = []
    index = 0
    while index < len(symbols):
        if index + 1 < len(symbols) and (symbols[index], symbols[index + 1]) == pair:
            merged.append(symbols[index] + symbols[index + 1])
            index += 2
        else:
            merged.append(symbols[index])
            index += 1
    return merged


def _clone_segmented_corpus(segmented_corpus: SegmentedCorpus) -> SegmentedCorpus:
    return [
        [list(symbols) for symbols in text_units] for text_units in segmented_corpus
    ]
