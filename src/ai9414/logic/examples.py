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
        _build_wumpus_no_breeze_example(),
        _build_wumpus_forced_pit_example(),
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
    return _build_entailment_example(
        name="entailment_chain",
        title="Entailment chain",
        subtitle="Entailment is tested by checking whether KB and not query are unsatisfiable.",
        problem_subtitle="The knowledge base proves C once A implies B and B implies C are both available.",
        formulas=formulas,
        query=query,
        entailment_target="KB and not C",
        teaching_note="Entailment holds when KB and not query become unsatisfiable together.",
    )


def _build_wumpus_no_breeze_example() -> LogicExample:
    formulas = [
        "B_11 -> (P_12 or P_21)",
        "P_12 -> B_11",
        "P_21 -> B_11",
        "not B_11",
    ]
    query = "not P_12"
    return _build_entailment_example(
        name="wumpus_no_breeze",
        title="Wumpus no-breeze entailment",
        subtitle="A no-breeze percept rules out pits in adjacent squares.",
        problem_subtitle="The agent observes no breeze at [1,1], so [1,2] must not contain a pit.",
        formulas=formulas,
        query=query,
        entailment_target="KB and P_12",
        teaching_note=(
            "This mirrors the small Wumpus slide example: to prove not P_12, "
            "DPLL checks whether adding P_12 makes the knowledge base unsatisfiable."
        ),
        visualisation={
            "kind": "wumpus",
            "title": "No breeze at [1,1]",
            "width": 3,
            "height": 2,
            "agent": [1, 1],
            "percepts": [
                {"square": [1, 1], "label": "no breeze", "kind": "clear"},
            ],
            "candidates": [[1, 2], [2, 1]],
            "entailed_safe": [[1, 2]],
            "notes": [
                "[1,2] and [2,1] are the pit candidates adjacent to [1,1].",
                "No breeze at [1,1] rules out every adjacent pit.",
            ],
        },
    )


def _build_wumpus_forced_pit_example() -> LogicExample:
    formulas = [
        "B_11 -> (P_12 or P_21)",
        "P_12 -> B_11",
        "P_21 -> B_11",
        "B_12 -> (P_11 or P_22 or P_13)",
        "P_11 -> B_12",
        "P_22 -> B_12",
        "P_13 -> B_12",
        "B_21 -> (P_11 or P_22 or P_31)",
        "P_11 -> B_21",
        "P_22 -> B_21",
        "P_31 -> B_21",
        "not B_11",
        "not B_12",
        "B_21",
    ]
    query = "P_31"
    return _build_entailment_example(
        name="wumpus_forced_pit",
        title="Wumpus forced pit",
        subtitle="Several percepts combine to force one remaining pit location.",
        problem_subtitle=(
            "No breeze at [1,1] and [1,2] rules out nearby pits; a breeze at [2,1] "
            "then forces a pit at [3,1]."
        ),
        formulas=formulas,
        query=query,
        entailment_target="KB and not P_31",
        teaching_note=(
            "This larger Wumpus example shows DPLL using multiple percept rules: "
            "the negated query closes the last possible explanation for the breeze."
        ),
        visualisation={
            "kind": "wumpus",
            "title": "Forced pit from multiple percepts",
            "width": 3,
            "height": 3,
            "agent": [1, 1],
            "percepts": [
                {"square": [1, 1], "label": "no breeze", "kind": "clear"},
                {"square": [1, 2], "label": "no breeze", "kind": "clear"},
                {"square": [2, 1], "label": "breeze", "kind": "breeze"},
            ],
            "candidates": [[1, 1], [1, 2], [1, 3], [2, 1], [2, 2], [3, 1]],
            "entailed_safe": [[1, 1], [1, 2], [1, 3], [2, 1], [2, 2]],
            "entailed_pits": [[3, 1]],
            "notes": [
                "No breeze at [1,1] rules out [1,2] and [2,1].",
                "No breeze at [1,2] rules out [1,1], [2,2], and [1,3].",
                "The breeze at [2,1] then has only [3,1] left as an explanation.",
            ],
        },
    )


def _build_entailment_example(
    *,
    name: str,
    title: str,
    subtitle: str,
    problem_subtitle: str,
    formulas: list[str],
    query: str,
    entailment_target: str,
    teaching_note: str,
    visualisation: dict[str, object] | None = None,
) -> LogicExample:
    clauses = []
    for formula in formulas:
        clauses.extend(formula_to_cnf_clauses(formula))
    clauses.extend(negate_formula_to_cnf_clauses(query))
    return LogicExample(
        name=name,
        title=title,
        subtitle=subtitle,
        problem=LogicProblem(
            mode="entailment",
            title=title,
            subtitle=problem_subtitle,
            clauses=clauses,
            kb_formulas=formulas,
            query=query,
            entailment_target=entailment_target,
            original_input=formulas + [f"query: {query}"],
            visualisation=visualisation or {},
        ),
        metadata={"teaching_note": teaching_note},
    )
