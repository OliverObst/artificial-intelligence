"""Teaching-oriented DPLL solver and trace recorder."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from ai9414.logic.models import DpllTreeNode, LogicProblem, VariableOrder

ALGORITHM_LABEL = "DPLL"
ALGORITHM_NOTE = (
    "DPLL treats propositional reasoning as a structured search over partial assignments. "
    "Unit propagation and pure literals reduce the search space before DPLL makes an explicit branch."
)


@dataclass
class RawTraceStep:
    event_type: str
    label: str
    annotation: str
    teaching_note: str
    snapshot: dict[str, Any]


@dataclass
class SolverResult:
    trace_id: str
    problem: LogicProblem
    raw_steps: list[RawTraceStep]
    initial_data: dict[str, Any]
    status: str
    assignment: dict[str, bool]


@dataclass(frozen=True)
class ClauseEvaluation:
    index: int
    status: str
    literals: list[dict[str, Any]]
    unit_literal: str | None
    text: str


class _TraceRecorder:
    def __init__(
        self,
        problem: LogicProblem,
        *,
        unit_propagation: bool,
        pure_literals: bool,
        variable_order: VariableOrder,
    ) -> None:
        self.problem = problem
        self.tree_nodes: dict[str, DpllTreeNode] = {}
        self.visible_tree_ids: list[str] = []
        self.raw_steps: list[RawTraceStep] = []
        self.assignment: dict[str, bool] = {}
        self.assignment_order: list[dict[str, Any]] = []
        self.active_tree_node: str | None = None
        self.active_tree_path: list[str] = []
        self.final_tree_path: list[str] = []
        self.finished = False
        self.status = "ready"
        self.result: str | None = None
        self.tree_counter = 0
        self.trace_id = f"logic-{uuid4().hex[:8]}"
        self.options = {
            "unit_propagation": unit_propagation,
            "pure_literals": pure_literals,
            "variable_order": variable_order,
        }
        self.stats = {
            "decisions": 0,
            "forced_assignments": 0,
            "contradictions": 0,
            "backtracks": 0,
        }

    def create_tree_node(
        self,
        *,
        graph_node: str,
        assignment_text: str,
        parent: str | None,
        depth: int,
        status: str,
        reason: str,
        terminal: bool = False,
    ) -> str:
        tree_id = f"t{self.tree_counter}"
        self.tree_counter += 1
        self.tree_nodes[tree_id] = DpllTreeNode(
            tree_id=tree_id,
            graph_node=graph_node,
            assignment_text=assignment_text,
            parent=parent,
            depth=depth,
            status=status,
            order=len(self.visible_tree_ids),
            terminal=terminal,
            reason=reason,
        )
        self.visible_tree_ids.append(tree_id)
        return tree_id

    def set_status(self, tree_id: str, status: str) -> None:
        if tree_id in self.tree_nodes:
            self.tree_nodes[tree_id].status = status

    def set_current_state(
        self,
        *,
        assignment: dict[str, bool],
        assignment_order: list[dict[str, Any]],
        active_tree_node: str | None,
        active_tree_path: list[str],
        status: str,
    ) -> None:
        self.assignment = dict(assignment)
        self.assignment_order = copy.deepcopy(assignment_order)
        self.active_tree_node = active_tree_node
        self.active_tree_path = list(active_tree_path)
        self.status = status

    def snapshot(self) -> dict[str, Any]:
        evaluated = evaluate_formula(self.problem.clauses, self.assignment)
        summary = {
            "satisfied": sum(1 for clause in evaluated if clause.status == "satisfied"),
            "unresolved": sum(1 for clause in evaluated if clause.status == "unresolved"),
            "unit": sum(1 for clause in evaluated if clause.status == "unit"),
            "contradicted": sum(1 for clause in evaluated if clause.status == "contradicted"),
            "assigned_variables": len(self.assignment),
            "total_variables": len(self.problem.variables),
        }
        return {
            "tree": {
                "nodes": [self.tree_nodes[tree_id].model_dump() for tree_id in self.visible_tree_ids]
            },
            "search": {
                "active_tree_node": self.active_tree_node,
                "active_tree_path": list(self.active_tree_path),
                "best_tree_path": [],
                "final_tree_path": list(self.final_tree_path),
                "finished": self.finished,
                "status": self.status,
                "result": self.result,
            },
            "logic": {
                "mode": self.problem.mode,
                "variables": list(self.problem.variables),
                "clauses": [clause.__dict__ for clause in evaluated],
                "summary": summary,
                "assignment": _assignment_items(self.assignment_order),
                "kb_formulas": list(self.problem.kb_formulas),
                "query": self.problem.query,
                "entailment_target": self.problem.entailment_target,
                "original_input": list(self.problem.original_input),
            },
            "stats": copy.deepcopy(self.stats),
        }

    def record(
        self,
        *,
        event_type: str,
        label: str,
        annotation: str,
        teaching_note: str,
    ) -> None:
        self.raw_steps.append(
            RawTraceStep(
                event_type=event_type,
                label=label,
                annotation=annotation,
                teaching_note=teaching_note,
                snapshot=self.snapshot(),
            )
        )

    def initial_data(self) -> dict[str, Any]:
        return {
            "example_title": self.problem.title,
            "example_subtitle": self.problem.subtitle,
            "algorithm_label": ALGORITHM_LABEL,
            "algorithm_note": ALGORITHM_NOTE,
            "goal_label": (
                "Find a satisfying assignment"
                if self.problem.mode == "sat"
                else "Test whether KB entails the query by checking whether KB and not query are unsatisfiable"
            ),
            "problem_mode": self.problem.mode,
            **self.snapshot(),
        }


def solve_dpll(
    problem: LogicProblem,
    *,
    unit_propagation: bool = True,
    pure_literals: bool = False,
    variable_order: VariableOrder = "alphabetical",
) -> SolverResult:
    recorder = _TraceRecorder(
        problem,
        unit_propagation=unit_propagation,
        pure_literals=pure_literals,
        variable_order=variable_order,
    )

    root_id = recorder.create_tree_node(
        graph_node="start",
        assignment_text="No assignments",
        parent=None,
        depth=0,
        status="active",
        reason="start",
    )
    recorder.set_current_state(
        assignment={},
        assignment_order=[],
        active_tree_node=root_id,
        active_tree_path=[root_id],
        status="searching",
    )
    recorder.record(
        event_type="start",
        label="Start DPLL",
        annotation=(
            "The clause list is ready. DPLL will propagate forced literals first, "
            "then branch only when a genuine choice remains."
        ),
        teaching_note=ALGORITHM_NOTE,
    )
    initial_data = copy.deepcopy(recorder.initial_data())

    def search(
        assignment: dict[str, bool],
        assignment_order: list[dict[str, Any]],
        current_tree_id: str,
        current_path: list[str],
    ) -> bool:
        recorder.set_current_state(
            assignment=assignment,
            assignment_order=assignment_order,
            active_tree_node=current_tree_id,
            active_tree_path=current_path,
            status="searching",
        )

        while True:
            evaluated = evaluate_formula(problem.clauses, assignment)
            contradicted = next((clause for clause in evaluated if clause.status == "contradicted"), None)
            if contradicted is not None:
                recorder.stats["contradictions"] += 1
                recorder.set_status(current_tree_id, "contradiction")
                recorder.set_current_state(
                    assignment=assignment,
                    assignment_order=assignment_order,
                    active_tree_node=current_tree_id,
                    active_tree_path=current_path,
                    status="contradiction",
                )
                recorder.record(
                    event_type="contradiction",
                    label=f"Contradiction in clause C{contradicted.index + 1}",
                    annotation=(
                        f"Clause {contradicted.text} is false under the current assignment, "
                        "so this branch cannot succeed."
                    ),
                    teaching_note=(
                        "A contradiction ends only the current branch. DPLL still has to check "
                        "other unexplored decisions before declaring the whole formula unsatisfiable."
                    ),
                )
                return False

            if all(clause.status == "satisfied" for clause in evaluated):
                recorder.result = _result_label(problem.mode, satisfiable=True)
                recorder.final_tree_path = list(current_path)
                recorder.set_status(current_tree_id, "solution")
                recorder.set_current_state(
                    assignment=assignment,
                    assignment_order=assignment_order,
                    active_tree_node=current_tree_id,
                    active_tree_path=current_path,
                    status=recorder.result,
                )
                recorder.record(
                    event_type="solution_found",
                    label=_solution_label(problem.mode, satisfiable=True),
                    annotation=_solution_annotation(problem.mode, satisfiable=True, assignment=assignment),
                    teaching_note=(
                        "A satisfiable branch gives DPLL a complete witness. "
                        "In entailment mode, satisfiable here means KB and not query still has a model."
                    ),
                )
                return True

            unit_clause = first_unit_clause(evaluated) if unit_propagation else None
            if unit_clause is not None and unit_clause.unit_literal is not None:
                current_tree_id, current_path, assignment, assignment_order = _append_assignment_node(
                    recorder,
                    parent_id=current_tree_id,
                    current_path=current_path,
                    assignment=assignment,
                    assignment_order=assignment_order,
                    literal=unit_clause.unit_literal,
                    reason="unit",
                    clause_index=unit_clause.index,
                )
                continue

            pure_literal = first_pure_literal(problem.clauses, assignment, variable_order) if pure_literals else None
            if pure_literal is not None:
                current_tree_id, current_path, assignment, assignment_order = _append_assignment_node(
                    recorder,
                    parent_id=current_tree_id,
                    current_path=current_path,
                    assignment=assignment,
                    assignment_order=assignment_order,
                    literal=pure_literal,
                    reason="pure",
                    clause_index=None,
                )
                continue

            break

        next_variable = choose_branch_variable(problem.clauses, assignment, variable_order)
        if next_variable is None:
            recorder.result = _result_label(problem.mode, satisfiable=False)
            recorder.set_status(current_tree_id, "contradiction")
            return False

        recorder.set_current_state(
            assignment=assignment,
            assignment_order=assignment_order,
            active_tree_node=current_tree_id,
            active_tree_path=current_path,
            status="branching",
        )
        recorder.record(
            event_type="choose_variable",
            label=f"Choose branching variable {next_variable}",
            annotation=(
                f"No forced move remains, so DPLL branches on {next_variable}. "
                "The deterministic variable order keeps classroom replays stable."
            ),
            teaching_note="Branching is the point where DPLL explores alternative assignments as a search tree.",
        )

        recorder.set_status(current_tree_id, "branched")
        for branch_value in (True, False):
            literal = next_variable if branch_value else f"~{next_variable}"
            child_tree_id, child_path, child_assignment, child_assignment_order = _append_assignment_node(
                recorder,
                parent_id=current_tree_id,
                current_path=current_path,
                assignment=assignment,
                assignment_order=assignment_order,
                literal=literal,
                reason="decision",
                clause_index=None,
            )
            if search(child_assignment, child_assignment_order, child_tree_id, child_path):
                return True
            recorder.stats["backtracks"] += 1
            recorder.set_current_state(
                assignment=assignment,
                assignment_order=assignment_order,
                active_tree_node=current_tree_id,
                active_tree_path=current_path,
                status="backtracking",
            )
            recorder.record(
                event_type="backtrack",
                label="Backtrack",
                annotation=(
                    f"The branch {literal.replace('~', '')} = {'true' if branch_value else 'false'} failed, "
                    "so DPLL returns to the previous decision point."
                ),
                teaching_note="Backtracking keeps the tree history visible even though the active assignment retracts.",
            )

        recorder.set_status(current_tree_id, "backtracked")
        return False

    satisfiable = search({}, [], root_id, [root_id])
    recorder.finished = True
    recorder.result = _result_label(problem.mode, satisfiable=satisfiable)
    recorder.set_current_state(
        assignment=recorder.assignment,
        assignment_order=recorder.assignment_order,
        active_tree_node=recorder.active_tree_node,
        active_tree_path=recorder.active_tree_path,
        status=recorder.result,
    )
    recorder.record(
        event_type="finished",
        label=_solution_label(problem.mode, satisfiable=satisfiable),
        annotation=_solution_annotation(problem.mode, satisfiable=satisfiable, assignment=recorder.assignment),
        teaching_note=(
            "The final result depends on the whole search. "
            "One contradiction is only a failed branch, not automatically a proof of unsatisfiability."
        ),
    )
    return SolverResult(
        trace_id=recorder.trace_id,
        problem=problem,
        raw_steps=recorder.raw_steps,
        initial_data=initial_data,
        status=recorder.result,
        assignment=copy.deepcopy(recorder.assignment),
    )


def choose_branch_variable(
    clauses: list[list[str]],
    assignment: dict[str, bool],
    variable_order: VariableOrder,
) -> str | None:
    remaining = [variable for variable in variables_in_appearance_order(clauses) if variable not in assignment]
    if not remaining:
        return None
    if variable_order == "appearance":
        return remaining[0]
    return sorted(remaining)[0]


def variables_in_appearance_order(clauses: list[list[str]]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for clause in clauses:
        for literal in clause:
            variable = literal[1:] if literal.startswith("~") else literal
            if variable in seen:
                continue
            seen.add(variable)
            ordered.append(variable)
    return ordered


def first_pure_literal(
    clauses: list[list[str]],
    assignment: dict[str, bool],
    variable_order: VariableOrder,
) -> str | None:
    occurrences: dict[str, set[bool]] = {}
    for clause in clauses:
        clause_values = [evaluate_literal(literal, assignment) for literal in clause]
        if any(value is True for value in clause_values):
            continue
        for literal in clause:
            variable = literal[1:] if literal.startswith("~") else literal
            if variable in assignment:
                continue
            occurrences.setdefault(variable, set()).add(not literal.startswith("~"))
    if not occurrences:
        return None

    candidates = [
        variable
        for variable, polarities in occurrences.items()
        if len(polarities) == 1
    ]
    if not candidates:
        return None

    ordered = candidates if variable_order == "appearance" else sorted(candidates)
    variable = ordered[0]
    polarity = next(iter(occurrences[variable]))
    return variable if polarity else f"~{variable}"


def first_unit_clause(evaluated: list[ClauseEvaluation]) -> ClauseEvaluation | None:
    for clause in evaluated:
        if clause.status == "unit":
            return clause
    return None


def evaluate_formula(clauses: list[list[str]], assignment: dict[str, bool]) -> list[ClauseEvaluation]:
    evaluations: list[ClauseEvaluation] = []
    for index, clause in enumerate(clauses):
        literal_views: list[dict[str, Any]] = []
        unassigned_literals: list[str] = []
        has_true = False
        for literal in clause:
            value = evaluate_literal(literal, assignment)
            if value is True:
                has_true = True
                value_label = "true"
            elif value is False:
                value_label = "false"
            else:
                value_label = "unassigned"
                unassigned_literals.append(literal)
            literal_views.append(
                {
                    "text": format_literal(literal),
                    "raw": literal,
                    "state": value_label,
                }
            )

        if has_true:
            status = "satisfied"
            unit_literal = None
        elif not unassigned_literals:
            status = "contradicted"
            unit_literal = None
        elif len(unassigned_literals) == 1:
            status = "unit"
            unit_literal = unassigned_literals[0]
        else:
            status = "unresolved"
            unit_literal = None
        evaluations.append(
            ClauseEvaluation(
                index=index,
                status=status,
                literals=literal_views,
                unit_literal=unit_literal,
                text=format_clause(clause),
            )
        )
    return evaluations


def evaluate_literal(literal: str, assignment: dict[str, bool]) -> bool | None:
    variable = literal[1:] if literal.startswith("~") else literal
    if variable not in assignment:
        return None
    value = assignment[variable]
    return not value if literal.startswith("~") else value


def parse_literal(literal: str) -> tuple[str, bool]:
    return (literal[1:], False) if literal.startswith("~") else (literal, True)


def format_literal(literal: str) -> str:
    return literal.replace("~", "¬")


def format_clause(clause: list[str]) -> str:
    return "(" + " ∨ ".join(format_literal(literal) for literal in clause) + ")"


def _append_assignment_node(
    recorder: _TraceRecorder,
    *,
    parent_id: str,
    current_path: list[str],
    assignment: dict[str, bool],
    assignment_order: list[dict[str, Any]],
    literal: str,
    reason: str,
    clause_index: int | None,
) -> tuple[str, list[str], dict[str, bool], list[dict[str, Any]]]:
    variable, value = parse_literal(literal)
    new_assignment = dict(assignment)
    new_assignment[variable] = value
    new_entry = {
        "variable": variable,
        "value": value,
        "reason": reason,
        "clause_index": clause_index,
    }
    new_order = copy.deepcopy(assignment_order) + [new_entry]
    label = f"{variable} = {'T' if value else 'F'}"
    assignment_text = ", ".join(
        f"{entry['variable']} = {'T' if entry['value'] else 'F'}" for entry in new_order
    )
    tree_id = recorder.create_tree_node(
        graph_node=label,
        assignment_text=assignment_text,
        parent=parent_id,
        depth=len(new_order),
        status="forced" if reason in {"unit", "pure"} else "active",
        reason=reason,
    )
    recorder.set_current_state(
        assignment=new_assignment,
        assignment_order=new_order,
        active_tree_node=tree_id,
        active_tree_path=current_path + [tree_id],
        status="propagating" if reason in {"unit", "pure"} else "branching",
    )
    if reason == "decision":
        recorder.stats["decisions"] += 1
        recorder.record(
            event_type="assign",
            label=f"Assign {label}",
            annotation=f"Choose {label} as the next branch in the DPLL search tree.",
            teaching_note="A decision assignment is a real branch point because DPLL could later try the opposite value.",
        )
    elif reason == "unit":
        recorder.stats["forced_assignments"] += 1
        recorder.record(
            event_type="assign",
            label=f"Force {label}",
            annotation=(
                f"Clause C{clause_index + 1} became unit, so {label} is forced by unit propagation."
            ),
            teaching_note="Unit propagation is not a guess. Once every other literal in a clause is false, the last one must be true.",
        )
    else:
        recorder.stats["forced_assignments"] += 1
        recorder.record(
            event_type="assign",
            label=f"Use pure literal {label}",
            annotation=(
                f"{variable} appears with only one polarity in the unresolved clauses, "
                f"so DPLL can set {label} without risking a contradiction."
            ),
            teaching_note="Pure literal elimination is optional, but it can shrink the search tree before any branching happens.",
        )
    return tree_id, current_path + [tree_id], new_assignment, new_order


def _assignment_items(assignment_order: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "variable": entry["variable"],
            "value": entry["value"],
            "reason": entry["reason"],
            "clause_index": entry["clause_index"],
            "text": f"{entry['variable']} = {'T' if entry['value'] else 'F'}",
        }
        for entry in assignment_order
    ]


def _result_label(mode: str, *, satisfiable: bool) -> str:
    if mode == "sat":
        return "satisfiable" if satisfiable else "unsatisfiable"
    return "not entailed" if satisfiable else "entailed"


def _solution_label(mode: str, *, satisfiable: bool) -> str:
    if mode == "sat":
        return "Satisfying assignment found" if satisfiable else "Formula is unsatisfiable"
    return "Query is not entailed" if satisfiable else "Query is entailed"


def _solution_annotation(mode: str, *, satisfiable: bool, assignment: dict[str, bool]) -> str:
    if mode == "sat":
        if satisfiable:
            return (
                "All clauses are satisfied by the current assignment: "
                + ", ".join(f"{variable} = {'true' if value else 'false'}" for variable, value in assignment.items())
                + "."
            )
        return "Every branch leads to a contradiction, so no assignment satisfies the CNF."
    if satisfiable:
        return (
            "KB and not query still has a satisfying assignment, so the query does not follow from the knowledge base."
        )
    return "KB and not query is unsatisfiable, so the query is entailed by the knowledge base."
