from ai9414.core.server import create_fastapi_app
from ai9414.delivery import DeliveryDemo


def test_delivery_demo_exposes_office_examples():
    app = DeliveryDemo()
    assert app.list_examples() == ["four_rooms", "corridor"]


def test_delivery_trace_reaches_found_state():
    app = DeliveryDemo()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "delivery"
    assert trace["steps"][0]["event_type"] == "start"
    assert trace["steps"][-1]["event_type"] == "found"
    assert trace["summary"]["result"] == "found"
    assert trace["initial_state"]["labyrinth"]["start"] == [1, 1]
    assert trace["initial_state"]["labyrinth"]["exit"] == [12, 12]


def test_delivery_corridor_configuration_is_solvable():
    app = DeliveryDemo()
    app.load_example("corridor")
    trace = app.get_trace_payload()
    assert trace["summary"]["result"] == "found"
    assert trace["initial_state"]["labyrinth"]["size"] == "corridor"


def test_delivery_action_order_changes_trace():
    app = DeliveryDemo()
    default_trace = app.get_trace_payload()
    app.set_options(action_order="straight_right_left")
    right_first_trace = app.get_trace_payload()
    app.set_options(action_order="random")
    random_trace = app.get_trace_payload()

    assert default_trace["summary"]["result"] == "found"
    assert right_first_trace["summary"]["result"] == "found"
    assert random_trace["summary"]["result"] == "found"
    assert default_trace["summary"]["step_count"] != right_first_trace["summary"]["step_count"]
    assert random_trace["initial_state"]["action_order_label"] == "random choice"


def test_delivery_fastapi_routes_work():
    app = DeliveryDemo()
    from fastapi.testclient import TestClient

    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "delivery"
