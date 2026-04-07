"""Curated DPLL examples for teaching propositional logic."""

from __future__ import annotations

from ai9414.logic.models import LogicExample, LogicProblem
from ai9414.logic.parser import formula_to_cnf_clauses, negate_formula_to_cnf_clauses


def build_examples() -> dict[str, LogicExample]:
    examples: list[LogicExample] = [
        LogicExample(
            name="simple_sat",
            title="Simple branching",
            subtitle=(
                "A small satisfiable CNF where one decision quickly leads to a satisfying assignment."
            ),
            problem=LogicProblem(
                mode="sat",
                title="Simple branching",
                subtitle="DPLL branches once, then finishes through forced assignments.",
                clauses=[["A", "B"], ["~A", "C"], ["~B", "C"]],
                original_input=["(A or B)", "(not A or C)", "(not B or C)"],
            ),
            metadata={"teaching_note": "The compact clause list makes the branching pattern easy to follow."},
        ),
        LogicExample(
            name="tiny_contradiction",
            title="Immediate contradiction",
            subtitle="The smallest unsatisfiable CNF shows what a contradicted branch looks like.",
            problem=LogicProblem(
                mode="sat",
                title="Immediate contradiction",
                subtitle="A single variable is forced to be both true and false.",
                clauses=[["A"], ["~A"]],
                original_input=["(A)", "(not A)"],
            ),
        ),
        LogicExample(
            name="unit_chain",
            title="Unit propagation chain",
            subtitle="A short chain of unit clauses makes every later assignment forced.",
            problem=LogicProblem(
                mode="sat",
                title="Unit propagation chain",
                subtitle="Each new unit clause forces the next literal in the chain.",
                clauses=[["A"], ["~A", "B"], ["~B", "C"]],
                original_input=["(A)", "(not A or B)", "(not B or C)"],
            ),
        ),
        LogicExample(
            name="unsat_branching",
            title="Unsatisfiable after branching",
            subtitle="A symmetric CNF where both decision branches fail and DPLL must backtrack.",
            problem=LogicProblem(
                mode="sat",
                title="Unsatisfiable after branching",
                subtitle="Both branches fail, so the full backtracking pattern is visible.",
                clauses=[["A", "B"], ["~A", "B"], ["A", "~B"], ["~A", "~B"]],
                original_input=["(A or B)", "(not A or B)", "(A or not B)", "(not A or not B)"],
            ),
        ),
        LogicExample(
            name="constraint_model",
            title="Small constraint model",
            subtitle="A compact propositional model of small logical constraints.",
            problem=LogicProblem(
                mode="sat",
                title="Small constraint model",
                subtitle="Exactly one of A, B, and C is true, with a small dependency chain.",
                clauses=[
                    ["A", "B", "C"],
                    ["~A", "~B"],
                    ["~A", "~C"],
                    ["~B", "~C"],
                    ["~A", "~B"],
                    ["~C", "A"],
                ],
                original_input=[
                    "(A or B or C)",
                    "(not A or not B)",
                    "(not A or not C)",
                    "(not B or not C)",
                    "(A implies not B)",
                    "(C implies A)",
                ],
            ),
        ),
        _build_entailment_chain_example(),
    ]
    return {example.name: example for example in examples}


def examples_for_mode(mode: str) -> dict[str, LogicExample]:
    return {
        name: example
        for name, example in build_examples().items()
        if example.problem.mode == mode
    }


def _build_entailment_chain_example() -> LogicExample:
    formulas = ["A -> B", "B -> C", "A"]
    query = "C"
    clauses = []
    for formula in formulas:
        clauses.extend(formula_to_cnf_clauses(formula))
    clauses.extend(negate_formula_to_cnf_clauses(query))
    return LogicExample(
        name="entailment_chain",
        title="Entailment chain",
        subtitle="Entailment is tested by checking whether KB and not query are unsatisfiable.",
        problem=LogicProblem(
            mode="entailment",
            title="Entailment chain",
            subtitle="The knowledge base proves C once A implies B and B implies C are both available.",
            clauses=clauses,
            kb_formulas=formulas,
            query=query,
            entailment_target="KB and not C",
            original_input=formulas + [f"query: {query}"],
        ),
        metadata={"teaching_note": "Entailment holds when KB and not query become unsatisfiable together."},
    )
