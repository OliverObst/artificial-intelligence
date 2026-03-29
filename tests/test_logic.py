from fastapi.testclient import TestClient

from ai9414.core.server import create_fastapi_app
from ai9414.logic import DpllDemo, run_dpll_solver
from ai9414.logic.parser import formula_to_cnf_clauses, negate_formula_to_cnf_clauses
from ai9414.logic.student import (
    DPLL_TRACE_ACTIONS,
    build_unimplemented_dpll_result,
    validate_dpll_solver_result,
    validate_logic_payload,
)


def test_dpll_demo_lists_sat_examples_by_default():
    app = DpllDemo()
    assert app.list_examples() == [
        "simple_sat",
        "tiny_contradiction",
        "unit_chain",
        "unsat_branching",
        "constraint_model",
    ]


def test_dpll_demo_lists_entailment_examples_in_entailment_mode():
    app = DpllDemo(mode="entailment")
    assert app.list_examples() == ["entailment_chain"]


def test_dpll_trace_reaches_finished_state():
    app = DpllDemo()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "logic"
    assert trace["steps"][0]["event_type"] == "start"
    assert trace["steps"][-1]["event_type"] == "finished"
    assert trace["summary"]["result"] == "satisfiable"


def test_entailment_example_reports_entailed():
    app = DpllDemo(mode="entailment")
    trace = app.get_trace_payload()
    assert trace["summary"]["result"] == "entailed"
    assert trace["initial_state"]["logic"]["query"] == "C"


def test_load_cnf_accepts_custom_clauses():
    app = DpllDemo()
    app.load_cnf([["A"], ["~A", "B"]], title="Custom")
    payload = app.build_state_payload()
    assert payload["example_name"] is None
    assert payload["data"]["logic"]["variables"] == ["A", "B"]
    assert payload["data"]["logic_problem"]["clauses"] == [["A"], ["~A", "B"]]


def test_small_formula_parser_builds_expected_cnf():
    assert formula_to_cnf_clauses("A -> B") == [["~A", "B"]]
    assert negate_formula_to_cnf_clauses("C") == [["~C"]]


def test_dpll_student_helpers_expose_problem_formalisation():
    app = DpllDemo()
    payload = validate_logic_payload(app.build_state_payload()["data"]["logic_problem"])
    placeholder = build_unimplemented_dpll_result()
    assert payload["mode"] == "sat"
    assert DPLL_TRACE_ACTIONS == (
        "start",
        "choose_variable",
        "assign",
        "contradiction",
        "backtrack",
        "solution_found",
        "finished",
    )
    assert placeholder["status"] == "error"
    assert run_dpll_solver


def test_dpll_result_validation_accepts_canonical_shape():
    result = validate_dpll_solver_result(
        {
            "algorithm": "dpll",
            "mode": "sat",
            "status": "satisfiable",
            "trace": [
                {
                    "step": 0,
                    "action": "start",
                    "node_id": "t0",
                    "parent_id": None,
                    "assignment": {},
                    "variable": None,
                    "value": None,
                    "reason": None,
                    "clause_index": None,
                }
            ],
            "assignment": {"A": True},
        }
    )
    assert result["status"] == "satisfiable"


def test_dpll_fastapi_routes_work():
    app = DpllDemo()
    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "logic"
