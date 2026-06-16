"""Resolution proof construction for the live refutation demo."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from ai9414.logic.models import normalise_literal
from ai9414.resolution.models import ResolutionProblem, ResolutionProofStep, complement, literal_variable


@dataclass(frozen=True)
class ResolutionRawStep:
    event_type: str
    label: str
    annotation: str
    teaching_note: str | None
    snapshot: dict[str, Any]


@dataclass(frozen=True)
class ResolutionResult:
    trace_id: str
    status: str
    initial_data: dict[str, Any]
    raw_steps: list[ResolutionRawStep]


def clause_expression(literals: list[str]) -> str:
    if not literals:
        return "□"
    return " ∨ ".join(literals)


def resolve_pair(left_clause: list[str], right_clause: list[str], pivot: str) -> tuple[list[str], str | None]:
    variable = literal_variable(pivot)
    positive = variable
    negative = f"~{variable}"

    if positive in left_clause and negative in right_clause:
        left_drop, right_drop = positive, negative
    elif negative in left_clause and positive in right_clause:
        left_drop, right_drop = negative, positive
    else:
        return [], f"Cleft and Cright do not contain complementary literals for {variable}."

    resolvent: list[str] = []
    seen: set[str] = set()
    for literal in [*left_clause, *right_clause]:
        value = normalise_literal(literal)
        if value in {left_drop, right_drop} or value in seen:
            continue
        seen.add(value)
        resolvent.append(value)

    if any(complement(literal) in seen for literal in resolvent):
        return resolvent, "The resolvent is a tautology, so it is true but not useful for closing the proof."
    return resolvent, None


def build_resolution_result(problem: ResolutionProblem) -> ResolutionResult:
    clauses = [_clause_record(index + 1, clause, "given") for index, clause in enumerate(problem.clauses)]
    proof_steps = [_proof_step_record(index + 1, item) for index, item in enumerate(problem.steps)]
    initial_data = _snapshot(problem, copy.deepcopy(clauses), copy.deepcopy(proof_steps), "ready", None)
    snapshot = copy.deepcopy(initial_data)
    raw_steps = [
        ResolutionRawStep(
            event_type="start",
            label="Start with clauses",
            annotation="Resolution works over clauses. A refutation proof succeeds when it derives the empty clause □.",
            teaching_note="For entailment, these clauses represent KB together with the negated query.",
            snapshot=snapshot,
        )
    ]

    status = "in_progress"
    for index, attempted in enumerate(problem.steps, start=1):
        left = _lookup_clause(clauses, attempted.left)
        right = _lookup_clause(clauses, attempted.right)
        if left is None or right is None:
            message = f"Step {index} refers to a clause that has not been derived yet."
            proof_steps[index - 1]["status"] = "invalid"
            proof_steps[index - 1]["explanation"] = message
            raw_steps.append(
                ResolutionRawStep(
                    event_type="invalid_step",
                    label=f"Invalid proof step {index}",
                    annotation=message,
                    teaching_note="Resolution steps can only use given clauses or clauses derived earlier in the proof.",
                    snapshot=_snapshot(problem, clauses, proof_steps, "invalid attempt", index),
                )
            )
            status = "invalid_attempt"
            break

        resolvent, warning = resolve_pair(left["literals"], right["literals"], attempted.pivot)
        if warning and "do not contain" in warning:
            proof_steps[index - 1]["status"] = "invalid"
            proof_steps[index - 1]["explanation"] = warning
            _mark_selected(clauses, attempted.left, attempted.right, None)
            raw_steps.append(
                ResolutionRawStep(
                    event_type="invalid_step",
                    label=f"Invalid proof step {index}",
                    annotation=warning.replace("Cleft", f"C{attempted.left}").replace("Cright", f"C{attempted.right}"),
                    teaching_note="A resolution step needs one literal and its negation.",
                    snapshot=_snapshot(problem, clauses, proof_steps, "invalid attempt", index),
                )
            )
            status = "invalid_attempt"
            break

        new_id = len(clauses) + 1
        derived = _clause_record(
            new_id,
            resolvent,
            "derived",
            parents=[attempted.left, attempted.right],
            pivot=attempted.pivot,
        )
        clauses.append(derived)
        proof_steps[index - 1]["status"] = "done"
        proof_steps[index - 1]["resolvent_id"] = new_id
        proof_steps[index - 1]["resolvent"] = clause_expression(resolvent)
        proof_steps[index - 1]["explanation"] = attempted.note or _step_explanation(attempted, resolvent)
        _mark_selected(clauses, attempted.left, attempted.right, new_id)
        status = "refuted" if not resolvent else "deriving"
        label = f"Resolve C{attempted.left} and C{attempted.right} on {attempted.pivot}"
        annotation = f"Derived C{new_id}: {clause_expression(resolvent)}."
        if not resolvent:
            annotation += " The empty clause closes the refutation."
        elif warning:
            annotation += f" {warning}"
        raw_steps.append(
            ResolutionRawStep(
                event_type="resolve" if resolvent else "empty_clause",
                label=label,
                annotation=annotation,
                teaching_note=attempted.note or None,
                snapshot=_snapshot(problem, clauses, proof_steps, status, index),
            )
        )
        if not resolvent:
            break

    if status == "refuted":
        final_status = "refuted"
        label = "Refutation complete"
        annotation = "Deriving □ means the clauses KB ∧ not query are unsatisfiable, so the original query is entailed."
    elif status == "invalid_attempt":
        final_status = "invalid_attempt"
        label = "Proof attempt stopped"
        annotation = "The attempted proof step is not a valid resolution step."
    else:
        final_status = "open"
        label = "Proof attempt open"
        annotation = "No empty clause was derived. The attempt may be incomplete, or the entailment may not hold."

    raw_steps.append(
        ResolutionRawStep(
            event_type="finished",
            label=label,
            annotation=annotation,
            teaching_note=None,
            snapshot=_snapshot(problem, clauses, proof_steps, final_status, None),
        )
    )
    return ResolutionResult(
        trace_id=f"resolution-{uuid4().hex[:8]}",
        status=final_status,
        initial_data=initial_data,
        raw_steps=raw_steps,
    )


def _clause_record(
    clause_id: int,
    literals: list[str],
    kind: str,
    *,
    parents: list[int] | None = None,
    pivot: str | None = None,
) -> dict[str, Any]:
    return {
        "id": clause_id,
        "label": f"C{clause_id}",
        "literals": list(literals),
        "expression": clause_expression(literals),
        "kind": kind,
        "parents": parents or [],
        "pivot": pivot,
        "status": "empty" if not literals else "available",
    }


def _proof_step_record(index: int, step: ResolutionProofStep) -> dict[str, Any]:
    return {
        "step": index,
        "left": step.left,
        "right": step.right,
        "pivot": step.pivot,
        "status": "pending",
        "resolvent_id": None,
        "resolvent": "",
        "explanation": step.note,
    }


def _lookup_clause(clauses: list[dict[str, Any]], clause_id: int) -> dict[str, Any] | None:
    for clause in clauses:
        if clause["id"] == clause_id:
            return clause
    return None


def _mark_selected(clauses: list[dict[str, Any]], left_id: int, right_id: int, new_id: int | None) -> None:
    for clause in clauses:
        if clause["id"] in {left_id, right_id}:
            clause["status"] = "selected"
        elif new_id is not None and clause["id"] == new_id:
            clause["status"] = "empty" if not clause["literals"] else "new"
        elif not clause["literals"]:
            clause["status"] = "empty"
        else:
            clause["status"] = "available"


def _step_explanation(step: ResolutionProofStep, resolvent: list[str]) -> str:
    return f"Remove {step.pivot} and ~{step.pivot}; keep the remaining literals: {clause_expression(resolvent)}."


def _snapshot(
    problem: ResolutionProblem,
    clauses: list[dict[str, Any]],
    proof_steps: list[dict[str, Any]],
    status: str,
    active_step: int | None,
) -> dict[str, Any]:
    derived_count = sum(1 for clause in clauses if clause["kind"] == "derived")
    empty_found = any(not clause["literals"] for clause in clauses)
    return {
        "example_title": problem.title,
        "example_subtitle": problem.subtitle,
        "algorithm_label": "Resolution refutation",
        "problem_mode": "resolution",
        "resolution_problem": problem.model_dump(),
        "resolution": {
            "title": problem.title,
            "subtitle": problem.subtitle,
            "query": problem.query,
            "entailment_target": problem.entailment_target,
            "variables": list(problem.variables),
            "visualisation": dict(problem.visualisation),
            "clauses": [dict(clause) for clause in clauses],
            "proof_steps": [dict(step) for step in proof_steps],
            "active_step": active_step,
            "status": status,
            "summary": {
                "given": len(problem.clauses),
                "derived": derived_count,
                "total_clauses": len(clauses),
                "proof_steps": len(proof_steps),
                "completed_steps": sum(1 for step in proof_steps if step["status"] == "done"),
                "empty_clause_found": empty_found,
            },
        },
        "stats": {
            "given_clauses": len(problem.clauses),
            "derived_clauses": derived_count,
            "proof_steps": len(proof_steps),
            "completed_steps": sum(1 for step in proof_steps if step["status"] == "done"),
        },
    }
