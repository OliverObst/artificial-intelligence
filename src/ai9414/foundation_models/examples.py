"""Curated inputs for the foundation-model teaching explorers."""

from __future__ import annotations

import math

from ai9414.foundation_models.models import (
    DecodingCandidate,
    DecodingExample,
    DecodingOptions,
    SequenceSearchExample,
    SequenceSearchNode,
    TokenisationCorpus,
    TokenisationExample,
)


def build_examples() -> dict[str, TokenisationExample]:
    examples = [
        TokenisationExample(
            name="simple_sentence",
            title="Simple sentence",
            subtitle="A clean baseline for comparing character, word, and subword token counts.",
            text="Deliver parcel to Office A before 10:30.",
            default_corpus="office_messages",
        ),
        TokenisationExample(
            name="decoding_context",
            title="Decoding activity context",
            subtitle="Tokenise the exact fixed context used by the decoding lecture activity.",
            text="The robot picked up the",
            default_corpus="office_messages",
            metadata={"related_decoding_example": "lecture_activity"},
        ),
        TokenisationExample(
            name="capital_context",
            title="Capital question context",
            subtitle="Tokenise the exact fixed context used by the peaked decoding example.",
            text="The capital of France is",
            default_corpus="office_messages",
            metadata={"related_decoding_example": "peaked_distribution"},
        ),
        TokenisationExample(
            name="typo_sentence",
            title="Typos and misspellings",
            subtitle="Word tokenisation stays brittle here, while subword pieces still recover some structure.",
            text="Delivr the parcell to Offce A befor 10:30.",
            default_corpus="office_messages",
        ),
        TokenisationExample(
            name="rare_names",
            title="Rare names",
            subtitle="Names expose why subword tokenisers are often more flexible than plain word vocabularies.",
            text="Send the package to Maximilian and Krzysztof.",
            default_corpus="names_and_codes",
        ),
        TokenisationExample(
            name="code_example",
            title="Code and punctuation",
            subtitle="Programming text breaks differently because punctuation and short fragments matter.",
            text="for i in range(10): print(i)",
            default_corpus="code_and_symbols",
        ),
        TokenisationExample(
            name="german_compound",
            title="German compound word",
            subtitle="A long compound word shows why character and subword tokenisation behave so differently.",
            text="Donaudampfschifffahrtsgesellschaftskapitaen",
            default_corpus="multilingual_fragments",
        ),
        TokenisationExample(
            name="mixed_symbols",
            title="Mixed symbols and numbers",
            subtitle="Numbers, hyphens, currency, and emoji often lead to surprising token boundaries.",
            text="Room A-17 costs $12.50 :)",
            default_corpus="names_and_codes",
        ),
        TokenisationExample(
            name="mixed_language",
            title="Mixed language text",
            subtitle="Mixed scripts and accents make it obvious that there is no single natural token boundary.",
            text="Hola from Munchen, see you at Tokyo Station.",
            default_corpus="multilingual_fragments",
        ),
    ]
    return {example.name: example for example in examples}


def build_corpora() -> dict[str, TokenisationCorpus]:
    corpora = [
        TokenisationCorpus(
            name="office_messages",
            title="Office messages",
            subtitle="Short delivery-style messages that favour office and timing vocabulary.",
            texts=[
                "Deliver parcel to Office A before 10:30.",
                "Collect package from Mail Room after 09:15.",
                "Office A receives parcel before lunch.",
                "Send parcel to corridor desk at 10:30.",
            ],
        ),
        TokenisationCorpus(
            name="names_and_codes",
            title="Names and codes",
            subtitle="Names, room identifiers, and small codes make subword fragments visible.",
            texts=[
                "Send badge to Maximilian in Room A-17.",
                "Krzysztof checks parcel code ZX-14.",
                "Room B-204 stores package ID KX-9.",
                "Maximilian meets Krzysztof at Desk 12.",
            ],
        ),
        TokenisationCorpus(
            name="multilingual_fragments",
            title="Multilingual fragments",
            subtitle="A small mixed-language corpus that produces less tidy subword pieces.",
            texts=[
                "Guten Morgen aus Munchen.",
                "Donaudampfschifffahrtsgesellschaftskapitaen arrives heute.",
                "Hola amiga, nos vemos manana.",
                "Tokyo Station verbindet alte und neue Linien.",
            ],
        ),
        TokenisationCorpus(
            name="code_and_symbols",
            title="Code and symbols",
            subtitle="Tiny code snippets and symbol-heavy text shift the most frequent pairs away from plain words.",
            texts=[
                "for i in range(10): print(i)",
                "total_cost += item_price * quantity",
                "if room_id == 'A-17': unlock()",
                "value = cost_per_unit / 2.0",
            ],
        ),
    ]
    return {corpus.name: corpus for corpus in corpora}


