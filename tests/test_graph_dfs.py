from ai9414.core.server import create_fastapi_app
from ai9414.graph_dfs import GraphDfsDemo
from ai9414.graph_dfs.generator import generate_spatial_graph
from ai9414.graph_dfs.solver import solve_graph_dfs
from ai9414.graph_dfs.student import (
    GRAPH_TRACE_ACTIONS,
    build_unimplemented_graph_result,
    get_neighbours,
    validate_graph_payload,
    validate_graph_solver_result,
)
from ai9414.search import run_graph_solver


def test_graph_dfs_demo_exposes_configurations():
    app = GraphDfsDemo()
    assert app.list_examples() == ["small", "large"]


def test_graph_dfs_trace_reaches_found_state():
    app = GraphDfsDemo()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "graph_dfs"
    assert trace["steps"][0]["event_type"] == "start"
    assert trace["steps"][-1]["event_type"] == "found"
    assert trace["summary"]["result"] == "found"


def test_large_graph_configuration_contains_backtracking():
    app = GraphDfsDemo()
    app.load_example("large")
    trace = app.get_trace_payload()
    assert any(step["event_type"] == "backtrack" for step in trace["steps"])


def test_generate_graph_command_returns_playback_trace():
    app = GraphDfsDemo()
    payload = app.handle_action(
        {
            "action": "app_command",
            "payload": {"command": "generate_graph", "size": "large", "seed": 41},
        }
    )
    assert payload["ok"] is True
    assert payload["state"]["data"]["graph"]["size"] == "large"
    assert payload["state"]["data"]["graph"]["seed"] == 41
    assert payload["trace"]["summary"]["step_count"] > 0
    assert payload["trace"]["summary"]["result"] == "found"


def test_generated_graphs_are_solvable():
    graph = generate_spatial_graph(size="small", seed=17)
    result = solve_graph_dfs(graph)
    assert result.status == "found"
    assert result.path[0] == graph.start
    assert result.path[-1] == graph.goal


def test_student_helpers_expose_problem_formalisation():
    graph = generate_spatial_graph(size="small", seed=17)
    payload = validate_graph_payload(graph.model_dump())
    neighbours = get_neighbours(payload, payload["start"])
    placeholder = build_unimplemented_graph_result()
    assert GRAPH_TRACE_ACTIONS == ("start", "expand", "backtrack", "found", "fail")
    assert isinstance(neighbours, list)
    assert placeholder["status"] == "error"
    assert run_graph_solver


def test_graph_result_validation_accepts_canonical_shape():
    result = validate_graph_solver_result(
        {
            "algorithm": "dfs",
            "status": "found",
            "trace": [
                {
                    "step": 0,
                    "action": "start",
                    "node": "A",
                    "parent": None,
                    "depth": 0,
                    "stack": ["A"],
                }
            ],
            "path": ["A"],
            "visited_order": ["A"],
        }
    )
    assert result["status"] == "found"


def test_graph_dfs_fastapi_routes_work():
    app = GraphDfsDemo()
    from fastapi.testclient import TestClient

    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "graph_dfs"
