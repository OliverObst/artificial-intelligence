"""Curated examples for the resolution/refutation demo."""

from __future__ import annotations

from ai9414.resolution.models import ResolutionExample, ResolutionProblem, ResolutionProofStep


def step(left: int, right: int, pivot: str, note: str = "") -> ResolutionProofStep:
    return ResolutionProofStep(left=left, right=right, pivot=pivot, note=note)


def build_examples() -> dict[str, ResolutionExample]:
    examples = [
        ResolutionExample(
            name="modus_ponens_refutation",
            title="Modus Ponens as Refutation",
            subtitle="Show that A -> B and A entail B by deriving the empty clause from KB and not B.",
            problem=ResolutionProblem(
                title="Modus Ponens as Refutation",
                subtitle="The negated query closes the proof.",
                clauses=[["~A", "B"], ["A"], ["~B"]],
                steps=[
                    step(1, 2, "A", "Resolve the implication clause with the fact A."),
                    step(4, 3, "B", "Resolve B with the negated query."),
                ],
                query="B",
                entailment_target="KB and not B",
                original_input=["A -> B", "A", "query: B"],
            ),
        ),
        ResolutionExample(
            name="chain_refutation",
            title="Three-Step Entailment Chain",
            subtitle="A compact proof that A -> B, B -> C, and A entail C.",
            problem=ResolutionProblem(
                title="Three-Step Entailment Chain",
                subtitle="Each resolvent becomes a reusable derived clause.",
                clauses=[["~A", "B"], ["~B", "C"], ["A"], ["~C"]],
                steps=[
                    step(1, 3, "A", "Derive B from A and A -> B."),
                    step(2, 5, "B", "Derive C from B and B -> C."),
                    step(4, 6, "C", "C contradicts the negated query not C."),
                ],
                query="C",
                entailment_target="KB and not C",
                original_input=["A -> B", "B -> C", "A", "query: C"],
            ),
        ),
        ResolutionExample(
            name="wumpus_no_breeze",
            title="Wumpus: No Breeze Means Safe",
            subtitle="A small Wumpus proof that no breeze at [1,1] entails no pit at [1,2].",
            problem=ResolutionProblem(
                title="Wumpus: No Breeze Means Safe",
                subtitle="The proof refutes the assumption that P_12 is true.",
                clauses=[
                    ["~B_11", "P_12", "P_21"],
                    ["B_11", "~P_12"],
                    ["B_11", "~P_21"],
                    ["~B_11"],
                    ["P_12"],
                ],
                steps=[
                    step(2, 5, "P_12", "If there were a pit at [1,2], the breeze rule forces B_11."),
                    step(4, 6, "B_11", "But the percept says there is no breeze at [1,1]."),
                ],
                query="not P_12",
                entailment_target="KB and P_12",
                original_input=[
                    "B_11 iff (P_12 or P_21)",
                    "not B_11",
                    "query: not P_12",
                ],
                visualisation={
                    "kind": "wumpus",
                    "width": 2,
                    "height": 2,
                    "agent": [1, 1],
                    "percepts": [{"cell": [1, 1], "kind": "clear", "label": "no breeze"}],
                    "entailed_safe": [[1, 2]],
                    "candidate_pits": [[1, 2], [2, 1]],
                },
            ),
        ),
        ResolutionExample(
            name="wumpus_forced_pit",
            title="Wumpus: A Forced Pit",
            subtitle="A larger refutation showing that the pit at [3,1] is forced by the breeze pattern.",
            problem=ResolutionProblem(
                title="Wumpus: A Forced Pit",
                subtitle="Assume not P_31, then resolve until the empty clause appears.",
                clauses=[
                    ["~B_11", "P_12", "P_21"],
                    ["B_11", "~P_12"],
                    ["B_11", "~P_21"],
                    ["~B_12", "P_11", "P_13", "P_22"],
                    ["B_12", "~P_11"],
                    ["B_12", "~P_22"],
                    ["B_12", "~P_13"],
                    ["~B_21", "P_11", "P_22", "P_31"],
                    ["B_21", "~P_11"],
                    ["B_21", "~P_22"],
                    ["B_21", "~P_31"],
                    ["~B_11"],
                    ["~B_12"],
                    ["B_21"],
                    ["~P_31"],
                ],
                steps=[
                    step(13, 5, "B_12", "No breeze at [1,2] rules out P_11."),
                    step(13, 6, "B_12", "The same percept rules out P_22."),
                    step(8, 14, "B_21", "The breeze at [2,1] leaves P_11, P_22, or P_31."),
                    step(18, 16, "P_11", "Remove P_11 from the disjunction."),
                    step(19, 17, "P_22", "Remove P_22 from the disjunction."),
                    step(20, 15, "P_31", "P_31 contradicts the negated query not P_31."),
                ],
                query="P_31",
                entailment_target="KB and not P_31",
                original_input=[
                    "local breeze rules for [1,1], [1,2], [2,1]",
                    "not B_11",
                    "not B_12",
                    "B_21",
                    "query: P_31",
                ],
                visualisation={
                    "kind": "wumpus",
                    "width": 3,
                    "height": 3,
                    "agent": [1, 1],
                    "percepts": [
                        {"cell": [1, 1], "kind": "clear", "label": "no breeze"},
                        {"cell": [1, 2], "kind": "clear", "label": "no breeze"},
                        {"cell": [2, 1], "kind": "breeze", "label": "breeze"},
                    ],
                    "entailed_pits": [[3, 1]],
                    "entailed_safe": [[1, 1], [1, 2], [2, 2]],
                    "candidate_pits": [[1, 3], [2, 2], [3, 1]],
                },
            ),
        ),
    ]
    return {example.name: example for example in examples}