def build_decoding_examples() -> dict[str, DecodingExample]:
    """Return deterministic next-token score distributions for decoding lessons."""

    examples = [
        DecodingExample(
            name="lecture_activity",
            title="Decoding choices",
            subtitle=(
                "The lecture mini-activity distribution makes greedy, top-k, and top-p "
                "decisions directly comparable."
            ),
            context_tokens=["The", " robot", " picked", " up", " the"],
            candidates=_candidates_from_probabilities(
                [
                    ("mug", 0.35),
                    ("cup", 0.22),
                    ("bowl", 0.16),
                    ("robot", 0.09),
                    ("blue", 0.07),
                    ("floor", 0.05),
                    ("banana", 0.04),
                    ("other", 0.02),
                ]
            ),
            default_options=DecodingOptions(
                selection_rule="top_p",
                top_k=3,
                top_p=0.7,
                seed=9414,
            ),
            sequence_search=SequenceSearchExample(
                title="When the locally best token loses",
                subtitle=(
                    "This two-step teaching tree narrows the first choice to mug and cup, "
                    "then compares complete continuations by cumulative log-probability."
                ),
                beam_width=2,
                nodes=[
                    SequenceSearchNode(node_id="context"),
                    SequenceSearchNode(
                        node_id="mug",
                        parent_id="context",
                        token=" mug",
                        conditional_probability=35 / 57,
                    ),
                    SequenceSearchNode(
                        node_id="cup",
                        parent_id="context",
                        token=" cup",
                        conditional_probability=22 / 57,
                    ),
                    SequenceSearchNode(
                        node_id="mug_carefully",
                        parent_id="mug",
                        token=" carefully",
                        conditional_probability=0.55,
                        terminal=True,
                    ),
                    SequenceSearchNode(
                        node_id="mug_quickly",
                        parent_id="mug",
                        token=" quickly",
                        conditional_probability=0.45,
                        terminal=True,
                    ),
                    SequenceSearchNode(
                        node_id="cup_safely",
                        parent_id="cup",
                        token=" safely",
                        conditional_probability=0.95,
                        terminal=True,
                    ),
                    SequenceSearchNode(
                        node_id="cup_slowly",
                        parent_id="cup",
                        token=" slowly",
                        conditional_probability=0.05,
                        terminal=True,
                    ),
                ],
            ),
            metadata={
                "source": "Foundation Models lecture mini-activity: Decoding Choices",
                "scores_are_precomputed": True,
                "related_tokenisation_example": "decoding_context",
            },
        ),
        DecodingExample(
            name="peaked_distribution",
            title="Peaked distribution",
            subtitle="One candidate dominates, so low temperature makes the preference even sharper.",
            context_tokens=["The", " capital", " of", " France", " is"],
            candidates=_candidates_from_probabilities(
                [
                    ("Paris", 0.82),
                    ("Lyon", 0.06),
                    ("London", 0.04),
                    ("Berlin", 0.03),
                    ("located", 0.02),
                    ("a", 0.015),
                    ("France", 0.01),
                    ("other", 0.005),
                ]
            ),
            default_options=DecodingOptions(
                selection_rule="greedy",
                temperature=0.7,
                top_k=3,
                top_p=0.9,
                seed=9414,
            ),
            metadata={
                "scores_are_precomputed": True,
                "related_tokenisation_example": "capital_context",
            },
        ),
        DecodingExample(
            name="flat_distribution",
            title="Flat distribution",
            subtitle="Several candidates are plausible, making seeded sampling visibly consequential.",
            context_tokens=["The", " robot", " could"],
            candidates=_candidates_from_probabilities(
                [
                    ("move", 0.16),
                    ("wait", 0.15),
                    ("turn", 0.14),
                    ("pick", 0.13),
                    ("scan", 0.12),
                    ("signal", 0.11),
                    ("stop", 0.10),
                    ("other", 0.09),
                ]
            ),
            default_options=DecodingOptions(
                selection_rule="sampling",
                temperature=1.3,
                top_k=4,
                top_p=0.8,
                seed=9414,
            ),
            metadata={"scores_are_precomputed": True},
        ),
        DecodingExample(
            name="long_tail_distribution",
            title="Long-tail distribution",
            subtitle="Top-p adapts the candidate-set size while removing a low-probability tail.",
            context_tokens=["For", " the", " project", ",", " we", " should"],
            candidates=_candidates_from_probabilities(
                [
                    ("plan", 0.28),
                    ("use", 0.18),
                    ("build", 0.13),
                    ("first", 0.10),
                    ("consider", 0.08),
                    ("test", 0.06),
                    ("ask", 0.05),
                    ("document", 0.04),
                    ("compare", 0.03),
                    ("revisit", 0.025),
                    ("carefully", 0.02),
                    ("other", 0.005),
                ]
            ),
            default_options=DecodingOptions(
                selection_rule="top_p",
                temperature=1.0,
                top_k=5,
                top_p=0.9,
                seed=9414,
            ),
            metadata={"scores_are_precomputed": True},
        ),
    ]
    return {example.name: example for example in examples}


def _candidates_from_probabilities(
    entries: list[tuple[str, float]],
) -> list[DecodingCandidate]:
    """Encode a readable curated distribution as fixed logits."""

    return [
        DecodingCandidate(token=token, logit=math.log(probability))
        for token, probability in entries
    ]
