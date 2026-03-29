from ai9414.core.server import create_fastapi_app
from ai9414.labyrinth import LabyrinthDemo
from ai9414.labyrinth.generator import generate_labyrinth
from ai9414.labyrinth.solver import solve_labyrinth
from ai9414.search import run_labyrinth_solver
from ai9414.labyrinth.student import (
    LABYRINTH_ACTIONS,
    LABYRINTH_ACTION_DELTAS,
    LABYRINTH_TRACE_ACTIONS,
    apply_labyrinth_action,
    build_unimplemented_result,
    get_available_actions,
    get_open_neighbours,
    validate_labyrinth_payload,
    validate_labyrinth_solver_result,
)


def test_labyrinth_demo_exposes_built_in_examples():
    app = LabyrinthDemo()
    assert app.list_examples() == ["small", "medium", "large"]


def test_labyrinth_trace_reaches_found_state():
    app = LabyrinthDemo()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "labyrinth"
    assert trace["steps"][0]["event_type"] == "start"
    assert trace["steps"][-1]["event_type"] == "found"
    assert trace["summary"]["result"] == "found"


def test_default_labyrinth_example_contains_backtracking():
    app = LabyrinthDemo()
    trace = app.get_trace_payload()
    assert any(step["event_type"] == "backtrack" for step in trace["steps"])


def test_medium_and_large_configurations_include_backtracking():
    app = LabyrinthDemo()
    app.load_example("medium")
    medium_trace = app.get_trace_payload()
    assert any(step["event_type"] == "backtrack" for step in medium_trace["steps"])

    app.load_example("large")
    large_trace = app.get_trace_payload()
    assert any(step["event_type"] == "backtrack" for step in large_trace["steps"])


def test_generate_labyrinth_command_returns_playback_trace():
    app = LabyrinthDemo()
    payload = app.handle_action(
        {
            "action": "app_command",
            "payload": {"command": "generate_labyrinth", "size": "medium", "seed": 41},
        }
    )
    assert payload["ok"] is True
    assert payload["state"]["data"]["labyrinth"]["size"] == "medium"
    assert payload["state"]["data"]["labyrinth"]["seed"] == 41
    assert payload["trace"]["summary"]["step_count"] > 0
    assert payload["trace"]["summary"]["result"] == "found"


def test_generated_labyrinths_are_solvable():
    labyrinth = generate_labyrinth(size="small", seed=17)
    result = solve_labyrinth(labyrinth)
    assert result.status == "found"
    assert result.path[0] == labyrinth.start
    assert result.path[-1] == labyrinth.exit


def test_student_helpers_expose_problem_formalisation():
    labyrinth = generate_labyrinth(size="small", seed=17)
    payload = validate_labyrinth_payload(labyrinth.model_dump())
    start = tuple(payload["start"])
    actions = get_available_actions(payload, start)
    neighbours = get_open_neighbours(payload, start)
    placeholder = build_unimplemented_result()
    assert LABYRINTH_ACTIONS == ("move_up", "move_right", "move_down", "move_left")
    assert LABYRINTH_ACTION_DELTAS["move_right"] == (0, 1)
    assert LABYRINTH_TRACE_ACTIONS == ("start", "expand", "backtrack", "found", "fail")
    assert actions
    assert apply_labyrinth_action(start, actions[0]) == neighbours[0]
    assert isinstance(neighbours, list)
    assert placeholder["status"] == "error"
    assert run_labyrinth_solver


def test_student_result_validation_accepts_canonical_shape():
    result = validate_labyrinth_solver_result(
        {
            "algorithm": "dfs",
            "status": "found",
            "trace": [
                {
                    "step": 0,
                    "action": "start",
                    "cell": [1, 1],
                    "parent": None,
                    "depth": 0,
                    "stack": [[1, 1]],
                }
            ],
            "path": [[1, 1]],
            "visited_order": [[1, 1]],
        }
    )
    assert result["status"] == "found"


def test_labyrinth_fastapi_routes_work():
    app = LabyrinthDemo()
    from fastapi.testclient import TestClient

    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "labyrinth"
