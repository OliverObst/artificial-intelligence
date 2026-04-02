"""Domain models for the foundation models tokenisation explorer."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from ai9414.core.config import BaseConfigModel
from ai9414.core.models import AI9414Model

TokeniserMode = Literal["character", "word", "bpe"]


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
            raise ValueError("A tokenisation corpus must include at least one non-empty text.")
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
        allowed = {"playback_speed", "tokeniser_mode", "corpus", "num_merges", "context_window"}
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
