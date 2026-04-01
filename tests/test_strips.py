from fastapi.testclient import TestClient

from ai9414.core.server import create_fastapi_app
from ai9414.strips import StripsDemo, StripsProblem, run_strips_solver
from ai9414.strips.student import (
    STRIPS_TRACE_ACTIONS,
    apply_action_signature,
    build_unimplemented_strips_result,
    get_applicable_actions,
    get_initial_facts,
    validate_strips_payload,
    validate_strips_solver_result,
)


def test_strips_demo_lists_curated_examples():
    app = StripsDemo()
    assert app.list_examples() == [
        "canonical_delivery",
        "robot_starts_mail_room",
        "keycard_in_office_b",
        "unlocked_lab",
        "lab_via_office_b",
    ]


def test_strips_trace_reaches_goal_state():
    app = StripsDemo()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "strips"
    assert trace["steps"][0]["event_type"] == "plan_found"
    assert trace["summary"]["result"] == "found"
    assert trace["steps"][-1]["state_patch"]["planning"]["goal_satisfied"] is True


def test_unlocked_example_drops_unlock_action():
    app = StripsDemo(problem="unlocked_lab")
    trace = app.get_trace_payload()
    plan = trace["steps"][0]["state_patch"]["planning"]["plan"]
    assert all(action["name"] != "unlock_door" for action in plan)


def test_load_problem_accepts_custom_problem():
    app = StripsDemo(
        problem=StripsProblem(
            title="Custom",
            rooms=["corridor", "mail_room", "office_a", "office_b", "lab"],
            robot_start="corridor",
            parcel_start="mail_room",
            keycard_start="office_a",
            locked_edge=("corridor", "lab"),
            door_locked=True,
            goal=[("at", "parcel", "lab")],
        )
    )
    payload = app.build_state_payload()
    assert payload["example_name"] is None
    assert payload["data"]["strips_problem"]["title"] == "Custom"


def test_strips_student_helpers_expose_symbolic_state_tools():
    app = StripsDemo()
    problem = validate_strips_payload(app.build_state_payload()["data"]["strips_problem"])
    facts = get_initial_facts(problem)
    actions = get_applicable_actions(problem, facts)
    next_facts = apply_action_signature(problem, facts, actions[0])
    placeholder = build_unimplemented_strips_result()
    assert STRIPS_TRACE_ACTIONS == ("expand", "goal")
    assert any(fact[0] == "at" and fact[1] == "robot" for fact in facts)
    assert isinstance(actions, list)
    assert next_facts != facts
    assert placeholder["status"] == "error"
    assert run_strips_solver


def test_strips_result_validation_accepts_canonical_shape():
    result = validate_strips_solver_result(
        {
            "algorithm": "strips_bfs",
            "status": "found",
            "plan": [
                "move(robot, corridor, office_a)",
                "pickup_keycard(robot, keycard, office_a)",
            ],
            "stats": {
                "expanded_states": 3,
                "generated_states": 4,
                "frontier_peak": 2,
            },
            "search_trace": [
                {
                    "step": 0,
                    "action": "expand",
                    "facts": [["at", "robot", "corridor"]],
                    "plan_prefix": [],
                    "frontier_size": 1,
                }
            ],
        }
    )
    assert result["status"] == "found"


def test_strips_fastapi_routes_work():
    app = StripsDemo()
    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "strips"
