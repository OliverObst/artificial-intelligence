from pathlib import Path

import pytest

from ai9414.demo import PlaceholderDemo
from ai9414.core.server import create_fastapi_app


@pytest.fixture
def precomputed_demo():
    return PlaceholderDemo(execution_mode="precomputed")


@pytest.fixture
def incremental_demo():
    return PlaceholderDemo(execution_mode="incremental")


@pytest.fixture
def precomputed_client(precomputed_demo):
    from fastapi.testclient import TestClient

    with TestClient(create_fastapi_app(precomputed_demo)) as client:
        yield client


@pytest.fixture
def incremental_client(incremental_demo):
    from fastapi.testclient import TestClient

    with TestClient(create_fastapi_app(incremental_demo)) as client:
        yield client


@pytest.fixture
def valid_config_path(tmp_path: Path):
    path = tmp_path / "placeholder.json"
    path.write_text(
        """
{
  "schema_version": "1.0",
  "app_type": "placeholder",
  "title": "Configured placeholder",
  "options": {
    "pace": "slow"
  },
  "data": {
    "target": 4,
    "step_size": 2
  }
}
""".strip(),
        encoding="utf-8",
    )
    return path

