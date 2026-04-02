from fastapi.testclient import TestClient

from ai9414.core.server import create_fastapi_app
from ai9414.uncertainty import BeliefStateExplorer, run_uncertainty_solver
from ai9414.uncertainty.student import validate_uncertainty_payload


def test_uncertainty_demo_lists_curated_examples():
    app = BeliefStateExplorer()
    assert app.list_examples() == [
        "office_localisation_basic",
        "office_localisation_motion_noise",
        "office_localisation_ambiguous_sensor",
        "office_localisation_repeated_evidence",
    ]


def test_uncertainty_trace_exposes_bayes_update_state():
    app = BeliefStateExplorer()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "uncertainty"
    assert trace["summary"]["result"] == "posterior ready"
    assert trace["steps"][0]["event_type"] == "bayes_update"
    assert trace["steps"][0]["state_patch"]["uncertainty"]["current_action"] == "move_to_mail_room"


def test_uncertainty_set_belief_updates_initial_state():
    app = BeliefStateExplorer()
    app.set_belief(
        {
            "mail_room": 0.1,
            "office_a": 0.4,
            "corridor": 0.2,
            "office_b": 0.2,
            "lab": 0.1,
        }
    )
    payload = app.build_state_payload()
    assert payload["data"]["uncertainty"]["posterior_belief"]["office_a"] == 0.4


def test_uncertainty_step_advances_replay_and_validates_action():
    app = BeliefStateExplorer()
    payload = app.step(action="move_to_mail_room")
    assert payload["view"]["current_step"] == 1
    assert payload["data"]["uncertainty"]["step_index"] == 1


def test_uncertainty_student_payload_validation_round_trips_problem():
    app = BeliefStateExplorer()
    problem = validate_uncertainty_payload(app.build_state_payload()["data"]["uncertainty_problem"])
    assert problem["title"] == "Office localisation baseline"
    assert len(problem["scripted_steps"]) == 3
    assert run_uncertainty_solver


def test_uncertainty_fastapi_routes_work():
    app = BeliefStateExplorer()
    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "uncertainty"
