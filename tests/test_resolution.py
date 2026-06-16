from fastapi.testclient import TestClient

from ai9414.core.server import create_fastapi_app
from ai9414.resolution import ResolutionDemo
from ai9414.resolution.solver import resolve_pair


def test_resolution_demo_lists_examples():
    app = ResolutionDemo()
    assert app.list_examples() == [
        "modus_ponens_refutation",
        "chain_refutation",
        "wumpus_no_breeze",
        "wumpus_forced_pit",
    ]


def test_chain_refutation_reaches_empty_clause():
    app = ResolutionDemo(example="chain_refutation")
    trace = app.get_trace_payload()
    assert trace["app_type"] == "resolution"
    assert trace["summary"]["result"] == "refuted"
    assert trace["steps"][-1]["event_type"] == "finished"
    assert trace["steps"][-2]["event_type"] == "empty_clause"
    assert trace["steps"][-2]["state_patch"]["resolution"]["summary"]["empty_clause_found"] is True


def test_wumpus_forced_pit_resolution_example_has_visualisation():
    app = ResolutionDemo(example="wumpus_forced_pit")
    trace = app.get_trace_payload()
    assert trace["summary"]["result"] == "refuted"
    visualisation = trace["initial_state"]["resolution"]["visualisation"]
    assert visualisation["kind"] == "wumpus"
    assert [3, 1] in visualisation["entailed_pits"]


def test_custom_proof_attempt_can_be_loaded_from_python():
    app = ResolutionDemo()
    app.load_proof_attempt(
        [["~A", "B"], ["A"], ["~B"]],
        [{"left": 1, "right": 2, "pivot": "A"}, {"left": 4, "right": 3, "pivot": "B"}],
    )
    trace = app.get_trace_payload()
    assert trace["summary"]["result"] == "refuted"
    assert trace["steps"][-2]["state_patch"]["resolution"]["clauses"][-1]["expression"] == "□"


def test_invalid_resolution_attempt_is_visualised():
    app = ResolutionDemo()
    app.load_proof_attempt([["A"], ["B"]], [{"left": 1, "right": 2, "pivot": "A"}])
    trace = app.get_trace_payload()
    assert trace["summary"]["result"] == "invalid_attempt"
    assert trace["steps"][1]["event_type"] == "invalid_step"


def test_resolve_pair_builds_expected_resolvent():
    resolvent, warning = resolve_pair(["~A", "B"], ["A"], "A")
    assert resolvent == ["B"]
    assert warning is None


def test_resolution_fastapi_custom_attempt_command():
    app = ResolutionDemo()
    with TestClient(create_fastapi_app(app)) as client:
        response = client.post(
            "/api/action",
            json={
                "action": "app_command",
                "payload": {
                    "command": "load_resolution_attempt",
                    "clauses": "~A or B\nA\n~B",
                    "steps": "1, 2, A\n4, 3, B",
                },
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["trace"]["summary"]["result"] == "refuted"
