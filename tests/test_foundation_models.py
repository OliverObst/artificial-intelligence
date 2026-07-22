from fastapi.testclient import TestClient

from ai9414.core.server import create_fastapi_app
from ai9414.foundation_models import (
    TokenisationExplorer,
    apply_bpe,
    learn_bpe_merges,
    tokenize_characters,
    tokenize_words,
)
from ai9414.foundation_models.models import TokenisationProblem
from ai9414.foundation_models.student import (
    build_bpe_learning_states,
    tokenize_bpe_units,
)
from ai9414.foundation_models.trace import build_foundation_trace


def test_tokenisation_explorer_lists_curated_examples():
    app = TokenisationExplorer()
    assert app.list_examples() == [
        "simple_sentence",
        "typo_sentence",
        "rare_names",
        "code_example",
        "german_compound",
        "mixed_symbols",
        "mixed_language",
    ]


def test_tokenisation_trace_uses_foundation_app_type():
    app = TokenisationExplorer()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "foundation_models"
    assert trace["initial_state"]["foundation_models"]["mode"] == "bpe"
    assert (
        trace["initial_state"]["foundation_models"]["explorer_kind"] == "tokenisation"
    )
    assert trace["summary"]["result"] == "tokenised"


def test_tokenisation_modes_and_custom_text_round_trip():
    app = TokenisationExplorer()
    app.set_options(tokeniser_mode="word", num_merges=8, context_window=128)
    app.set_text("Deliver parcel to Office B.")
    payload = app.build_state_payload()
    assert payload["data"]["foundation_models"]["mode"] == "word"
    assert payload["data"]["foundation_models"]["text"] == "Deliver parcel to Office B."
    assert payload["data"]["foundation_models"]["stats"]["context_window"] == 128


def test_student_tokenisers_return_reasonable_tokens():
    assert tokenize_characters("A B.") == ["A", " ", "B", "."]
    assert tokenize_words("Room A-17 costs $12.50.") == [
        "Room",
        "A",
        "-",
        "17",
        "costs",
        "$",
        "12",
        ".",
        "50",
        ".",
    ]
    assert tokenize_bpe_units("  Hello, world!\n") == [
        "  Hello",
        ",",
        " world",
        "!",
        "\n",
    ]
    merges = learn_bpe_merges(["banana bandana"], 8)
    assert merges
    bpe_tokens = apply_bpe("banana bandana", merges)
    assert "".join(bpe_tokens) == "banana bandana"
    assert " bandana" in bpe_tokens


def test_bpe_learning_states_are_canonical_and_explain_ties():
    states = build_bpe_learning_states(["ab ac"], 2)
    assert learn_bpe_merges(["ab ac"], 2) == states[-1]["learned_merges"]
    assert states[1]["selected_pair"] == (" ", "a")
    assert states[1]["tied_candidate_count"] == 3

    trace = build_foundation_trace(
        TokenisationProblem(
            title="Tie example",
            subtitle="Deterministic BPE tie-breaking.",
            text="ab ac",
            corpus_name="tie_example",
            corpus_texts=["ab ac"],
            tokeniser_mode="bpe",
            num_merges=1,
            context_window=32,
        )
    ).model_dump()
    assert "3 pairs share that frequency" in trace["steps"][0]["annotation"]
    selected_pair = trace["steps"][0]["state_patch"]["foundation_models"]["bpe"][
        "selected_pair"
    ]
    assert selected_pair["display_left"] == "▁"
    assert (
        selected_pair["tie_break_rule"]
        == "highest frequency, then alphabetical symbol-pair order"
    )


def test_token_rows_use_visible_whitespace_without_claiming_vocabulary_ids():
    app = TokenisationExplorer()
    app.set_tokeniser_mode("character")
    app.set_text("A B")
    foundation = app.build_state_payload()["data"]["foundation_models"]

    assert [token["text"] for token in foundation["tokens"]] == ["A", " ", "B"]
    assert foundation["tokens"][1]["display_text"] == "▁"
    assert foundation["tokens"][1]["accessible_label"] == "space"
    assert all("token_id" not in token for token in foundation["tokens"])
    assert foundation["stats"]["token_budget_is_illustrative"] is True
    assert foundation["whitespace_legend"].startswith(
        "In token displays, ▁ marks a space"
    )


def test_bpe_round_trips_every_curated_example():
    app = TokenisationExplorer()
    for example in app.examples.values():
        corpus = app.corpora[example.default_corpus]
        merges = learn_bpe_merges(corpus.texts, 12)
        assert "".join(apply_bpe(example.text, merges)) == example.text


def test_foundation_models_fastapi_routes_work():
    app = TokenisationExplorer()
    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "foundation_models"

        page = client.get("/")
        assert page.status_code == 200
        assert (
            'id="foundation-panel" class="foundation-panel hidden" role="region"'
            in page.text
        )
        assert (
            'id="foundation-text-panel" class="foundation-panel hidden" role="region"'
            in page.text
        )
        assert (
            'id="step-explanation-live" role="status" aria-live="polite"' in page.text
        )
