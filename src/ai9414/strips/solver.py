"""Teaching-oriented STRIPS planner and state helpers."""

from __future__ import annotations

import copy
import re
from collections import deque
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from ai9414.strips.models import CANONICAL_ROOMS, StripsProblem

ALGORITHM_LABEL = "Forward STRIPS planning (BFS)"
ALGORITHM_NOTE = (
    "The planner searches over symbolic world states, not over the graphics. "
    "Each grounded action changes predicates, and the room view on the right is only a rendering of those facts."
)
DOOR_NAME = "lab_door"
ROOM_ORDER = {room: index for index, room in enumerate(("office_a", "mail_room", "office_b", "corridor", "lab"))}
FACT_ORDER = {
    "at": 0,
    "carrying": 1,
    "has": 2,
    "handempty": 3,
    "locked": 4,
    "unlocked": 5,
    "connected": 6,
    "door_between": 7,
}
ACTION_ORDER = {
    "pickup_keycard": 0,
    "unlock_door": 1,
    "pickup_parcel": 2,
    "drop_parcel": 3,
    "move": 4,
}
ACTION_RE = re.compile(r"^(?P<name>[a-z_]+)\((?P<args>.*)\)$")

Fact = tuple[str, ...]


@dataclass(frozen=True)
class GroundedAction:
    name: str
    args: tuple[str, ...]
    preconditions: tuple[Fact, ...]
    add_effects: tuple[Fact, ...]
    delete_effects: tuple[Fact, ...]
    category: str

    @property
    def signature(self) -> str:
        return f"{self.name}({', '.join(self.args)})"


@dataclass(frozen=True)
class PlannerSearchTraceEntry:
    index: int
    depth: int
    frontier_size: int
    state_facts: tuple[Fact, ...]
    applicable_actions: tuple[GroundedAction, ...]
    plan_prefix: tuple[str, ...]
    goal_reached: bool


@dataclass
class PlannerResult:
    trace_id: str
    problem: StripsProblem
    initial_state: frozenset[Fact]
    plan: list[GroundedAction]
    search_trace: list[PlannerSearchTraceEntry]
    status: str
    stats: dict[str, int]


def canonical_edges(problem: StripsProblem) -> list[tuple[str, str]]:
    other_door_room = door_other_room(problem)
    edges = [
        ("corridor", "mail_room"),
        ("corridor", "office_a"),
        ("corridor", "office_b"),
        (other_door_room, "lab"),
    ]
    return edges


def door_other_room(problem: StripsProblem) -> str:
    left, right = problem.locked_edge
    return right if left == "lab" else left


def static_facts(problem: StripsProblem) -> set[Fact]:
    facts: set[Fact] = set()
    for left, right in canonical_edges(problem):
        facts.add(("connected", left, right))
        facts.add(("connected", right, left))
    facts.add(("door_between", DOOR_NAME, problem.locked_edge[0], problem.locked_edge[1]))
    return facts


def initial_state(problem: StripsProblem) -> frozenset[Fact]:
    facts = static_facts(problem)
    facts.update(
        {
            ("at", "robot", problem.robot_start),
            ("at", "parcel", problem.parcel_start),
            ("at", "keycard", problem.keycard_start),
            ("handempty", "robot"),
        }
    )
    if problem.door_locked:
        facts.add(("locked", DOOR_NAME))
    else:
        facts.add(("unlocked", DOOR_NAME))
    return frozenset(facts)


def goal_satisfied(problem: StripsProblem, state: frozenset[Fact]) -> bool:
    return all(tuple(fact) in state for fact in problem.goal)


def robot_room(state: frozenset[Fact]) -> str:
    for fact in state:
        if fact[:2] == ("at", "robot"):
            return fact[2]
    raise ValueError("State does not contain the robot location.")


def contains_fact(state: frozenset[Fact], *fact: str) -> bool:
    return tuple(fact) in state


def is_door_edge(problem: StripsProblem, left: str, right: str) -> bool:
    return {left, right} == set(problem.locked_edge)


def fact_sort_key(raw_fact: Fact) -> tuple[Any, ...]:
    predicate = raw_fact[0]
    args = raw_fact[1:]
    normalised_args = tuple(ROOM_ORDER.get(arg, 99) if arg in ROOM_ORDER else arg for arg in args)
    return (FACT_ORDER.get(predicate, 99), normalised_args, raw_fact)


def sort_facts(facts: list[Fact] | tuple[Fact, ...] | frozenset[Fact]) -> list[Fact]:
    return sorted((tuple(fact) for fact in facts), key=fact_sort_key)


def render_fact(raw_fact: Fact) -> str:
    predicate, *args = raw_fact
    return f"{predicate}({', '.join(args)})"


def fact_payload(raw_fact: Fact) -> dict[str, Any]:
    return {
        "predicate": raw_fact[0],
        "args": list(raw_fact[1:]),
        "text": render_fact(raw_fact),
    }


