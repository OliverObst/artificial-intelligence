import json
import math

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ai9414.core.server import create_fastapi_app
from ai9414.foundation_models import (
    DecodingExplorer,
    apply_temperature,
    greedy_select,
    repeated_sample_counts,
    renormalise,
    sample_from_draw,
    seeded_sample,
    softmax,
    top_k_filter,
    top_p_filter,
)
from ai9414.foundation_models.examples import build_decoding_examples
from ai9414.foundation_models.models import (
    DecodingCandidate,
    DecodingExample,
    DecodingOptions,
    DecodingProblem,
    SequenceSearchExample,
    SequenceSearchNode,
)
from ai9414.foundation_models.sequence_search import (
    build_sequence_search_comparison,
)


def test_softmax_is_stable_and_temperature_changes_entropy():
    assert softmax([1000.0, 1001.0]) == pytest.approx([0.2689414214, 0.7310585786])

    logits = [2.0, 1.0, -0.5]
    low_temperature = softmax(apply_temperature(logits, 0.5))
    base_temperature = softmax(apply_temperature(logits, 1.0))
    high_temperature = softmax(apply_temperature(logits, 2.0))

    assert _entropy(low_temperature) < _entropy(base_temperature)
    assert _entropy(base_temperature) < _entropy(high_temperature)
    assert math.fsum(low_temperature) == pytest.approx(1.0)
    assert math.fsum(high_temperature) == pytest.approx(1.0)


def test_top_k_filter_retains_exact_count_with_stable_tie_breaking():
    filtered = top_k_filter([0.4, 0.2, 0.2, 0.2], 2)
    assert filtered == pytest.approx([0.4, 0.2, 0.0, 0.0])
    assert sum(probability > 0.0 for probability in filtered) == 2
    assert renormalise(filtered) == pytest.approx([2 / 3, 1 / 3, 0.0, 0.0])
    with pytest.raises(ValueError, match="candidate count"):
        top_k_filter([0.6, 0.4], 3)


