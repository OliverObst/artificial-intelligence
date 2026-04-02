from fastapi.testclient import TestClient

from ai9414.core.server import create_fastapi_app
from ai9414.foundation_models import (
    TokenisationExplorer,
    apply_bpe,
    learn_bpe_merges,
    tokenize_characters,
    tokenize_words,
)


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
    assert tokenize_characters("A B.") == ["A", "B", "."]
    assert tokenize_words("Room A-17 costs $12.50.") == ["Room", "A", "-", "17", "costs", "$", "12", ".", "50", "."]
    merges = learn_bpe_merges(["banana bandana"], 4)
    assert merges
    assert apply_bpe("banana", merges)


def test_foundation_models_fastapi_routes_work():
    app = TokenisationExplorer()
    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "foundation_models"
