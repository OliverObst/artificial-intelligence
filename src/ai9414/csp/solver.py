"""Teaching-oriented backtracking CSP solver with forward checking."""

from __future__ import annotations

import copy
import random
from typing import Any

from ai9414.csp.models import CspProblem

ALGORITHM_NAME = "backtracking_forward_checking"
ALGORITHM_LABEL = "Backtracking + forward checking"
ALGORITHM_NOTE = (
    "The solver makes one assignment at a time, prunes neighbouring domains immediately, "
    "and backtracks whenever a future variable loses every remaining colour."
)


def _choose_variable(
    problem: CspProblem,
    assignments: dict[str, str],
    domains: dict[str, list[str]],
    ordering: str,
) -> str:
    unassigned = [region for region in problem.regions if region not in assignments]
    if ordering in {"fixed", "first_unassigned"}:
        return unassigned[0]

    if ordering != "mrv":
        raise ValueError("Variable ordering must be 'fixed', 'first_unassigned', or 'mrv'.")

    region_order = {region: index for index, region in enumerate(problem.regions)}

    def key(region: str) -> tuple[int, int, int]:
        remaining = len(domains[region])
        future_degree = sum(1 for neighbour in problem.neighbours[region] if neighbour not in assignments)
        return (remaining, -future_degree, region_order[region])

    return min(unassigned, key=key)


def _order_values(values: list[str], ordering: str, rng: random.Random) -> list[str]:
    ordered = list(values)
    if ordering == "default":
        return ordered
    if ordering != "random":
        raise ValueError("Value ordering must be 'default' or 'random'.")
    rng.shuffle(ordered)
    return ordered


def solve_csp_problem(
    problem: CspProblem,
    *,
    variable_ordering: str = "fixed",
    value_ordering: str = "default",
    random_seed: int = 7,
    algorithm: str = ALGORITHM_NAME,
) -> dict[str, Any]:
    """Solve the CSP and return a clean event trace."""

    if algorithm != ALGORITHM_NAME:
        raise ValueError(f"Unsupported algorithm '{algorithm}'.")

    assignments: dict[str, str] = {}
    domains = {region: list(problem.domains[region]) for region in problem.regions}
    events: list[dict[str, Any]] = []
    stats = {
        "assignments": 0,
        "prunes": 0,
        "backtracks": 0,
        "wipeouts": 0,
    }
    rng = random.Random(random_seed)
    step = 0

    def emit(action: str, **payload: Any) -> None:
        nonlocal step
        event = {"step": step, "action": action, **payload}
        events.append(event)
        step += 1

    emit("start")

    def search() -> bool:
        if len(assignments) == len(problem.regions):
            emit("solution_found", assignments=dict(assignments))
            return True

        variable = _choose_variable(problem, assignments, domains, variable_ordering)
        emit("select_variable", variable=variable, domain=list(domains[variable]))

        for value in _order_values(domains[variable], value_ordering, rng):
            emit("try_value", variable=variable, value=value, domain=list(domains[variable]))

            previous_assignments = dict(assignments)
            previous_domains = copy.deepcopy(domains)
            assignments[variable] = value
            domains[variable] = [value]
            stats["assignments"] += 1
            emit("assign", variable=variable, value=value, assignments=dict(assignments))

            changes: list[dict[str, Any]] = []
            wiped_out: str | None = None

            for neighbour in problem.neighbours[variable]:
                if neighbour in assignments:
                    continue
                if value not in domains[neighbour]:
                    continue
                domains[neighbour] = [colour for colour in domains[neighbour] if colour != value]
                changes.append(
                    {
                        "variable": neighbour,
                        "removed": [value],
                        "new_domain": list(domains[neighbour]),
                    }
                )
                stats["prunes"] += 1
                if not domains[neighbour]:
                    wiped_out = neighbour
                    break

            if changes:
                emit(
                    "prune",
                    variable=variable,
                    value=value,
                    changes=changes,
                    cause=f"{variable} = {value}",
                )

            if wiped_out is not None:
                stats["wipeouts"] += 1
                emit("domain_wipeout", variable=wiped_out, cause=f"{variable} = {value}")
                assignments.clear()
                assignments.update(previous_assignments)
                domains.clear()
                domains.update(previous_domains)
                stats["backtracks"] += 1
                emit("backtrack", variable=variable, value=value, failed_variable=wiped_out)
                emit("unassign", variable=variable, value=value)
                continue

            if search():
                return True

            assignments.clear()
            assignments.update(previous_assignments)
            domains.clear()
            domains.update(previous_domains)
            stats["backtracks"] += 1
            emit("backtrack", variable=variable, value=value)
            emit("unassign", variable=variable, value=value)

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
