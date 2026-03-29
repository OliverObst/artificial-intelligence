from ai9414.search import run_weighted_graph_solver
from ai9414.search.generator import generate_weighted_graph
from ai9414.search.student import (
    SEARCH_TRACE_ACTIONS,
    build_unimplemented_weighted_graph_result,
    get_neighbours,
    validate_weighted_graph_payload,
    validate_weighted_graph_solver_result,
)
from ai9414.search.trace import build_search_trace_from_definition


def test_generated_weighted_graphs_are_solvable():
    graph = generate_weighted_graph(size="small", seed=17)
    trace = build_search_trace_from_definition(
        graph,
        title="Generated weighted graph",
        subtitle="Automated test graph.",
    ).model_dump()
    final_search = trace["steps"][-1]["state_patch"]["search"]
    assert final_search["final_graph_path"][0] == graph.start
    assert final_search["final_graph_path"][-1] == graph.goal


def test_weighted_student_helpers_expose_problem_formalisation():
    graph = generate_weighted_graph(size="small", seed=17)
    payload = validate_weighted_graph_payload(graph.model_dump())
    neighbours = get_neighbours(payload, payload["start"])
    placeholder = build_unimplemented_weighted_graph_result()
    assert SEARCH_TRACE_ACTIONS == (
        "start",
        "expand",
        "consider_edge",
        "descend",
        "prune",
        "backtrack",
        "solution_found",
        "best_updated",
        "finished",
    )
    assert isinstance(neighbours, list)
    assert placeholder["status"] == "error"
    assert run_weighted_graph_solver


def test_weighted_result_validation_accepts_canonical_shape():
    result = validate_weighted_graph_solver_result(
        {
            "algorithm": "dfbb",
            "status": "found",
            "trace": [
                {
                    "step": 0,
                    "action": "start",
                    "node": "A",
                    "parent": None,
                    "depth": 0,
                    "path_cost": 0.0,
                    "current_path": ["A"],
                    "current_cost": 0.0,
                    "best_path": [],
                    "best_cost": None,
                    "considered_edge": None,
                }
            ],
            "path": ["A"],
            "best_cost": 0.0,
            "visited_order": ["A"],
        }
    )
    assert result["status"] == "found"
