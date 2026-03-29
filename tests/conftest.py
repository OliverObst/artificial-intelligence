from pathlib import Path

import pytest

from ai9414.core.server import create_fastapi_app
from ai9414.search import SearchDemo


@pytest.fixture
def precomputed_demo():
    return SearchDemo()


@pytest.fixture
def precomputed_client(precomputed_demo):
    from fastapi.testclient import TestClient

    with TestClient(create_fastapi_app(precomputed_demo)) as client:
        yield client

@pytest.fixture
def valid_config_path(tmp_path: Path):
    path = tmp_path / "search.json"
    path.write_text(
        """
{
  "schema_version": "1.0",
  "app_type": "search",
  "title": "Configured weighted graph",
  "options": {
    "playback_speed": 1.5
  },
  "data": {
    "subtitle": "Instructor-defined example for automated tests.",
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
    return path
