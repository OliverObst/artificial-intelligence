import math
from pathlib import Path

from ai9414.core.server import AppLauncher, find_free_port
from ai9414.search.examples import build_examples
from ai9414.search.trace import build_search_trace


def test_find_free_port_returns_positive_integer():
    port = find_free_port()
    assert isinstance(port, int)
    assert port > 0


def test_root_serves_student_shell(precomputed_client):
    response = precomputed_client.get("/")
    assert response.status_code == 200
    assert "Search Tree" in response.text


def test_manifest_route(precomputed_client):
    payload = precomputed_client.get("/api/manifest").json()
    assert payload["app_type"] == "search"
    assert payload["execution_mode"] == "precomputed"
    assert payload["capabilities"]["solution_mode"] is True


def test_state_route(precomputed_client):
    payload = precomputed_client.get("/api/state").json()
    assert payload["data"]["algorithm_label"] == "Depth-first branch-and-bound"
    assert payload["data"]["graph"]["start"]
    assert payload["data"]["graph"]["goal"]
    assert payload["data"]["search"]["current_graph_path"] == [
        payload["data"]["graph"]["start"]
    ]


def test_trace_route_precomputed(precomputed_client):
    payload = precomputed_client.get("/api/trace").json()
    assert payload["is_complete"] is True
    assert payload["initial_state"]["algorithm_label"] == "Depth-first branch-and-bound"
    assert payload["steps"][0]["event_type"] == "initialise"
    assert payload["steps"][-1]["event_type"] == "finished"
    assert payload["summary"]["step_count"] == len(payload["steps"])


def test_action_route_validation(precomputed_client):
    response = precomputed_client.post(
        "/api/action",
        json={"action": "set_option", "payload": {"unknown": True}},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "invalid_option_value"


def test_precomputed_next_step_flow(precomputed_client):
    response = precomputed_client.post("/api/action", json={"action": "next_step"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"]["view"]["current_step"] == 1
    assert payload["state"]["data"]["tree"]["nodes"]
    assert payload["state"]["data"]["search"]["current_graph_path"]


def test_browser_launch_fallback_path(monkeypatch, capsys, precomputed_demo):
    launcher = AppLauncher(precomputed_demo, open_browser=True, port=45678)

    monkeypatch.setattr("webbrowser.open", lambda url: False)
    launcher._open_browser_if_possible()

    captured = capsys.readouterr()
    assert "Open this URL manually" in captured.out


def test_solution_replay_export(tmp_path: Path, precomputed_demo):
    bundle_dir = precomputed_demo.export_solution_bundle(tmp_path / "solution")
    assert (bundle_dir / "index.html").exists()
    assert (bundle_dir / "trace.json").exists()
    assert (bundle_dir / "student-assets" / "style.css").exists()
    trace_payload = (bundle_dir / "trace.json").read_text(encoding="utf-8")
    assert '"initial_state"' in trace_payload
    assert '"is_complete": true' in trace_payload


def test_configuration_file_validation_path(precomputed_demo, tmp_path: Path):
    bad_path = tmp_path / "bad.json"
    bad_path.write_text('{"schema_version": "1.0", "app_type": "search"}', encoding="utf-8")

    payload = precomputed_demo.handle_action({"action": "load_config", "payload": {"path": str(bad_path)}})
    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_configuration_file"


def test_configuration_file_loads(valid_config_path, precomputed_demo):
    payload = precomputed_demo.handle_action(
        {"action": "load_config", "payload": {"path": str(valid_config_path)}}
    )
    assert payload["ok"] is True
    assert payload["state"]["config_name"] == valid_config_path.name
    assert payload["state"]["data"]["graph"]["start"] == "A"
    assert payload["state"]["data"]["graph"]["goal"] == "D"
    assert payload["state"]["options"]["playback_speed"] == 1.5


def test_examples_produce_optimal_paths():
    for example in build_examples().values():
        trace = build_search_trace(example)
        final_search = trace.steps[-1].state_patch["search"]
        optimal_cost = _brute_force_shortest_cost(example.graph)
        assert math.isclose(final_search["best_cost"], optimal_cost, rel_tol=1e-9)


def test_misleading_branch_updates_best_solution_more_than_once():
    example = build_examples()["misleading_branch"]
    trace = build_search_trace(example)
    best_updates = [step for step in trace.steps if step.event_type == "best_updated"]
    assert len(best_updates) >= 2


def test_strong_pruning_example_emits_prune_events():
    example = build_examples()["strong_pruning"]
    trace = build_search_trace(example)
    prune_steps = [step for step in trace.steps if step.event_type == "prune"]
    assert prune_steps


def _brute_force_shortest_cost(graph) -> float:
    adjacency: dict[str, list[tuple[str, float]]] = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.u].append((edge.v, edge.cost))
        adjacency[edge.v].append((edge.u, edge.cost))

    best_cost = math.inf

    def walk(node: str, visited: set[str], cost: float) -> None:
        nonlocal best_cost
        if cost >= best_cost:
            return
        if node == graph.goal:
            best_cost = min(best_cost, cost)
            return
        for neighbour, edge_cost in adjacency[node]:
            if neighbour in visited:
                continue
            walk(neighbour, visited | {neighbour}, cost + edge_cost)

    walk(graph.start, {graph.start}, 0.0)
    return best_cost
