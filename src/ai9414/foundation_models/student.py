"""Student-facing tokenisation helpers for the foundation models explorer."""

from __future__ import annotations

import re
from collections import Counter

TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def tokenize_characters(text: str) -> list[str]:
    """Return a simple character-level tokenisation that ignores whitespace."""

    return [character for character in str(text) if not character.isspace()]


def tokenize_words(text: str) -> list[str]:
    """Return a simple rule-based word tokenisation with punctuation split out."""

    return TOKEN_PATTERN.findall(str(text))


def learn_bpe_merges(corpus: list[str], num_merges: int) -> list[tuple[str, str]]:
    """Learn a small deterministic sequence of BPE-style merges from a corpus."""

    segmented_corpus = _initialise_segmented_corpus(corpus)
    merges: list[tuple[str, str]] = []

    for _ in range(max(0, int(num_merges))):
        pair_counts: Counter[tuple[str, str]] = Counter()
        for text_units in segmented_corpus:
            for symbols in text_units:
                pair_counts.update(zip(symbols, symbols[1:]))

        if not pair_counts:
            break

        selected_pair = sorted(
            pair_counts.items(),
            key=lambda item: (-item[1], item[0][0], item[0][1]),
        )[0][0]
        merges.append(selected_pair)
        segmented_corpus = [
            [_merge_symbol_pair(symbols, selected_pair) for symbols in text_units]
            for text_units in segmented_corpus
        ]

    return merges


def apply_bpe(text: str, merges: list[tuple[str, str]]) -> list[str]:
    """Apply a learned BPE merge list to a new text and return its token sequence."""

    tokens: list[str] = []
    for token in tokenize_words(text):
        symbols = list(token)
        for pair in merges:
            symbols = _merge_symbol_pair(symbols, pair)
        tokens.extend(symbols)
    return tokens


def _initialise_segmented_corpus(corpus: list[str]) -> list[list[list[str]]]:
    return [[list(token) for token in tokenize_words(text)] for text in corpus]


def _merge_symbol_pair(symbols: list[str], pair: tuple[str, str]) -> list[str]:
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
