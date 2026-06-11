from fastapi.testclient import TestClient

from ai9414.core.server import create_fastapi_app
from ai9414.strips import BlocksworldDemo, StripsDemo, StripsProblem, run_strips_solver
from ai9414.strips.student import (
    STRIPS_TRACE_ACTIONS,
    apply_action_signature,
    build_unimplemented_strips_result,
    get_applicable_actions,
    get_initial_facts,
    validate_strips_payload,
    validate_strips_solver_result,
)


def test_strips_demo_lists_curated_examples():
    app = StripsDemo()
    assert app.list_examples() == [
        "canonical_delivery",
        "robot_starts_mail_room",
        "keycard_in_office_b",
        "unlocked_lab",
        "lab_via_office_b",
    ]


def test_blocksworld_demo_lists_only_blocksworld_examples():
    app = BlocksworldDemo()
    assert app.list_examples() == [
        "3_block_tower",
        "4_block_tower",
        "5_block_tower",
        "sussman_anomaly",
        "hanoi_5_discs",
        "hanoi_6_discs",
    ]
    assert app.build_state_payload()["data"]["strips_problem"]["domain"] == "blocksworld"


def test_four_and_five_block_towers_start_with_three_stacks():
    for example_name, expected_blocks in (("4_block_tower", 4), ("5_block_tower", 5)):
        app = BlocksworldDemo(problem=example_name)
        problem = app.build_state_payload()["data"]["strips_problem"]
        stacks = problem["initial_stacks"]
        flattened = [block for stack in stacks for block in stack]
        assert len(stacks) == 3
        assert len(flattened) == expected_blocks
        assert any(len(stack) > 1 for stack in stacks)
        assert sorted(flattened) == sorted(problem["blocks"])


def test_strips_trace_reaches_goal_state():
    app = StripsDemo()
    trace = app.get_trace_payload()
    assert trace["app_type"] == "strips"
    assert trace["steps"][0]["event_type"] == "plan_found"
    assert trace["summary"]["result"] == "found"
    assert trace["steps"][-1]["state_patch"]["planning"]["goal_satisfied"] is True


def test_unlocked_example_drops_unlock_action():
    app = StripsDemo(problem="unlocked_lab")
    trace = app.get_trace_payload()
    plan = trace["steps"][0]["state_patch"]["planning"]["plan"]
    assert all(action["name"] != "unlock_door" for action in plan)


def test_sussman_anomaly_blocks_world_plan_reaches_goal():
    app = BlocksworldDemo(problem="sussman_anomaly")
    trace = app.get_trace_payload()
    plan = trace["steps"][0]["state_patch"]["planning"]["plan"]
    assert trace["summary"]["result"] == "found"
    assert trace["steps"][-1]["state_patch"]["planning"]["goal_satisfied"] is True
    assert [action["signature"] for action in plan] == [
        "unstack(a, c)",
        "putdown(a)",
        "pickup(b)",
        "stack(b, c)",
        "pickup(a)",
        "stack(a, b)",
    ]
    assert trace["steps"][-1]["state_patch"]["planning"]["world"]["domain"] == "blocksworld"


def test_hanoi_example_uses_peg_supports_and_size_rule():
    app = BlocksworldDemo(problem="hanoi_5_discs")
    payload = app.build_state_payload()["data"]["strips_problem"]
    trace = app.get_trace_payload()
    assert payload["supports"] == ["left_peg", "middle_peg", "right_peg"]
    assert payload["metadata"]["smaller_on_larger"] is True
    assert payload["metadata"]["hanoi_disc_moves"] == 31
    assert payload["metadata"]["expected_strips_actions"] == 62
    assert trace["summary"]["result"] == "found"
    assert len(trace["steps"][0]["state_patch"]["planning"]["plan"]) == 62
    assert trace["steps"][0]["state_patch"]["planning"]["world"]["block_sizes"]["d1"] == 1
    assert trace["steps"][0]["state_patch"]["planning"]["world"]["block_sizes"]["d5"] == 5


def test_same_small_bfs_shape_solves_strips_and_blocksworld():
    def key(facts):
        return tuple(sorted(facts))

    def done(facts, goal):
        state = set(facts)
        return all(tuple(fact) in state for fact in goal)

    def solve(problem):
        start = get_initial_facts(problem)
        frontier = [(start, [])]
        visited = {key(start)}
        while frontier:
            facts, plan = frontier.pop(0)
            if done(facts, problem["goal"]):
                return plan
            for action in get_applicable_actions(problem, facts):
                next_facts = apply_action_signature(problem, facts, action)
                next_key = key(next_facts)
                if next_key in visited:
                    continue
                visited.add(next_key)
                frontier.append((next_facts, plan + [action]))
        return []

    strips_problem = StripsDemo().build_state_payload()["data"]["strips_problem"]
    blocksworld_problem = BlocksworldDemo(problem="sussman_anomaly").build_state_payload()["data"]["strips_problem"]
    assert solve(strips_problem)
    assert solve(blocksworld_problem) == [
        "unstack(a, c)",
        "putdown(a)",
        "pickup(b)",
        "stack(b, c)",
        "pickup(a)",
        "stack(a, b)",
    ]


def test_load_problem_accepts_custom_problem():
    app = StripsDemo(
        problem=StripsProblem(
            title="Custom",
            rooms=["corridor", "mail_room", "office_a", "office_b", "lab"],
            robot_start="corridor",
            parcel_start="mail_room",
            keycard_start="office_a",
            locked_edge=("corridor", "lab"),
            door_locked=True,
            goal=[("at", "parcel", "lab")],
        )
    )
    payload = app.build_state_payload()
    assert payload["example_name"] is None
    assert payload["data"]["strips_problem"]["title"] == "Custom"


def test_strips_student_helpers_expose_symbolic_state_tools():
    app = StripsDemo()
    problem = validate_strips_payload(app.build_state_payload()["data"]["strips_problem"])
    facts = get_initial_facts(problem)
    actions = get_applicable_actions(problem, facts)
    next_facts = apply_action_signature(problem, facts, actions[0])
    placeholder = build_unimplemented_strips_result()
    assert STRIPS_TRACE_ACTIONS == ("expand", "goal")
    assert any(fact[0] == "at" and fact[1] == "robot" for fact in facts)
    assert isinstance(actions, list)
    assert next_facts != facts
    assert placeholder["status"] == "error"
    assert run_strips_solver


def test_strips_result_validation_accepts_canonical_shape():
    result = validate_strips_solver_result(
        {
            "algorithm": "strips_bfs",
            "status": "found",
            "plan": [
                "move(robot, corridor, office_a)",
                "pickup_keycard(robot, keycard, office_a)",
            ],
            "stats": {
                "expanded_states": 3,
                "generated_states": 4,
                "frontier_peak": 2,
            },
            "search_trace": [
                {
                    "step": 0,
                    "action": "expand",
                    "facts": [["at", "robot", "corridor"]],
                    "plan_prefix": [],
                    "frontier_size": 1,
                }
            ],
        }
    )
    assert result["status"] == "found"


def test_strips_fastapi_routes_work():
    app = StripsDemo()
    with TestClient(create_fastapi_app(app)) as client:
        response = client.get("/api/manifest")
        assert response.status_code == 200
        assert response.json()["app_type"] == "strips"
