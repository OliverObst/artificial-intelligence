from ai9414.core.server import create_fastapi_app
from ai9414.graph_astar import GraphAStarDemo
from ai9414.graph_astar.generator import generate_weighted_graph
from ai9414.graph_astar.solver import solve_graph_astar
from ai9414.graph_astar.student import (
    GRAPH_ASTAR_TRACE_ACTIONS,
    build_unimplemented_graph_astar_result,
    get_neighbours,
    heuristic_to_goal,
    validate_graph_astar_solver_result,
    validate_graph_payload,
)
from ai9414.search import run_graph_astar_solver


def test_graph_astar_demo_exposes_configurations():
    app = GraphAStarDemo()
    assert app.list_examples() == ["small", "large"]


def test_graph_astar_trace_reaches_found_state():
    app = GraphAStarDemo()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "graph_astar"
    assert trace["steps"][0]["event_type"] == "start"
    assert trace["steps"][-1]["event_type"] == "found"
    assert trace["summary"]["result"] == "found"


def test_generate_graph_command_returns_playback_trace():
    app = GraphAStarDemo()
    payload = app.handle_action(
        {"action": "app_command", "payload": {"command": "generate_graph", "size": "large", "seed": 41}}
    )
    assert payload["ok"] is True
    assert payload["state"]["data"]["graph"]["size"] == "large"
    assert payload["state"]["data"]["graph"]["seed"] == 41
    assert payload["trace"]["summary"]["step_count"] > 0
    assert payload["trace"]["summary"]["result"] == "found"


def test_generated_graphs_are_solvable_with_astar():
    graph = generate_weighted_graph(size="small", seed=17)
    result = solve_graph_astar(graph)
    assert result.status == "found"
    assert result.path[0] == graph.start
    assert result.path[-1] == graph.goal
    assert result.best_cost is not None


def test_graph_astar_student_helpers_expose_problem_formalisation():
    graph = generate_weighted_graph(size="small", seed=17)
    payload = validate_graph_payload(graph.model_dump())
    neighbours = get_neighbours(payload, payload["start"])
    placeholder = build_unimplemented_graph_astar_result()
    heuristic = heuristic_to_goal(payload, payload["start"])
    assert GRAPH_ASTAR_TRACE_ACTIONS == ("start", "expand", "consider_edge", "relax", "found", "fail")
    assert isinstance(neighbours, list)
    assert isinstance(heuristic, float)
    assert placeholder["status"] == "error"
    assert run_graph_astar_solver


def test_graph_astar_result_validation_accepts_canonical_shape():
    result = validate_graph_astar_solver_result(
        {
            "algorithm": "astar",
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
                    "heuristic": 1.2,
                    "priority": 1.2,
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


def test_graph_astar_fastapi_routes_work():
    app = GraphAStarDemo()
    from fastapi.testclient import TestClient

    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "graph_astar"
