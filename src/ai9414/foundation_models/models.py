"""Domain models for the foundation-model teaching explorers."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model

TokeniserMode = Literal["character", "word", "bpe"]
DecodingRule = Literal["greedy", "sampling", "top_k", "top_p"]


class TokenisationCorpus(AI9414Model):
    name: str
    title: str
    subtitle: str
    texts: list[str]

    @field_validator("texts")
    @classmethod
    def validate_texts(cls, value: list[str]) -> list[str]:
        texts = [str(text) for text in value if str(text).strip()]
        if not texts:
            raise ValueError(
                "A tokenisation corpus must include at least one non-empty text."
            )
        return texts


class TokenisationExample(AI9414Model):
    name: str
    title: str
    subtitle: str
    text: str
    default_corpus: str = "office_messages"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        text = str(value)
        if not text.strip():
            raise ValueError("Example text must not be empty.")
        return text


class TokenisationConfigData(AI9414Model):
    text: str
    title: str = "Instructor-supplied tokenisation example"
    subtitle: str = "Custom text loaded from a configuration file."
    corpus: str = "office_messages"

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        text = str(value)
        if not text.strip():
            raise ValueError("Configuration text must not be empty.")
        return text


class TokenisationConfigModel(BaseConfigModel):
    app_type: str = "foundation_models"
    data: TokenisationConfigData

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "playback_speed",
            "tokeniser_mode",
            "corpus",
            "num_merges",
            "context_window",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(unknown)}.")
        return value


class TokenSequenceSummary(AI9414Model):
    mode: TokeniserMode
    label: str
    tokens: list[str]
    token_count: int
    average_token_length: float


class TokenisationProblem(AI9414Model):
    title: str
    subtitle: str
    text: str
    corpus_name: str
    corpus_texts: list[str]
    tokeniser_mode: TokeniserMode = "bpe"
    num_merges: int = 12
    context_window: int = 64

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        text = str(value)
        if not text.strip():
            raise ValueError("Problem text must not be empty.")
        return text

    @field_validator("corpus_texts")
    @classmethod
    def validate_corpus_texts(cls, value: list[str]) -> list[str]:
        texts = [str(text) for text in value if str(text).strip()]
        if not texts:
            raise ValueError("At least one corpus text is required.")
        return texts

    @model_validator(mode="after")
    def validate_numbers(self) -> "TokenisationProblem":
        if self.num_merges < 0:
            raise ValueError("num_merges must be non-negative.")
        if self.context_window <= 0:
            raise ValueError("context_window must be positive.")
        return self


class DecodingCandidate(AI9414Model):
    """One candidate next token with a precomputed model logit."""

    token: str
    logit: float

    @field_validator("token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        token = str(value)
        if not token:
            raise ValueError("A decoding candidate token must not be empty.")
        return token

    @field_validator("logit")
    @classmethod
    def validate_logit(cls, value: float) -> float:
        logit = float(value)
        if not math.isfinite(logit):
            raise ValueError("Candidate logits must be finite.")
        return logit


class DecodingOptions(AI9414Model):
    """Validated controls for one next-token decoding decision."""

    playback_speed: float = 1.0
    selection_rule: DecodingRule = "top_p"
    temperature: float = 1.0
    top_k: int = 3
    top_p: float = 0.7
    seed: int = 9414

    @field_validator("playback_speed")
    @classmethod
    def validate_playback_speed(cls, value: float) -> float:
        speed = float(value)
        if not math.isfinite(speed) or not 0.5 <= speed <= 5.0:
            raise ValueError("playback_speed must be between 0.5 and 5.0.")
        return speed

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, value: float) -> float:
        temperature = float(value)
        if not math.isfinite(temperature) or not 0.05 <= temperature <= 5.0:
            raise ValueError("temperature must be between 0.05 and 5.0.")
        return temperature

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, value: int) -> int:
        top_k = int(value)
        if top_k < 1:
            raise ValueError("top_k must be positive.")
        return top_k

    @field_validator("top_p")
    @classmethod
    def validate_top_p(cls, value: float) -> float:
        top_p = float(value)
        if not math.isfinite(top_p) or not 0.0 < top_p <= 1.0:
            raise ValueError("top_p must be greater than zero and at most one.")
        return top_p

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, value: int) -> int:
        seed = int(value)
        if not 0 <= seed <= 2**32 - 1:
            raise ValueError("seed must be between 0 and 4294967295.")
        return seed


class DecodingExample(AI9414Model):
    """A curated context and fixed next-token score distribution."""

    name: str
    title: str
    subtitle: str
    context_tokens: list[str]
    candidates: list[DecodingCandidate]
    default_options: DecodingOptions = Field(default_factory=DecodingOptions)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("context_tokens")
    @classmethod
    def validate_context_tokens(cls, value: list[str]) -> list[str]:
        tokens = [str(token) for token in value]
        if not tokens or any(not token for token in tokens):
            raise ValueError("A decoding example requires non-empty context tokens.")
        return tokens

    @field_validator("candidates")
    @classmethod
    def validate_candidates(
        cls, value: list[DecodingCandidate]
    ) -> list[DecodingCandidate]:
        if len(value) < 2:
            raise ValueError("A decoding example requires at least two candidates.")
        tokens = [candidate.token for candidate in value]
        if len(tokens) != len(set(tokens)):
            raise ValueError("Decoding candidate tokens must be unique.")
        return value

    @model_validator(mode="after")
    def validate_default_top_k(self) -> "DecodingExample":
        if self.default_options.top_k > len(self.candidates):
            raise ValueError("The default top_k cannot exceed the candidate count.")
        return self


class DecodingProblem(AI9414Model):
    """Complete validated input to a deterministic decoding replay."""

    title: str
    subtitle: str
    context_tokens: list[str]
    candidates: list[DecodingCandidate]
    options: DecodingOptions = Field(default_factory=DecodingOptions)

    @field_validator("context_tokens")
    @classmethod
    def validate_problem_context(cls, value: list[str]) -> list[str]:
        tokens = [str(token) for token in value]
        if not tokens or any(not token for token in tokens):
            raise ValueError("A decoding problem requires non-empty context tokens.")
        return tokens

    @field_validator("candidates")
    @classmethod
    def validate_problem_candidates(
        cls, value: list[DecodingCandidate]
    ) -> list[DecodingCandidate]:
        if len(value) < 2:
            raise ValueError("A decoding problem requires at least two candidates.")
        tokens = [candidate.token for candidate in value]
        if len(tokens) != len(set(tokens)):
            raise ValueError("Decoding candidate tokens must be unique.")
        return value

    @model_validator(mode="after")
    def validate_top_k_for_candidates(self) -> "DecodingProblem":
        if self.options.top_k > len(self.candidates):
            raise ValueError("top_k cannot exceed the candidate count.")
        return self


class DecodingConfigData(AI9414Model):
    title: str = "Instructor-supplied decoding example"
    subtitle: str = "Precomputed candidate logits loaded from a configuration file."
    context_tokens: list[str]
    candidates: list[DecodingCandidate]

    @field_validator("context_tokens")
    @classmethod
    def validate_config_context(cls, value: list[str]) -> list[str]:
        tokens = [str(token) for token in value]
        if not tokens or any(not token for token in tokens):
            raise ValueError(
                "A decoding configuration requires non-empty context tokens."
            )
        return tokens

    @field_validator("candidates")
    @classmethod
    def validate_config_candidates(
        cls, value: list[DecodingCandidate]
    ) -> list[DecodingCandidate]:
        if len(value) < 2:
            raise ValueError(
                "A decoding configuration requires at least two candidates."
            )
        tokens = [candidate.token for candidate in value]
        if len(tokens) != len(set(tokens)):
            raise ValueError("Decoding candidate tokens must be unique.")
        return value


class DecodingConfigModel(BaseConfigModel):
    app_type: str = "foundation_models"
    data: DecodingConfigData

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "playback_speed",
            "selection_rule",
            "temperature",
            "top_k",
            "top_p",
            "seed",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(unknown)}.")
        return value
