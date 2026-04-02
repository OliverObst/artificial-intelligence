"""Teaching-oriented delivery scheduling CSP solver."""

from __future__ import annotations

import copy
import random
from typing import Any

from ai9414.delivery_csp.models import DeliveryConstraint, DeliveryCspProblem

ALGORITHM_NAME = "backtracking_forward_checking"
ALGORITHM_LABEL = "Backtracking + forward checking"
ALGORITHM_NOTE = (
    "The solver assigns one delivery at a time, prunes future slot-room options immediately, "
    "and backtracks whenever some delivery loses every remaining time slot."
)


def _constraint_graph(problem: DeliveryCspProblem) -> dict[str, set[str]]:
    graph = {delivery.id: set() for delivery in problem.deliveries}
    for constraint in problem.constraints:
        graph[constraint.left].add(constraint.right)
        graph[constraint.right].add(constraint.left)
    return graph


def _choose_variable(
    problem: DeliveryCspProblem,
    assignments: dict[str, str],
    domains: dict[str, list[str]],
    ordering: str,
    graph: dict[str, set[str]],
) -> str:
    unassigned = [delivery.id for delivery in problem.deliveries if delivery.id not in assignments]
    if ordering in {"fixed", "first_unassigned"}:
        return unassigned[0]
    if ordering != "mrv":
        raise ValueError("Variable ordering must be 'fixed', 'first_unassigned', or 'mrv'.")

    delivery_order = {delivery.id: index for index, delivery in enumerate(problem.deliveries)}

    def key(delivery_id: str) -> tuple[int, int, int]:
        remaining = len(domains[delivery_id])
        future_degree = sum(1 for neighbour in graph[delivery_id] if neighbour not in assignments)
        return (remaining, -future_degree, delivery_order[delivery_id])

    return min(unassigned, key=key)


def _order_values(values: list[str], ordering: str, rng: random.Random) -> list[str]:
    ordered = list(values)
    if ordering == "default":
        return ordered
    if ordering != "random":
        raise ValueError("Value ordering must be 'default' or 'random'.")
    rng.shuffle(ordered)
    return ordered


def _violates_pair(
    problem: DeliveryCspProblem,
    left_delivery: str,
    left_value_id: str,
    right_delivery: str,
    right_value_id: str,
) -> bool:
    value_map = problem.value_map()
    slot_order = problem.slot_order()
    left_value = value_map[left_value_id]
    right_value = value_map[right_value_id]

    # Implicit room capacity: one delivery per room and slot.
    if left_value.slot == right_value.slot and left_value.room == right_value.room:
        return True

    for constraint in problem.constraints:
        if constraint.left == left_delivery and constraint.right == right_delivery:
            if _violates_constraint(constraint, left_value.slot, right_value.slot, slot_order):
                return True
        elif constraint.left == right_delivery and constraint.right == left_delivery:
            if _violates_constraint(constraint, right_value.slot, left_value.slot, slot_order):
                return True
    return False


def _violates_constraint(
    constraint: DeliveryConstraint,
    left_slot_id: str,
    right_slot_id: str,
    slot_order: dict[str, int],
) -> bool:
    if constraint.kind == "not_same_slot":
        return left_slot_id == right_slot_id
    if constraint.kind == "precedence":
        return slot_order[left_slot_id] >= slot_order[right_slot_id]
    raise ValueError(f"Unsupported constraint kind '{constraint.kind}'.")


def solve_delivery_csp_problem(
    problem: DeliveryCspProblem,
    *,
    variable_ordering: str = "fixed",
    value_ordering: str = "default",
    random_seed: int = 7,
    algorithm: str = ALGORITHM_NAME,
) -> dict[str, Any]:
    """Solve the delivery scheduling CSP and return a clean event trace."""

    if algorithm != ALGORITHM_NAME:
        raise ValueError(f"Unsupported algorithm '{algorithm}'.")

    assignments: dict[str, str] = {}
    domains = {delivery.id: list(problem.domains[delivery.id]) for delivery in problem.deliveries}
    events: list[dict[str, Any]] = []
    stats = {"assignments": 0, "prunes": 0, "backtracks": 0, "wipeouts": 0}
    rng = random.Random(random_seed)
    graph = _constraint_graph(problem)
    step = 0

    def emit(action: str, **payload: Any) -> None:
        nonlocal step
        events.append({"step": step, "action": action, **payload})
        step += 1

    emit("start")

    def search() -> bool:
        if len(assignments) == len(problem.deliveries):
            emit("solution_found", assignments=dict(assignments))
            return True

        variable = _choose_variable(problem, assignments, domains, variable_ordering, graph)
        emit("select_variable", variable=variable, domain=list(domains[variable]))

        for value_id in _order_values(domains[variable], value_ordering, rng):
            emit("try_value", variable=variable, value=value_id, domain=list(domains[variable]))

            previous_assignments = dict(assignments)
            previous_domains = copy.deepcopy(domains)
            assignments[variable] = value_id
            domains[variable] = [value_id]
            stats["assignments"] += 1
            emit("assign", variable=variable, value=value_id, assignments=dict(assignments))

            changes: list[dict[str, Any]] = []
            wiped_out: str | None = None
            for other_delivery in [delivery.id for delivery in problem.deliveries if delivery.id not in assignments]:
                removed = [
                    candidate
                    for candidate in domains[other_delivery]
                    if _violates_pair(problem, variable, value_id, other_delivery, candidate)
                ]
                if not removed:
                    continue
                removed_set = set(removed)
                domains[other_delivery] = [
                    candidate for candidate in domains[other_delivery] if candidate not in removed_set
                ]
                changes.append(
                    {
                        "variable": other_delivery,
                        "removed": removed,
                        "new_domain": list(domains[other_delivery]),
                    }
                )
                stats["prunes"] += len(removed)
                if not domains[other_delivery]:
                    wiped_out = other_delivery
                    break

            if changes:
                emit(
                    "prune",
                    variable=variable,
                    value=value_id,
                    changes=changes,
                    cause=f"{variable} = {value_id}",
                )

            if wiped_out is not None:
                stats["wipeouts"] += 1
                emit("domain_wipeout", variable=wiped_out, cause=f"{variable} = {value_id}")
                assignments.clear()
                assignments.update(previous_assignments)
                domains.clear()
                domains.update(previous_domains)
                stats["backtracks"] += 1
                emit("backtrack", variable=variable, value=value_id, failed_variable=wiped_out)
                emit("unassign", variable=variable, value=value_id)
                continue

            if search():
                return True

            assignments.clear()
            assignments.update(previous_assignments)
            domains.clear()
            domains.update(previous_domains)
            stats["backtracks"] += 1
            emit("backtrack", variable=variable, value=value_id)
            emit("unassign", variable=variable, value=value_id)

        return False

    solved = search()
    if not solved:
        emit("failure")

    return {
        "algorithm": ALGORITHM_NAME,
        "status": "found" if solved else "not_found",
        "events": events,
        "assignment": dict(assignments) if solved else {},
        "stats": stats,
    }
