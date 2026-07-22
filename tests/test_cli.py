from __future__ import annotations

from pathlib import Path

import pytest

from ai9414 import cli
from ai9414.core import AI9414Error


def test_cli_without_arguments_prints_overview(capsys):
    assert cli.main([]) == 0

    captured = capsys.readouterr()
    assert "ai9414 demo graph-bnb" in captured.out
    assert "python -m ai9414 demo graph-dfs" in captured.out


def test_cli_lists_available_demos(capsys):
    assert cli.main(["list"]) == 0

    captured = capsys.readouterr()
    assert "delivery" in captured.out
    assert "graph-dfs" in captured.out
    assert "logic-dpll" in captured.out
    assert "logic-resolution" in captured.out
    assert "csp-delivery" in captured.out
    assert "foundation-models-tokenisation" in captured.out
    assert "foundation-models-decoding" in captured.out
    foundation_demo_lines = [
        line
        for line in captured.out.splitlines()
        if line.startswith("- foundation-models")
    ]
    assert len(foundation_demo_lines) == 2
    assert not any(
        line.startswith("- foundation-models:") for line in foundation_demo_lines
    )


def test_cli_lists_examples_for_one_demo(capsys):
    assert cli.main(["list", "--examples", "graph-dfs"]) == 0

    captured = capsys.readouterr()
    assert "graph-dfs examples:" in captured.out
    assert "- small" in captured.out
    assert "- large" in captured.out


def test_cli_lists_logic_examples_across_modes(capsys):
    assert cli.main(["list", "--examples", "logic-dpll"]) == 0

    captured = capsys.readouterr()
    assert "- simple_sat" in captured.out
    assert "- entailment_chain" in captured.out
    assert "- wumpus_no_breeze" in captured.out
    assert "- wumpus_forced_pit" in captured.out


def test_cli_lists_resolution_examples(capsys):
    assert cli.main(["list", "--examples", "logic-resolution"]) == 0

    captured = capsys.readouterr()
    assert "- chain_refutation" in captured.out
    assert "- wumpus_no_breeze" in captured.out
    assert "- wumpus_forced_pit" in captured.out


def test_cli_exposes_explicit_foundation_model_explorers(capsys):
    assert cli.main(["list", "--examples", "foundation-models-decoding"]) == 0

    captured = capsys.readouterr()
    assert "foundation-models-decoding examples:" in captured.out
    assert "- lecture_activity" in captured.out
    assert "- peaked_distribution" in captured.out

    tokenisation = cli.resolve_demo_spec("foundation-models-tokenisation").factory()
    decoding = cli.resolve_demo_spec("foundation-models-decoding").factory()
    assert tokenisation.app_title.endswith("Tokenisation Explorer")
    assert decoding.app_title.endswith("Decoding Explorer")

    for removed_name in ("foundation-models", "foundation_models"):
        with pytest.raises(AI9414Error) as exc_info:
            cli.resolve_demo_spec(removed_name)
        assert exc_info.value.code == "demo_not_found"
        assert "Unknown demo" in exc_info.value.message


def test_cli_launches_requested_demo(monkeypatch):
    launched: dict[str, object] = {}

    class DummyLauncher:
        def __init__(self, app_instance, *, host, port, open_browser):
            launched["app"] = app_instance
            launched["host"] = host
            launched["port"] = port
            launched["open_browser"] = open_browser

        def start(self):
            launched["started"] = True

    monkeypatch.setattr(cli, "AppLauncher", DummyLauncher)

    assert (
        cli.main(
            [
                "demo",
                "graph-dfs",
                "--example",
                "large",
                "--host",
                "0.0.0.0",
                "--port",
                "9414",
                "--no-browser",
            ]
        )
        == 0
    )

    app = launched["app"]
    assert app.app_type == "graph_dfs"
    assert app.example_name == "large"
    assert launched["host"] == "0.0.0.0"
    assert launched["port"] == 9414
    assert launched["open_browser"] is False
    assert launched["started"] is True


def test_cli_loads_configuration_before_launch(monkeypatch, tmp_path: Path):
    launched: dict[str, object] = {}

    class DummyLauncher:
        def __init__(self, app_instance, *, host, port, open_browser):
            launched["app"] = app_instance
            launched["host"] = host
            launched["port"] = port
            launched["open_browser"] = open_browser

        def start(self):
            launched["started"] = True

    monkeypatch.setattr(cli, "AppLauncher", DummyLauncher)

    config_path = tmp_path / "search.json"
    config_path.write_text(
        """
{
  "schema_version": "1.0",
  "app_type": "search",
  "title": "Configured weighted graph",
  "options": {
    "playback_speed": 1.5
  },
  "data": {
    "subtitle": "Configured example for CLI tests.",
    "graph": {
      "nodes": [
        {"id": "A", "x": 0.1, "y": 0.5},
        {"id": "B", "x": 0.45, "y": 0.3},
        {"id": "C", "x": 0.45, "y": 0.7},
        {"id": "D", "x": 0.85, "y": 0.5}
      ],
      "edges": [
        {"u": "A", "v": "B", "cost": 1.0},
        {"u": "A", "v": "C", "cost": 1.1},
        {"u": "B", "v": "D", "cost": 1.0},
        {"u": "C", "v": "D", "cost": 0.8}
      ],
      "start": "A",
      "goal": "D"
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    assert (
        cli.main(["demo", "graph-bnb", "--config", str(config_path), "--no-browser"])
        == 0
    )

    app = launched["app"]
    assert app.app_type == "search"
    assert app.config_name == "search.json"
    assert app.example_name is None
    assert launched["started"] is True


def test_cli_reports_unknown_demo(capsys):
    assert cli.main(["demo", "graph-df", "--no-browser"]) == 1

    captured = capsys.readouterr()
    assert "Unknown demo 'graph-df'" in captured.err
    assert "graph-dfs" in captured.err
