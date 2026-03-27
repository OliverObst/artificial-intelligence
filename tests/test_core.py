from pathlib import Path

from ai9414.core.server import AppLauncher, find_free_port


def test_find_free_port_returns_positive_integer():
    port = find_free_port()
    assert isinstance(port, int)
    assert port > 0


def test_root_serves_student_shell(precomputed_client):
    response = precomputed_client.get("/")
    assert response.status_code == 200
    assert "Main Visual Area" in response.text


def test_manifest_route(precomputed_client):
    payload = precomputed_client.get("/api/manifest").json()
    assert payload["app_type"] == "placeholder"
    assert payload["execution_mode"] == "precomputed"
    assert payload["capabilities"]["solution_mode"] is True


def test_state_route(precomputed_client):
    payload = precomputed_client.get("/api/state").json()
    assert payload["data"]["counter"] == 0
    assert payload["data"]["target"] == 3


def test_trace_route_precomputed(precomputed_client):
    payload = precomputed_client.get("/api/trace").json()
    assert payload["is_complete"] is True
    assert payload["summary"]["step_count"] == 3


def test_trace_route_incremental(incremental_client):
    payload = incremental_client.get("/api/trace").json()
    assert payload["is_complete"] is False
    assert payload["steps"] == []


def test_action_route_validation(precomputed_client):
    response = precomputed_client.post("/api/action", json={"action": "set_option", "payload": {"unknown": True}})
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "invalid_option_value"


def test_incremental_next_step_flow(incremental_client):
    response = incremental_client.post("/api/action", json={"action": "next_step"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["new_step"]["index"] == 0
    assert payload["state"]["data"]["counter"] == 1
    assert payload["trace_complete"] is False


def test_browser_launch_fallback_path(monkeypatch, capsys, precomputed_demo):
    launcher = AppLauncher(precomputed_demo, open_browser=True, port=45678)

    monkeypatch.setattr("webbrowser.open", lambda url: False)
    launcher._open_browser_if_possible()

    captured = capsys.readouterr()
    assert "Open this URL manually" in captured.out


def test_solution_replay_export(tmp_path: Path, incremental_demo):
    bundle_dir = incremental_demo.export_solution_bundle(tmp_path / "solution")
    assert (bundle_dir / "index.html").exists()
    assert (bundle_dir / "trace.json").exists()
    trace_payload = (bundle_dir / "trace.json").read_text(encoding="utf-8")
    assert '"is_complete": true' in trace_payload


def test_configuration_file_validation_path(precomputed_demo, tmp_path: Path):
    bad_path = tmp_path / "bad.json"
    bad_path.write_text('{"schema_version": "1.0", "app_type": "placeholder"}', encoding="utf-8")

    payload = precomputed_demo.handle_action({"action": "load_config", "payload": {"path": str(bad_path)}})
    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_configuration_file"


def test_configuration_file_loads(valid_config_path, precomputed_demo):
    payload = precomputed_demo.handle_action(
        {"action": "load_config", "payload": {"path": str(valid_config_path)}}
    )
    assert payload["ok"] is True
    assert payload["state"]["data"]["target"] == 4
    assert payload["state"]["data"]["step_size"] == 2

