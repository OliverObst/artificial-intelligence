"""Curated examples and corpora for the tokenisation explorer."""

from __future__ import annotations

from ai9414.foundation_models.models import TokenisationCorpus, TokenisationExample


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
