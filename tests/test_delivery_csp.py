from fastapi.testclient import TestClient

from ai9414.core.server import create_fastapi_app
from ai9414.delivery_csp import DeliveryCSPDemo, DeliveryCspProblem, run_delivery_csp_solver
from ai9414.delivery_csp.student import (
    DELIVERY_CSP_TRACE_ACTIONS,
    build_unimplemented_delivery_csp_result,
    validate_delivery_csp_payload,
    validate_delivery_csp_solver_result,
)


def test_delivery_csp_demo_lists_curated_examples():
    app = DeliveryCSPDemo()
    assert app.list_examples() == [
        "weekday_schedule",
        "precedence_chain",
        "room_pressure_unsat",
    ]


def test_delivery_csp_trace_finds_solution_for_default_example():
    app = DeliveryCSPDemo()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "delivery_csp"
    assert trace["summary"]["result"] == "found"
    assert trace["steps"][0]["event_type"] == "start"
    assert trace["steps"][-1]["event_type"] == "solution_found"


def test_room_pressure_example_is_unsatisfiable():
    app = DeliveryCSPDemo(example="room_pressure_unsat")
    trace = app.get_trace_payload()
    assert trace["summary"]["result"] == "not_found"
    assert trace["steps"][-1]["event_type"] == "failure"


def test_load_delivery_problem_accepts_custom_problem():
    app = DeliveryCSPDemo(
        problem=DeliveryCspProblem(
            title="Custom delivery schedule",
            deliveries=[
                {"id": "a", "label": "Delivery A", "short_label": "A", "colour": "#c75b4a"},
                {"id": "b", "label": "Delivery B", "short_label": "B", "colour": "#4d79ab"},
            ],
            slots=[
                {"id": "s1", "label": "09:00", "order": 0},
                {"id": "s2", "label": "11:00", "order": 1},
            ],
            rooms=[
                {"id": "dock", "label": "Dock"},
            ],
            values=[
                {"id": "s1_dock", "slot": "s1", "room": "dock", "label": "09:00 @ Dock"},
                {"id": "s2_dock", "slot": "s2", "room": "dock", "label": "11:00 @ Dock"},
            ],
            domains={
                "a": ["s1_dock", "s2_dock"],
                "b": ["s2_dock"],
            },
            constraints=[
                {
                    "kind": "precedence",
                    "left": "a",
                    "right": "b",
                    "label": "A before B",
                    "description": "Delivery A must happen before delivery B.",
                }
            ],
        )
    )
    payload = app.build_state_payload()
    assert payload["example_name"] is None
    assert payload["data"]["delivery_problem"]["title"] == "Custom delivery schedule"
    assert payload["data"]["delivery_problem"]["variables"] == ["a", "b"]


def test_delivery_csp_student_helpers_expose_payload_and_placeholder():
    app = DeliveryCSPDemo()
    payload = validate_delivery_csp_payload(app.build_state_payload()["data"]["delivery_problem"])
    placeholder = build_unimplemented_delivery_csp_result()
    assert payload["variables"] == ["meds", "path", "food", "linen", "waste"]
    assert DELIVERY_CSP_TRACE_ACTIONS == (
        "start",
        "select_variable",
        "try_value",
        "assign",
        "prune",
        "domain_wipeout",
        "backtrack",
        "unassign",
        "solution_found",
        "failure",
    )
    assert placeholder["status"] == "error"
    assert run_delivery_csp_solver


def test_delivery_csp_result_validation_accepts_canonical_shape():
    result = validate_delivery_csp_solver_result(
        {
            "algorithm": "backtracking_forward_checking",
            "status": "found",
            "events": [
                {"step": 0, "action": "start"},
                {"step": 1, "action": "select_variable", "variable": "path", "domain": ["slot_1_clinic"]},
                {"step": 2, "action": "try_value", "variable": "path", "value": "slot_1_clinic", "domain": ["slot_1_clinic"]},
                {"step": 3, "action": "assign", "variable": "path", "value": "slot_1_clinic", "assignments": {"path": "slot_1_clinic"}},
                {
                    "step": 4,
                    "action": "prune",
                    "variable": "path",
                    "value": "slot_1_clinic",
                    "changes": [
                        {"variable": "meds", "removed": ["slot_2_clinic"], "new_domain": ["slot_3_clinic"]},
                    ],
                },
                {"step": 5, "action": "solution_found", "assignments": {"path": "slot_1_clinic"}},
            ],
            "assignment": {"path": "slot_1_clinic"},
        }
    )
    assert result["status"] == "found"


def test_delivery_csp_fastapi_routes_work():
    app = DeliveryCSPDemo()
    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "delivery_csp"
