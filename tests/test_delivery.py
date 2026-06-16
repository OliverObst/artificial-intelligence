from ai9414.core.server import create_fastapi_app
from ai9414.delivery import DeliveryDemo


def test_delivery_demo_exposes_office_examples():
    app = DeliveryDemo()
    assert app.list_examples() == [
        "four_rooms",
        "single_room",
        "pacman",
    ]


def test_delivery_trace_reaches_found_state():
    app = DeliveryDemo()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "delivery"
    assert trace["steps"][0]["event_type"] == "start"
    assert trace["steps"][-1]["event_type"] == "found"
    assert trace["summary"]["result"] == "found"
    assert trace["initial_state"]["labyrinth"]["start"] == [1, 1]
    assert trace["initial_state"]["labyrinth"]["exit"] == [12, 12]


def test_delivery_single_room_configuration_is_solvable():
    app = DeliveryDemo()
    app.load_example("single_room")
    trace = app.get_trace_payload()
    assert trace["summary"]["result"] == "found"
    assert trace["initial_state"]["labyrinth"]["size"] == "single_room"


def test_delivery_collect_all_examples_are_solvable():
    app = DeliveryDemo()
    app.load_example("pacman")
    trace = app.get_trace_payload()
    final_search = trace["steps"][-1]["state_patch"]["search"]
    expected_dots = 245
    assert trace["summary"]["result"] == "found"
    assert trace["steps"][-1]["label"] == "All dots collected"
    assert len(trace["initial_state"]["labyrinth"]["collectibles"]) == expected_dots
    assert len(final_search["collected_dots"]) == expected_dots
    assert final_search["remaining_dots"] == []
    assert len(final_search["final_path"]) > len(
        {tuple(cell) for cell in final_search["final_path"]}
    )


def test_delivery_collectible_dots_use_pacman_maze():
    app = DeliveryDemo()
    app.load_example("pacman")
    dots = app.labyrinth.collectibles
    assert app.labyrinth.rows == 31
    assert app.labyrinth.cols == 28
    assert app.labyrinth.grid[23][13] == "S"
    assert len(dots) == 245
    assert all(app.labyrinth.grid[row][col] == "." for row, col in dots)
    assert any("      " in row for row in app.labyrinth.grid)
    assert any(row.count("#") > 10 for row in app.labyrinth.grid[2:-1])


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


def test_delivery_turns_do_not_move_robot():
    app = DeliveryDemo()
    trace = app.get_trace_payload()
    turn_index = next(
        index
        for index, step in enumerate(trace["steps"])
        if step["event_type"] in {"turn_left", "turn_right"}
    )
    previous_route = trace["steps"][turn_index - 1]["state_patch"]["search"]["current_route"]
    turn_search = trace["steps"][turn_index]["state_patch"]["search"]
    following_search = trace["steps"][turn_index + 1]["state_patch"]["search"]

    assert turn_search["current_route"] == previous_route
    assert turn_search["delivery_heading"] != trace["steps"][turn_index - 1]["state_patch"]["search"]["delivery_heading"]
    assert trace["steps"][turn_index + 1]["event_type"] == "expand"
    assert following_search["current_route"] != turn_search["current_route"]


def test_delivery_fastapi_routes_work():
    app = DeliveryDemo()
    from fastapi.testclient import TestClient

    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "delivery"