def action_sort_key(action: GroundedAction) -> tuple[Any, ...]:
    if action.name == "move":
        target = action.args[-1]
        return (ACTION_ORDER[action.name], ROOM_ORDER.get(target, 99), action.signature)
    room_args = tuple(ROOM_ORDER.get(arg, 99) if arg in ROOM_ORDER else arg for arg in action.args)
    return (ACTION_ORDER.get(action.name, 99), room_args, action.signature)


def action_payload(action: GroundedAction) -> dict[str, Any]:
    return {
        "name": action.name,
        "args": list(action.args),
        "signature": action.signature,
        "category": action.category,
        "preconditions": [fact_payload(fact) for fact in sort_facts(action.preconditions)],
        "add_effects": [fact_payload(fact) for fact in sort_facts(action.add_effects)],
        "delete_effects": [fact_payload(fact) for fact in sort_facts(action.delete_effects)],
    }


def enumerate_applicable_actions(problem: StripsProblem, state: frozenset[Fact]) -> list[GroundedAction]:
    room = robot_room(state)
    applicable: list[GroundedAction] = []

    for fact in sort_facts([item for item in state if item[0] == "connected" and item[1] == room]):
        target = fact[2]
        requires_unlocked = is_door_edge(problem, room, target)
        preconditions = [("at", "robot", room), ("connected", room, target)]
        if requires_unlocked:
            if not contains_fact(state, "unlocked", DOOR_NAME):
                continue
            preconditions.append(("unlocked", DOOR_NAME))
        applicable.append(
            GroundedAction(
                name="move",
                args=("robot", room, target),
                preconditions=tuple(preconditions),
                add_effects=(("at", "robot", target),),
                delete_effects=(("at", "robot", room),),
                category="movement",
            )
        )

    if contains_fact(state, "at", "parcel", room) and contains_fact(state, "handempty", "robot"):
        applicable.append(
            GroundedAction(
                name="pickup_parcel",
                args=("robot", "parcel", room),
                preconditions=(
                    ("at", "robot", room),
                    ("at", "parcel", room),
                    ("handempty", "robot"),
                ),
                add_effects=(("carrying", "robot", "parcel"),),
                delete_effects=(("at", "parcel", room), ("handempty", "robot")),
                category="manipulation",
            )
        )

    if contains_fact(state, "carrying", "robot", "parcel"):
        applicable.append(
            GroundedAction(
                name="drop_parcel",
                args=("robot", "parcel", room),
                preconditions=(("at", "robot", room), ("carrying", "robot", "parcel")),
                add_effects=(("at", "parcel", room), ("handempty", "robot")),
                delete_effects=(("carrying", "robot", "parcel"),),
                category="manipulation",
            )
        )

    if contains_fact(state, "at", "keycard", room) and contains_fact(state, "handempty", "robot"):
        applicable.append(
            GroundedAction(
                name="pickup_keycard",
                args=("robot", "keycard", room),
                preconditions=(
                    ("at", "robot", room),
                    ("at", "keycard", room),
                    ("handempty", "robot"),
                ),
                add_effects=(("has", "robot", "keycard"), ("handempty", "robot")),
                delete_effects=(("at", "keycard", room),),
                category="manipulation",
            )
        )

    door_left, door_right = problem.locked_edge
    if contains_fact(state, "locked", DOOR_NAME) and contains_fact(state, "has", "robot", "keycard"):
        if room in {door_left, door_right}:
            other_room = door_right if room == door_left else door_left
            applicable.append(
                GroundedAction(
                    name="unlock_door",
                    args=("robot", "keycard", DOOR_NAME, room, other_room),
                    preconditions=(
                        ("at", "robot", room),
                        ("has", "robot", "keycard"),
                        ("door_between", DOOR_NAME, door_left, door_right),
                        ("locked", DOOR_NAME),
                    ),
                    add_effects=(("unlocked", DOOR_NAME),),
                    delete_effects=(("locked", DOOR_NAME),),
                    category="door",
                )
            )

    return sorted(applicable, key=action_sort_key)


def apply_action(state: frozenset[Fact], action: GroundedAction) -> frozenset[Fact]:
    next_state = set(state)
    for fact in action.delete_effects:
        next_state.discard(fact)
    for fact in action.add_effects:
        next_state.add(fact)
    return frozenset(next_state)


def parse_action_signature(signature: str) -> tuple[str, tuple[str, ...]]:
    match = ACTION_RE.match(signature.strip())
    if match is None:
        raise ValueError(f"Action '{signature}' is not in the expected grounded form name(arg1, arg2, ...).")
    name = match.group("name")
    args_part = match.group("args").strip()
    args = tuple(part.strip() for part in args_part.split(",")) if args_part else ()
    if any(not arg for arg in args):
        raise ValueError(f"Action '{signature}' contains an empty argument.")
    return name, args


