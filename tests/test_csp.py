from fastapi.testclient import TestClient

from ai9414.core.server import create_fastapi_app
from ai9414.csp import CSPDemo, CspProblem, run_csp_solver
from ai9414.csp.student import (
    CSP_TRACE_ACTIONS,
    build_unimplemented_csp_result,
    validate_csp_payload,
    validate_csp_solver_result,
)


def test_csp_demo_lists_curated_examples():
    app = CSPDemo()
    assert app.list_examples() == [
        "australia",
        "australia_unsat_2_colours",
        "mini_map_easy",
        "mini_map_tight",
    ]


def test_csp_trace_finds_solution_for_default_australia():
    app = CSPDemo()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "csp"
    assert trace["summary"]["result"] == "found"
    assert trace["steps"][0]["event_type"] == "start"
    assert trace["steps"][-1]["event_type"] == "solution_found"


def test_two_colour_australia_is_unsatisfiable():
    app = CSPDemo(example="australia_unsat_2_colours")
    trace = app.get_trace_payload()
    assert trace["summary"]["result"] == "not_found"
    assert trace["steps"][-1]["event_type"] == "failure"


def test_load_map_problem_accepts_custom_problem():
    app = CSPDemo(
        problem=CspProblem(
            title="Custom",
            regions=["a", "b", "c", "d"],
            colours=["red", "green", "blue"],
            neighbours={
                "a": ["b", "c"],
                "b": ["a", "c", "d"],
                "c": ["a", "b", "d"],
                "d": ["b", "c"],
            },
        )
    )
    payload = app.build_state_payload()
    assert payload["example_name"] is None
    assert payload["data"]["csp_problem"]["title"] == "Custom"
    assert payload["data"]["csp_problem"]["variables"] == ["a", "b", "c", "d"]


def test_csp_student_helpers_expose_payload_and_placeholder():
    app = CSPDemo()
    payload = validate_csp_payload(app.build_state_payload()["data"]["csp_problem"])
    placeholder = build_unimplemented_csp_result()
    assert payload["variables"] == ["wa", "nt", "sa", "q", "nsw", "v", "t"]
    assert CSP_TRACE_ACTIONS == (
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
    assert run_csp_solver


def test_csp_result_validation_accepts_canonical_shape():
    result = validate_csp_solver_result(
        {
            "algorithm": "backtracking_forward_checking",
            "status": "found",
            "events": [
                {"step": 0, "action": "start"},
                {"step": 1, "action": "select_variable", "variable": "wa", "domain": ["red", "green", "blue"]},
                {"step": 2, "action": "try_value", "variable": "wa", "value": "red", "domain": ["red", "green", "blue"]},
                {"step": 3, "action": "assign", "variable": "wa", "value": "red", "assignments": {"wa": "red"}},
                {
                    "step": 4,
                    "action": "prune",
                    "variable": "wa",
                    "value": "red",
                    "changes": [
                        {"variable": "nt", "removed": ["red"], "new_domain": ["green", "blue"]},
                    ],
                },
                {"step": 5, "action": "solution_found", "assignments": {"wa": "red"}},
            ],
            "assignment": {"wa": "red"},
        }
    )
    assert result["status"] == "found"


def test_csp_fastapi_routes_work():
    app = CSPDemo()
    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "csp"
