from ai9414.core.server import create_fastapi_app
from ai9414.graph_gbfs import GraphGbfsDemo
from ai9414.graph_gbfs.generator import generate_weighted_graph
from ai9414.graph_gbfs.solver import solve_graph_gbfs
from ai9414.graph_gbfs.student import (
    GRAPH_GBFS_TRACE_ACTIONS,
    build_unimplemented_graph_gbfs_result,
    get_neighbours,
    heuristic_to_goal,
    validate_graph_gbfs_solver_result,
    validate_graph_payload,
)
from ai9414.search import run_graph_gbfs_solver


def test_graph_gbfs_demo_exposes_configurations():
    app = GraphGbfsDemo()
    assert app.list_examples() == ["small", "large"]


def test_graph_gbfs_trace_reaches_found_state():
    app = GraphGbfsDemo()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "graph_gbfs"
    assert trace["steps"][0]["event_type"] == "start"
    assert trace["steps"][-1]["event_type"] == "found"
    assert trace["summary"]["result"] == "found"


def test_generate_graph_command_returns_playback_trace():
    app = GraphGbfsDemo()
    payload = app.handle_action(
        {"action": "app_command", "payload": {"command": "generate_graph", "size": "large", "seed": 41}}
    )
    assert payload["ok"] is True
    assert payload["state"]["data"]["graph"]["size"] == "large"
    assert payload["state"]["data"]["graph"]["seed"] == 41
    assert payload["trace"]["summary"]["step_count"] > 0
    assert payload["trace"]["summary"]["result"] == "found"


def test_generated_graphs_are_solvable_with_gbfs():
    graph = generate_weighted_graph(size="small", seed=17)
    result = solve_graph_gbfs(graph)
    assert result.status == "found"
    assert result.path[0] == graph.start
    assert result.path[-1] == graph.goal
    assert result.path_cost is not None


def test_graph_gbfs_student_helpers_expose_problem_formalisation():
    graph = generate_weighted_graph(size="small", seed=17)
    payload = validate_graph_payload(graph.model_dump())
    neighbours = get_neighbours(payload, payload["start"])
    placeholder = build_unimplemented_graph_gbfs_result()
    heuristic = heuristic_to_goal(payload, payload["start"])
    assert GRAPH_GBFS_TRACE_ACTIONS == ("start", "expand", "consider_edge", "enqueue", "found", "fail")
    assert isinstance(neighbours, list)
    assert isinstance(heuristic, float)
    assert placeholder["status"] == "error"
    assert run_graph_gbfs_solver


def test_graph_gbfs_result_validation_accepts_canonical_shape():
    result = validate_graph_gbfs_solver_result(
        {
            "algorithm": "gbfs",
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
                    "considered_edge": None,
                }
            ],
            "path": ["A"],
            "path_cost": 0.0,
            "visited_order": ["A"],
        }
    )
    assert result["status"] == "found"


def test_graph_gbfs_fastapi_routes_work():
    app = GraphGbfsDemo()
    from fastapi.testclient import TestClient

    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "graph_gbfs"
