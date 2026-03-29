"""Small propositional parser and CNF conversion helpers for the DPLL demo."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

from ai9414.core.errors import AI9414Error

TokenKind = Literal["VAR", "NOT", "AND", "OR", "IMPLIES", "LPAREN", "RPAREN"]

TOKEN_PATTERN = re.compile(
    r"""
    (?P<SPACE>\s+)
    |(?P<IMPLIES>->)
    |(?P<LPAREN>\()
    |(?P<RPAREN>\))
    |(?P<NOT>~|!|\bnot\b)
    |(?P<AND>&|\^|\band\b)
    |(?P<OR>\||\bv\b|\bor\b|∨)
    |(?P<VAR>[A-Za-z][A-Za-z0-9_]*)
    """,
    re.IGNORECASE | re.VERBOSE,
)


@dataclass(frozen=True)
class Variable:
    name: str


@dataclass(frozen=True)
class Not:
    child: "Expr"


@dataclass(frozen=True)
class And:
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class Or:
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class Implies:
    left: "Expr"
    right: "Expr"


Expr = Variable | Not | And | Or | Implies


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: str


def parse_formula(text: str) -> Expr:
    """Parse a small propositional formula."""

    tokens = _tokenise(text)
    parser = _FormulaParser(tokens, text)
    expr = parser.parse_implication()
    if parser.has_more():
        token = parser.peek()
        raise AI9414Error(
            code="invalid_logic_formula",
            message=f"Unexpected token '{token.value}' in formula '{text}'.",
        )
    return expr


def formula_to_cnf_clauses(text: str) -> list[list[str]]:
    """Parse a propositional formula string and return CNF clauses."""

    expr = parse_formula(text)
    return expr_to_cnf_clauses(expr)


def expr_to_cnf_clauses(expr: Expr) -> list[list[str]]:
    """Convert an expression tree into CNF clauses using a small teaching-oriented pipeline."""

    without_implication = _eliminate_implications(expr)
    nnf = _to_nnf(without_implication)
    raw_clauses = _cnf_from_nnf(nnf)
    return _normalise_clauses(raw_clauses)


def negate_formula_to_cnf_clauses(text: str) -> list[list[str]]:
    """Return CNF clauses for the negation of a formula."""

    expr = parse_formula(text)
    return expr_to_cnf_clauses(Not(expr))


def extract_variables_from_clauses(clauses: list[list[str]]) -> list[str]:
    """Return sorted variables appearing in the clause set."""

    variables = {literal[1:] if literal.startswith("~") else literal for clause in clauses for literal in clause}
    return sorted(variables)


def _tokenise(text: str) -> list[Token]:
    tokens: list[Token] = []
    position = 0
    while position < len(text):
        match = TOKEN_PATTERN.match(text, position)
        if match is None:
            snippet = text[position : position + 12]
            raise AI9414Error(
                code="invalid_logic_formula",
                message=f"Could not parse formula near '{snippet}' in '{text}'.",
            )
        position = match.end()
        kind = match.lastgroup
        if kind == "SPACE":
            continue
        assert kind is not None
        tokens.append(Token(kind=kind, value=match.group()))
    return tokens


class _FormulaParser:
    def __init__(self, tokens: list[Token], source: str) -> None:
        self.tokens = tokens
        self.source = source
        self.index = 0

    def has_more(self) -> bool:
        return self.index < len(self.tokens)

    def peek(self) -> Token:
        return self.tokens[self.index]

    def consume(self, expected: TokenKind | None = None) -> Token:
        if not self.has_more():
            raise AI9414Error(
                code="invalid_logic_formula",
                message=f"Unexpected end of formula '{self.source}'.",
            )
        token = self.tokens[self.index]
        if expected is not None and token.kind != expected:
            raise AI9414Error(
                code="invalid_logic_formula",
                message=(
                    f"Expected {expected.lower()} in formula '{self.source}', "
                    f"but found '{token.value}'."
                ),
            )
        self.index += 1
        return token

    def parse_implication(self) -> Expr:
        left = self.parse_or()
        if self.has_more() and self.peek().kind == "IMPLIES":
            self.consume("IMPLIES")
            right = self.parse_implication()
            return Implies(left, right)
        return left

    def parse_or(self) -> Expr:
        expr = self.parse_and()
        while self.has_more() and self.peek().kind == "OR":
            self.consume("OR")
            expr = Or(expr, self.parse_and())
        return expr

    def parse_and(self) -> Expr:
        expr = self.parse_not()
        while self.has_more() and self.peek().kind == "AND":
            self.consume("AND")
            expr = And(expr, self.parse_not())
        return expr

    def parse_not(self) -> Expr:
        if self.has_more() and self.peek().kind == "NOT":
            self.consume("NOT")
            return Not(self.parse_not())
        return self.parse_atom()

    def parse_atom(self) -> Expr:
        token = self.consume()
        if token.kind == "VAR":
            return Variable(token.value)
        if token.kind == "LPAREN":
            expr = self.parse_implication()
            self.consume("RPAREN")
            return expr
        raise AI9414Error(
            code="invalid_logic_formula",
            message=f"Unexpected token '{token.value}' in formula '{self.source}'.",
        )


def _eliminate_implications(expr: Expr) -> Expr:
    if isinstance(expr, Variable):
        return expr
    if isinstance(expr, Not):
        return Not(_eliminate_implications(expr.child))
    if isinstance(expr, And):
        return And(_eliminate_implications(expr.left), _eliminate_implications(expr.right))
    if isinstance(expr, Or):
        return Or(_eliminate_implications(expr.left), _eliminate_implications(expr.right))
    return Or(Not(_eliminate_implications(expr.left)), _eliminate_implications(expr.right))


def _to_nnf(expr: Expr) -> Expr:
    if isinstance(expr, Variable):
        return expr
    if isinstance(expr, And):
        return And(_to_nnf(expr.left), _to_nnf(expr.right))
    if isinstance(expr, Or):
        return Or(_to_nnf(expr.left), _to_nnf(expr.right))
    assert isinstance(expr, Not)
    child = expr.child
    if isinstance(child, Variable):
        return expr
    if isinstance(child, Not):
        return _to_nnf(child.child)
    if isinstance(child, And):
        return Or(_to_nnf(Not(child.left)), _to_nnf(Not(child.right)))
    if isinstance(child, Or):
        return And(_to_nnf(Not(child.left)), _to_nnf(Not(child.right)))
    raise AI9414Error(
        code="invalid_logic_formula",
        message="Implications should be removed before CNF conversion.",
    )


def _cnf_from_nnf(expr: Expr) -> list[list[str]]:
    if isinstance(expr, Variable):
        return [[expr.name]]
    if isinstance(expr, Not):
        assert isinstance(expr.child, Variable)
        return [[f"~{expr.child.name}"]]
    if isinstance(expr, And):
        return _cnf_from_nnf(expr.left) + _cnf_from_nnf(expr.right)
    assert isinstance(expr, Or)
    left = _cnf_from_nnf(expr.left)
    right = _cnf_from_nnf(expr.right)
    distributed: list[list[str]] = []
    for left_clause in left:
        for right_clause in right:
            distributed.append(left_clause + right_clause)
    return distributed


def _normalise_clauses(clauses: list[list[str]]) -> list[list[str]]:
    normalised: list[list[str]] = []
    for clause in clauses:
        seen: dict[str, bool] = {}
        tautology = False
        for literal in clause:
            variable = literal[1:] if literal.startswith("~") else literal
            is_positive = not literal.startswith("~")
            if variable in seen and seen[variable] != is_positive:
                tautology = True
                break
            seen[variable] = is_positive
        if tautology:
            continue
        ordered = [
            variable if is_positive else f"~{variable}"
            for variable, is_positive in sorted(seen.items(), key=lambda item: item[0])
        ]
        normalised.append(ordered)
    return normalised
