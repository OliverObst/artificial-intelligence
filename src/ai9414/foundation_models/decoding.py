"""Pure probability operations used by the decoding explorer."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence


def apply_temperature(logits: Sequence[float], temperature: float) -> list[float]:
    """Scale finite logits by a positive temperature."""

    values = _finite_values(logits, label="logits")
    temperature = float(temperature)
    if not math.isfinite(temperature) or temperature <= 0.0:
        raise ValueError("temperature must be finite and positive.")
    return [value / temperature for value in values]


def softmax(logits: Sequence[float]) -> list[float]:
    """Return a numerically stable softmax distribution."""

    values = _finite_values(logits, label="logits")
    offset = max(values)
    exponentials = [math.exp(value - offset) for value in values]
    total = math.fsum(exponentials)
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("softmax could not form a finite positive total.")
    return [value / total for value in exponentials]


def greedy_select(probabilities: Sequence[float]) -> int:
    """Return the first index with maximal probability."""

    values = _probability_values(probabilities)
    return max(range(len(values)), key=values.__getitem__)


def top_k_filter(probabilities: Sequence[float], k: int) -> list[float]:
    """Keep the `k` highest-probability entries without renormalising."""

    values = _probability_values(probabilities)
    if isinstance(k, bool) or int(k) != k:
        raise ValueError("k must be an integer.")
    k = int(k)
    if not 1 <= k <= len(values):
        raise ValueError("k must be positive and cannot exceed the candidate count.")
    retained = set(_ranked_indices(values)[:k])
    return [value if index in retained else 0.0 for index, value in enumerate(values)]


def top_p_filter(probabilities: Sequence[float], p: float) -> list[float]:
    """Keep the smallest ranked prefix whose normalised mass reaches `p`."""

    values = _probability_values(probabilities)
    p = float(p)
    if not math.isfinite(p) or not 0.0 < p <= 1.0:
        raise ValueError("p must be greater than zero and at most one.")

    normalised = renormalise(values)
    retained: set[int] = set()
    cumulative = 0.0
    for index in _ranked_indices(normalised):
        retained.add(index)
        cumulative += normalised[index]
        if cumulative >= p:
            break
    return [value if index in retained else 0.0 for index, value in enumerate(values)]


def renormalise(probabilities: Sequence[float]) -> list[float]:
    """Scale non-negative weights to a probability distribution."""

    values = _probability_values(probabilities)
    total = math.fsum(values)
    if total <= 0.0:
        raise ValueError("At least one probability must be positive.")
    return [value / total for value in values]


def seeded_random_draw(seed: int) -> float:
    """Return the reproducible unit-interval draw used by seeded sampling."""

    if isinstance(seed, bool) or int(seed) != seed:
        raise ValueError("seed must be an integer.")
    seed = int(seed)
    if not 0 <= seed <= 2**32 - 1:
        raise ValueError("seed must be between 0 and 4294967295.")
    return random.Random(seed).random()


def sample_from_draw(probabilities: Sequence[float], draw: float) -> int:
    """Select the interval containing a supplied draw in `[0, 1)`."""

    distribution = renormalise(probabilities)
    draw = float(draw)
    if not math.isfinite(draw) or not 0.0 <= draw < 1.0:
        raise ValueError("draw must be finite and lie in [0, 1).")

    cumulative = 0.0
    last_positive = 0
    for index, probability in enumerate(distribution):
        if probability > 0.0:
            last_positive = index
        cumulative += probability
        if draw < cumulative:
            return index
    return last_positive


def seeded_sample(probabilities: Sequence[float], seed: int) -> int:
    """Select one index reproducibly from non-negative weights."""

    return sample_from_draw(probabilities, seeded_random_draw(seed))


def _finite_values(values: Sequence[float], *, label: str) -> list[float]:
    result = [float(value) for value in values]
    if not result:
        raise ValueError(f"{label} must not be empty.")
    if any(not math.isfinite(value) for value in result):
        raise ValueError(f"{label} must contain only finite values.")
    return result


def _probability_values(probabilities: Sequence[float]) -> list[float]:
    values = _finite_values(probabilities, label="probabilities")
    if any(value < 0.0 for value in values):
        raise ValueError("probabilities must be non-negative.")
    if not any(value > 0.0 for value in values):
        raise ValueError("At least one probability must be positive.")
    return values


def _ranked_indices(probabilities: Sequence[float]) -> list[int]:
    return sorted(
        range(len(probabilities)), key=lambda index: (-probabilities[index], index)
    )
