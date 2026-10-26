from importlib import resources
import sys
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

from ai9414.core.server import create_fastapi_app
from ai9414.uncertainty import BayesFilterDemo, run_uncertainty_solver
from ai9414.uncertainty.student import validate_uncertainty_payload
from ai9414.uncertainty.models import SensorModel
from ai9414.uncertainty.trace import (
    reference_motion_update_right,
    reference_normalise,
)


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


def test_two_door_trace_preserves_both_maxima():
    app = BayesFilterDemo.example("two_doors")
    initial = app.build_state_payload()["data"]["uncertainty"]
    assert initial["most_likely_cells"] == list(range(1, 11))
    for command, payload, maxima in [
        ("sense", {"landmark": "door", "present": True}, [2, 6]),
        ("move", {"direction": "right"}, [3, 7]),
        ("sense", {"landmark": "door", "present": False}, [3, 7]),
    ]:
        data = app.handle_app_command(command, payload)["state"]["data"]["uncertainty"]
        assert data["most_likely_cells"] == maxima
        assert [row["cell"] for row in data["cells"] if row["is_most_likely"]] == maxima
        assert data["history"][-1]["most_likely_cells"] == maxima
    assert data["most_likely_probability"] == pytest.approx(0.2407079646)


@pytest.mark.parametrize("hit,false_alarm,informative", [(0.8, 0.2, True), (0.45, 0.5, True), (0.5, 0.5, False)])
def test_sensor_information_depends_on_different_likelihoods(hit, false_alarm, informative):
    assert SensorModel(hit=hit, false_alarm=false_alarm).informative is informative
    app = BayesFilterDemo(sensor_hit=hit, sensor_false_alarm=false_alarm)
    data = app.handle_app_command("sense", {"landmark": "door", "present": True})["state"]["data"]["uncertainty"]
    if hit == false_alarm:
        assert data["posterior_belief"] == pytest.approx([0.1] * 10)
        assert "equal hit and false alarm" in data["warning"]
    elif hit < false_alarm:
        assert data["posterior_belief"][1] < 0.1
        assert "reversed evidence" in data["warning"]
        assert "uninformative" not in data["warning"]
    else:
        assert data["posterior_belief"][1] > 0.1
        assert not data["warning"]


@pytest.fixture
def uncertainty_stub(tmp_path, monkeypatch):
    demo = BayesFilterDemo()
    path = demo.write_stub(tmp_path / "week7_bayes_filter_stub.py")
    with TestClient(create_fastapi_app(demo)) as client:
        response = client.get("/assets/week7_bayes_filter_stub.py")
        assert response.status_code == 200
        assert response.text == path.read_text()
    module = ModuleType("week7_bayes_filter_stub")
    monkeypatch.setitem(sys.modules, module.__name__, module)
    exec(compile(response.text, str(path), "exec"), module.__dict__)
    return module


def solver_client(stub, monkeypatch):
    apps = []
    monkeypatch.setattr("ai9414.uncertainty.student.uvicorn.run", lambda app, **kwargs: apps.append(app))
    stub.run_live()
    return TestClient(apps[0])


def complete_stub(stub):
    stub.normalise = reference_normalise
    stub.motion_update_right = reference_motion_update_right

    def sensor_update(belief, corridor, sensor, sees_door):
        likelihoods = [sensor.hit if i in corridor.door_cells else sensor.false_alarm for i in range(corridor.cells)]
        if not sees_door:
            likelihoods = [1 - value for value in likelihoods]
        return stub.normalise([p * likelihood for p, likelihood in zip(belief, likelihoods)])

    stub.sensor_update = sensor_update


def test_unfinished_download_starts_solver_and_reports_missing_function(uncertainty_stub, monkeypatch):
    with solver_client(uncertainty_stub, monkeypatch) as client:
        response = client.post("/solve", json={"problem": BayesFilterDemo().problem.model_dump()})
    assert response.status_code == 400
    assert "Implement normalise" in response.json()["message"]


@pytest.mark.parametrize("example", ["two_doors", "ambiguous_corridor", "bad_sensor", "slippery_floor", "confident_but_wrong"])
def test_completed_download_solves_all_browser_examples(uncertainty_stub, monkeypatch, example):
    complete_stub(uncertainty_stub)
    problem = BayesFilterDemo.example(example).problem
    with solver_client(uncertainty_stub, monkeypatch) as client:
        response = client.post("/solve", json={"problem": problem.model_dump()})
    assert response.status_code == 200, response.text
    trace = response.json()["trace_bundle"]
    assert len(trace["steps"]) == len(problem.scripted_events)
    assert trace["is_complete"] is True


def test_download_standalone_checks_and_demo(uncertainty_stub, capsys):
    complete_stub(uncertainty_stub)
    uncertainty_stub.run_checks()
    uncertainty_stub.run_demo()
    output = capsys.readouterr().out
    assert "All checks passed." in output
    assert "Most likely cells: [2, 4]" in output
    assert "Most likely cells: [5]" in output


@pytest.mark.parametrize("broken_function", ["normalise", "sensor_update", "motion_update_right"])
def test_solver_rejects_incorrect_student_functions(uncertainty_stub, monkeypatch, broken_function):
    complete_stub(uncertainty_stub)
    if broken_function == "normalise":
        uncertainty_stub.normalise = lambda values: values
    elif broken_function == "sensor_update":
        # Unnormalised sensor output must not be silently repaired by the server.
        uncertainty_stub.sensor_update = lambda belief, *args: [2 * value for value in belief]
    else:
        uncertainty_stub.motion_update_right = lambda belief, motion: belief
    with solver_client(uncertainty_stub, monkeypatch) as client:
        response = client.post("/solve", json={"problem": BayesFilterDemo().problem.model_dump()})
    assert response.status_code == 400
    assert broken_function in response.json()["message"]