def action_from_signature(problem: StripsProblem, state: frozenset[Fact], signature: str) -> GroundedAction:
    parsed_name, parsed_args = parse_action_signature(signature)
    for action in enumerate_applicable_actions(problem, state):
        if action.name == parsed_name and action.args == parsed_args:
            return action
    raise ValueError(f"Action '{signature}' is not applicable in the current state.")


def validate_action_plan(problem: StripsProblem, signatures: list[str]) -> list[GroundedAction]:
    state = initial_state(problem)
    actions: list[GroundedAction] = []
    for index, signature in enumerate(signatures):
        action = action_from_signature(problem, state, signature)
        actions.append(action)
        state = apply_action(state, action)
        if goal_satisfied(problem, state) and index < len(signatures) - 1:
            continue
    return actions


def world_payload(problem: StripsProblem, state: frozenset[Fact]) -> dict[str, Any]:
    room_lookup = {
        "robot": None,
        "parcel": None,
        "keycard": None,
    }
    for fact in state:
        if fact[0] == "at" and fact[1] in room_lookup:
            room_lookup[fact[1]] = fact[2]
    return {
        "rooms": list(CANONICAL_ROOMS),
        "robot_room": room_lookup["robot"],
        "parcel_room": room_lookup["parcel"],
        "parcel_carried": contains_fact(state, "carrying", "robot", "parcel"),
        "keycard_room": room_lookup["keycard"],
        "robot_has_keycard": contains_fact(state, "has", "robot", "keycard"),
        "door_locked": contains_fact(state, "locked", DOOR_NAME),
        "door_edge": list(problem.locked_edge),
    }


def build_planning_snapshot(
    problem: StripsProblem,
    *,
    state: frozenset[Fact],
    plan: list[GroundedAction],
    selected_action: GroundedAction | None,
    plan_index: int,
    search_trace: list[PlannerSearchTraceEntry],
    stats: dict[str, int],
) -> dict[str, Any]:
    facts = sort_facts(state)
    applicable = enumerate_applicable_actions(problem, state)
    plan_payload = [action_payload(action) for action in plan]
    return {
        "planning": {
            "facts": [fact_payload(fact) for fact in facts],
            "goal_facts": [fact_payload(tuple(fact)) for fact in problem.goal],
            "applicable_actions": [action_payload(action) for action in applicable],
            "selected_action": action_payload(selected_action) if selected_action is not None else None,
            "plan": plan_payload,
            "plan_index": plan_index,
            "goal_satisfied": goal_satisfied(problem, state),
            "world": world_payload(problem, state),
            "search_trace": [
                {
                    "index": entry.index,
                    "depth": entry.depth,
                    "frontier_size": entry.frontier_size,
                    "goal_reached": entry.goal_reached,
                    "plan_prefix": list(entry.plan_prefix),
                    "state_facts": [render_fact(fact) for fact in sort_facts(entry.state_facts)],
                    "applicable_actions": [action.signature for action in entry.applicable_actions],
                }
                for entry in search_trace
            ],
        },
        "search": {
            "status": "goal reached" if goal_satisfied(problem, state) else "plan ready" if plan else "no plan",
            "expanded_states": int(stats.get("expanded_states", 0)),
            "generated_states": int(stats.get("generated_states", 0)),
            "frontier_peak": int(stats.get("frontier_peak", 0)),
            "current_depth": max(plan_index, 0),
        },
        "stats": copy.deepcopy(stats),
    }


def solve_strips_problem(problem: StripsProblem) -> PlannerResult:
    start_state = initial_state(problem)
    queue: deque[tuple[frozenset[Fact], list[GroundedAction]]] = deque([(start_state, [])])
    visited = {start_state}
    stats = {"expanded_states": 0, "generated_states": 1, "frontier_peak": 1}
    search_trace: list[PlannerSearchTraceEntry] = []
    trace_id = f"strips-{uuid4().hex[:8]}"

    while queue:
        stats["frontier_peak"] = max(stats["frontier_peak"], len(queue))
        state, plan = queue.popleft()
        applicable = enumerate_applicable_actions(problem, state)
        goal_here = goal_satisfied(problem, state)
        search_trace.append(
            PlannerSearchTraceEntry(
                index=len(search_trace),
                depth=len(plan),
                frontier_size=len(queue),
                state_facts=tuple(sort_facts(state)),
                applicable_actions=tuple(applicable),
                plan_prefix=tuple(action.signature for action in plan),
                goal_reached=goal_here,
            )
        )
        stats["expanded_states"] += 1

        if goal_here:
            return PlannerResult(
                trace_id=trace_id,
                problem=problem,
                initial_state=start_state,
                plan=list(plan),
                search_trace=search_trace,
                status="found",
                stats=stats,
            )

        for action in applicable:
            next_state = apply_action(state, action)
            if next_state in visited:
                continue
            visited.add(next_state)
            queue.append((next_state, [*plan, action]))
            stats["generated_states"] += 1

    return PlannerResult(
        trace_id=trace_id,
        problem=problem,
        initial_state=start_state,
        plan=[],
        search_trace=search_trace,
        status="not_found",
        stats=stats,
    )
