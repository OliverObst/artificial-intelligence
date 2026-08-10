from importlib import resources

from fastapi.testclient import TestClient

from ai9414.core.server import create_fastapi_app
from ai9414.uncertainty import BayesFilterDemo, run_uncertainty_solver
from ai9414.uncertainty.student import validate_uncertainty_payload


def test_bayes_filter_demo_lists_curated_examples():
    app = BayesFilterDemo()
    assert app.list_examples() == [
        "two_doors",
        "ambiguous_corridor",
        "bad_sensor",
        "slippery_floor",
        "confident_but_wrong",
    ]


def test_bayes_filter_default_state_is_uniform_corridor():
    app = BayesFilterDemo()
    payload = app.build_state_payload()
    uncertainty = payload["data"]["uncertainty"]
    assert uncertainty["cell_count"] == 10
    assert uncertainty["posterior_belief"] == [0.1] * 10
    assert uncertainty["landmarks"] == {"door": [1, 5]}
    assert uncertainty["show_true_position"] is True


def test_sensor_update_concentrates_door_cells():
    app = BayesFilterDemo()
    response = app.handle_app_command("sense", {"landmark": "door", "present": True})
    uncertainty = response["state"]["data"]["uncertainty"]
    assert response["trace"]["steps"][-1]["event_type"] == "sensor_update"
    assert uncertainty["most_likely_cell"] == 2
    assert uncertainty["posterior_belief"][1] > uncertainty["posterior_belief"][0]
    assert round(sum(uncertainty["posterior_belief"]), 6) == 1.0


def test_motion_update_shifts_and_spreads_belief():
    app = BayesFilterDemo()
    app.handle_app_command("sense", {"landmark": "door", "present": True})
    response = app.handle_app_command("move", {"direction": "right"})
    uncertainty = response["state"]["data"]["uncertainty"]
    assert response["trace"]["steps"][-1]["event_type"] == "motion_update"
    assert uncertainty["current_action"] == "move_right"
    assert uncertainty["transition_rows"][0]["entries"]
    assert round(sum(uncertainty["posterior_belief"]), 6) == 1.0


def test_move_and_sense_adds_motion_then_sampled_sensor_update():
    app = BayesFilterDemo()
    response = app.handle_app_command("move_and_sense", {"direction": "right", "landmark": "door"})
    trace_steps = response["trace"]["steps"]
    uncertainty = response["state"]["data"]["uncertainty"]

    assert [step["event_type"] for step in trace_steps[-2:]] == ["motion_update", "sensor_update"]
    assert uncertainty["current_observation"] in {"door", "no_door"}
    assert "sampled the door sensor" in response["message"]
    assert round(sum(uncertainty["posterior_belief"]), 6) == 1.0


def test_reset_all_keeps_trace_payload_available():
    app = BayesFilterDemo()
    app.handle_app_command("move_and_sense", {"direction": "right", "landmark": "door"})
    response = app.handle_app_command("reset_all", {})
    trace = app.get_trace_payload()

    assert response["state"]["view"]["current_step"] == 0
    assert trace["steps"] == []
    assert trace["initial_state"]["uncertainty"]["posterior_belief"] == [0.1] * 10


def test_move_after_reset_all_starts_from_initial_belief():
    app = BayesFilterDemo(
        motion_success=0.5,
        motion_stay=0.5,
        motion_overshoot=0.0,
    )
    app.handle_app_command("move", {"direction": "right"})
    app.handle_app_command("move", {"direction": "right"})
    app.handle_app_command("reset_all", {})

    response = app.handle_app_command("move", {"direction": "left"})
    fresh_response = BayesFilterDemo(
        motion_success=0.5,
        motion_stay=0.5,
        motion_overshoot=0.0,
    ).handle_app_command("move", {"direction": "left"})

    assert len(response["trace"]["steps"]) == 1
    assert (
        response["state"]["data"]["uncertainty"]["posterior_belief"]
        == fresh_response["state"]["data"]["uncertainty"]["posterior_belief"]
    )
    assert (
        response["state"]["data"]["uncertainty"]["current_true_position"]
        == fresh_response["state"]["data"]["uncertainty"]["current_true_position"]
    )


def test_standard_reset_action_clears_uncertainty_runtime_state():
    app = BayesFilterDemo()
    app.handle_app_command("move", {"direction": "right"})

    reset_response = app.handle_action({"action": "reset"})
    move_response = app.handle_app_command("move", {"direction": "left"})

    assert reset_response["trace"]["steps"] == []
    assert reset_response["state"]["view"]["current_step"] == 0
    assert len(move_response["trace"]["steps"]) == 1


def test_main_reset_clears_uncertainty_backend_state():
    app_js = (
        resources.files("ai9414.frontend")
        .joinpath("student")
        .joinpath("app.js")
        .read_text(encoding="utf-8")
    )

    reset_handler = app_js.split('$("reset-button").addEventListener', maxsplit=1)[1]
    reset_handler = reset_handler.split('$("reload-button").addEventListener', maxsplit=1)[0]

    assert 'state.player.mode !== "live"' in reset_handler
    assert 'await runUncertaintyCommand("reset_all")' in reset_handler


def test_bayes_filter_exercise_factory_hides_true_position():
    app = BayesFilterDemo.exercise("sensor_update")
    payload = app.build_state_payload()
    assert app.mode == "exercise"
    assert payload["data"]["uncertainty"]["show_true_position"] is False


def test_uncertainty_student_payload_validation_round_trips_problem():
    app = BayesFilterDemo.example("two_doors")
    problem = validate_uncertainty_payload(app.build_state_payload()["data"]["uncertainty_problem"])
    assert problem["title"] == "Two identical doors"
    assert problem["cells"] == 10
    assert run_uncertainty_solver


def test_uncertainty_fastapi_routes_work():
    app = BayesFilterDemo()
    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "uncertainty"