def test_top_p_filter_uses_smallest_threshold_reaching_prefix():
    probabilities = [0.35, 0.22, 0.16, 0.09, 0.07, 0.05, 0.04, 0.02]

    assert top_p_filter(probabilities, 0.70) == pytest.approx(
        [0.35, 0.22, 0.16, 0.0, 0.0, 0.0, 0.0, 0.0]
    )
    assert top_p_filter(probabilities, 0.57) == pytest.approx(
        [0.35, 0.22, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    )
    assert top_p_filter([0.1, 0.6, 0.3], 0.65) == pytest.approx([0.0, 0.6, 0.3])


def test_greedy_and_seeded_sampling_are_deterministic():
    probabilities = [0.4, 0.35, 0.25]
    assert greedy_select(probabilities) == 0
    assert greedy_select([0.5, 0.5]) == 0
    assert seeded_sample(probabilities, 9414) == seeded_sample(probabilities, 9414)
    assert sample_from_draw(probabilities, 0.0) == 0
    assert sample_from_draw(probabilities, 0.4) == 1
    assert sample_from_draw(probabilities, 0.75) == 2


def test_repeated_sampling_histogram_is_seeded_and_conserves_draws():
    probabilities = [0.5, 0.3, 0.2]
    first = repeated_sample_counts(probabilities, seed=17, sample_count=500)
    second = repeated_sample_counts(probabilities, seed=17, sample_count=500)

    assert first == second
    assert sum(first) == 500
    assert all(count >= 0 for count in first)
    with pytest.raises(ValueError, match="sample_count"):
        repeated_sample_counts(probabilities, seed=17, sample_count=0)


def test_sequence_search_compares_local_and_cumulative_scores():
    example = build_decoding_examples()["lecture_activity"].sequence_search
    assert example is not None

    comparison = build_sequence_search_comparison(example)

    assert comparison["greedy_result"]["sequence"] == "mug carefully"
    assert comparison["beam_result"]["sequence"] == "cup safely"
    assert (
        comparison["beam_result"]["cumulative_log_probability"]
        > comparison["greedy_result"]["cumulative_log_probability"]
    )
    assert comparison["beam_result"] == comparison["globally_best_result"]
    assert len(comparison["beam_steps"]) == 2
    assert sum(node["globally_best"] for node in comparison["nodes"]) == 1


def test_sequence_search_model_rejects_invalid_tree_probability_mass():
    with pytest.raises(ValidationError, match="sum to one"):
        SequenceSearchExample(
            title="Invalid tree",
            subtitle="Children do not form a distribution.",
            nodes=[
                SequenceSearchNode(node_id="root"),
                SequenceSearchNode(
                    node_id="left",
                    parent_id="root",
                    token=" left",
                    conditional_probability=0.7,
                    terminal=True,
                ),
                SequenceSearchNode(
                    node_id="right",
                    parent_id="root",
                    token=" right",
                    conditional_probability=0.2,
                    terminal=True,
                ),
            ],
        )


def test_decoding_models_reject_invalid_candidates_and_options():
    with pytest.raises(ValidationError, match="finite"):
        DecodingCandidate(token="mug", logit=float("nan"))
    with pytest.raises(ValidationError, match="temperature"):
        DecodingOptions(temperature=0.0)
    with pytest.raises(ValidationError, match="top_p"):
        DecodingOptions(top_p=1.1)
    with pytest.raises(ValidationError, match="unique"):
        DecodingExample(
            name="duplicate",
            title="Duplicate",
            subtitle="Invalid duplicate candidates.",
            context_tokens=["Context"],
            candidates=[
                DecodingCandidate(token="same", logit=1.0),
                DecodingCandidate(token="same", logit=0.0),
            ],
        )
    with pytest.raises(ValidationError, match="top_k"):
        DecodingProblem(
            title="Too few",
            subtitle="Top-k exceeds the candidate set.",
            context_tokens=["Context"],
            candidates=[
                DecodingCandidate(token="A", logit=1.0),
                DecodingCandidate(token="B", logit=0.0),
            ],
            options=DecodingOptions(top_k=3),
        )


def test_default_decoding_example_matches_the_lecture_activity():
    example = build_decoding_examples()["lecture_activity"]
    assert [candidate.token for candidate in example.candidates] == [
        "mug",
        "cup",
        "bowl",
        "robot",
        "blue",
        "floor",
        "banana",
        "other",
    ]
    assert softmax(
        [candidate.logit for candidate in example.candidates]
    ) == pytest.approx([0.35, 0.22, 0.16, 0.09, 0.07, 0.05, 0.04, 0.02])
    assert example.metadata["scores_are_precomputed"] is True


def test_decoding_trace_replays_every_conceptual_stage():
    app = DecodingExplorer()
    trace = app.get_trace_payload()
    initial = trace["initial_state"]["foundation_models"]

    assert initial["explorer_kind"] == "decoding"
    assert initial["stage"] == "model_scores"
    assert initial["scores_are_precomputed"] is True
    assert initial["arbitrary_text_supported"] is False
    assert initial["candidate_scores"][0]["transformed_probability"] is None
    assert [step["event_type"] for step in trace["steps"]] == [
        "temperature",
        "filtering",
        "renormalisation",
        "selection",
    ]

    temperature = trace["steps"][0]["state_patch"]["foundation_models"]
    filtering = trace["steps"][1]["state_patch"]["foundation_models"]
    renormalisation = trace["steps"][2]["state_patch"]["foundation_models"]
    selection = trace["steps"][3]["state_patch"]["foundation_models"]

    assert temperature["candidate_scores"][0]["transformed_probability"] is not None
    assert temperature["candidate_scores"][0]["retained"] is None
    assert filtering["retained_count"] == 3
    assert [
        row["token"] for row in filtering["candidate_scores"] if row["retained"]
    ] == ["mug", "cup", "bowl"]
    assert math.fsum(
        row["renormalised_probability"] for row in renormalisation["candidate_scores"]
    ) == pytest.approx(1.0)
    assert selection["random_draw"] is not None
    assert sum(row["selected"] for row in selection["candidate_scores"]) == 1
    assert selection["selected_token"]["token"] in {"mug", "cup", "bowl"}
    assert trace["summary"] == {"step_count": 4, "result": "token_selected"}


def test_decoding_options_rebuild_the_trace_and_return_structured_errors():
    app = DecodingExplorer()
    response = app.handle_action(
        {
            "action": "set_option",
            "payload": {
                "selection_rule": "top_k",
                "top_k": 2,
                "temperature": 0.5,
                "seed": 7,
            },
        }
    )
    assert response["ok"] is True
    filtering = response["trace"]["steps"][1]["state_patch"]["foundation_models"]
    assert filtering["selection_rule"] == "top_k"
    assert filtering["retained_count"] == 2

    invalid = app.handle_action(
        {"action": "set_option", "payload": {"temperature": 0.0}}
    )
    assert invalid["ok"] is False
    assert invalid["error"]["code"] == "invalid_option_value"

    histogram = app.handle_action(
        {
            "action": "set_option",
            "payload": {
                "selection_rule": "sampling",
                "show_sampling_histogram": True,
            },
        }
    )
    histogram_data = histogram["trace"]["initial_state"]["foundation_models"][
        "sampling_histogram"
    ]
    assert histogram_data["sample_count"] == 200
    assert sum(row["count"] for row in histogram_data["rows"]) == 200


def test_decoding_fastapi_contract_and_static_export(tmp_path):
    app = DecodingExplorer()
    with TestClient(create_fastapi_app(app)) as client:
        manifest = client.get("/api/manifest")
        assert manifest.status_code == 200
        assert manifest.json()["app_title"].endswith("Decoding Explorer")

        page = client.get("/")
        assert page.status_code == 200
        assert 'id="foundation-decoding-controls"' in page.text
        assert 'id="foundation-decoding-rule-select"' in page.text
        assert 'id="foundation-temperature-input"' in page.text
        assert 'id="foundation-top-k-control"' in page.text
        assert 'id="foundation-top-p-control"' in page.text
        assert 'id="foundation-seed-control"' in page.text
        assert 'id="foundation-sampling-histogram-input"' in page.text
        assert 'data-foundation-pipeline-stage="decoding"' in page.text

        script = client.get("/assets/app.js")
        assert script.status_code == 200
        assert "function renderDecodingDistribution" in script.text
        assert "function renderDecodingContext" in script.text
        assert "function renderSequenceSearch" in script.text
        assert "function renderSamplingHistogram" in script.text
        assert "function appendFoundationTeachingExtensions" in script.text
        assert 'makeDecodingElement("table", "decoding-table")' in script.text
        assert "arbitrary custom text cannot be submitted" in script.text
        assert 'selection_rule: event.target.value' in script.text
        assert 'show_sampling_histogram: event.target.checked' in script.text

        stylesheet = client.get("/assets/style.css")
        assert stylesheet.status_code == 200
        assert ".decoding-chart-row" in stylesheet.text
        assert ".decoding-table tbody th::before" in stylesheet.text
        assert ".foundation-decoding-controls" in stylesheet.text
        assert ".sequence-tree-group" in stylesheet.text
        assert ".decoding-histogram-chart" in stylesheet.text
        assert ".foundation-related-card" in stylesheet.text

        state = client.get("/api/state")
        assert state.status_code == 200
        assert state.json()["data"]["foundation_models"]["explorer_kind"] == "decoding"

        trace = client.get("/api/trace")
        assert trace.status_code == 200
        assert trace.json()["trace_id"] == "foundation-models-decoding-trace"

        exercises = client.get("/api/exercises")
        assert exercises.status_code == 200
        assert exercises.json()["explorer_kind"] == "decoding"
        assert {item["id"] for item in exercises.json()["exercises"]} == {
            "predict-filtered-set",
            "explain-beam-result",
        }

        notes = client.get("/api/instructor-notes")
        assert notes.status_code == 200
        assert notes.json()["notes"][0]["id"] == "scores-versus-rule"

    bundle_dir = app.export_solution_bundle(tmp_path / "decoding-solution")
    exported_trace = json.loads((bundle_dir / "trace.json").read_text(encoding="utf-8"))
    foundation = exported_trace["initial_state"]["foundation_models"]
    assert foundation["explorer_kind"] == "decoding"
    assert foundation["scores_are_precomputed"] is True
    assert foundation["sequence_search"]["beam_result"]["sequence"] == "cup safely"
    assert foundation["related_example"]["target_example"] == "decoding_context"
    assert foundation["teaching_extensions"]["student_exercises"]
    assert exported_trace["steps"][-1]["event_type"] == "selection"
    exported_page = (bundle_dir / "index.html").read_text(encoding="utf-8")
    exported_script = (bundle_dir / "app.js").read_text(encoding="utf-8")
    exported_stylesheet = (bundle_dir / "student-assets" / "style.css").read_text(
        encoding="utf-8"
    )
    assert 'data-foundation-pipeline-stage="scores"' in exported_page
    assert "function renderDecodingDistribution" in exported_script
    assert "function renderSequenceSearch" in exported_script
    assert "function appendFoundationTeachingExtensions" in exported_script
    assert "function renderFoundationPipeline" in exported_script
    assert ".decoding-draw-marker" in exported_stylesheet
    assert ".sequence-result-card" in exported_stylesheet


def test_decoding_explorer_loads_a_validated_config(tmp_path):
    config_path = tmp_path / "decoding.json"
    config_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "app_type": "foundation_models",
                "title": "Configured decoding distribution",
                "options": {
                    "selection_rule": "top_k",
                    "top_k": 2,
                    "temperature": 0.8,
                    "seed": 12,
                },
                "data": {
                    "title": "Configured decoding distribution",
                    "subtitle": "Three fixed candidate logits.",
                    "context_tokens": ["The", " answer", " is"],
                    "candidates": [
                        {"token": "A", "logit": 2.0},
                        {"token": "B", "logit": 1.0},
                        {"token": "C", "logit": 0.0},
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    app = DecodingExplorer()
    app.load_config(str(config_path))
    state = app.build_state_payload()
    assert state["config_name"] == "decoding.json"
    assert state["example_name"] is None
    assert state["data"]["options"]["selection_rule"] == "top_k"
    assert state["data"]["foundation_models"]["context_text"] == "The answer is"


def _entropy(probabilities: list[float]) -> float:
    return -math.fsum(
        probability * math.log(probability)
        for probability in probabilities
        if probability > 0.0
    )
