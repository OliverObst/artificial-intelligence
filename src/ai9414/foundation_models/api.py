"""Student-facing API for the foundation models tokenisation explorer."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from ai9414.core import BaseEducationalApp
from ai9414.core.errors import AI9414Error
from ai9414.foundation_models.examples import build_corpora, build_examples
from ai9414.foundation_models.models import (
    TokenisationConfigModel,
    TokenisationCorpus,
    TokenisationExample,
    TokenisationProblem,
)
from ai9414.foundation_models.trace import build_foundation_trace


class TokenisationExplorer(BaseEducationalApp):
    """Replay-first tokenisation explorer with curated examples and toy BPE learning."""

    def __init__(
        self,
        *,
        example: str | None = None,
        mode: str = "student",
        execution_mode: str = "precomputed",
    ) -> None:
        if execution_mode != "precomputed":
            raise AI9414Error(
                code="unsupported_action",
                message="TokenisationExplorer currently supports precomputed execution mode only.",
            )
        super().__init__(
            app_type="foundation_models",
            app_title="Foundation Models Demo - Tokenisation Explorer",
            execution_mode="precomputed",
            mode=mode,
        )
        self.examples = build_examples()
        self.corpora = build_corpora()
        self.example: TokenisationExample | None = None
        self.base_title = ""
        self.base_subtitle = ""
        self.base_text = ""
        self.custom_text: str | None = None
        self.options: dict[str, Any] = {
            "playback_speed": 1.0,
            "tokeniser_mode": "bpe",
            "corpus": "office_messages",
            "num_merges": 12,
            "context_window": 64,
        }
        self.load_example(example or "simple_sentence")

    def list_examples(self) -> list[str]:
        return list(self.examples.keys())

    def list_corpora(self) -> list[str]:
        return list(self.corpora.keys())

    def load_example(self, name: str) -> None:
        if name not in self.examples:
            raise AI9414Error(
                code="example_not_found",
                message=f"Example '{name}' was not found.",
                details={"available_examples": self.list_examples()},
            )
        self.example_name = name
        self.config_name = None
        self.example = self.examples[name]
        self.base_title = self.example.title
        self.base_subtitle = self.example.subtitle
        self.base_text = self.example.text
        self.custom_text = None
        self.options["corpus"] = self.example.default_corpus
        self.reset_runtime()

    def load_config(self, path: str) -> None:
        raw = self.load_base_config(path)
        config = TokenisationConfigModel.model_validate(raw)
        self.example_name = None
        self.config_name = Path(path).name
        self.example = None
        self.base_title = config.data.title
        self.base_subtitle = config.data.subtitle
        self.base_text = config.data.text
        self.custom_text = None
        self.options = {
            "playback_speed": 1.0,
            "tokeniser_mode": "bpe",
            "corpus": config.data.corpus,
            "num_merges": 12,
            "context_window": 64,
        }
        self.set_options(**config.options)
        self.reset_runtime()

    def set_options(self, **kwargs: Any) -> None:
        allowed = {"playback_speed", "tokeniser_mode", "corpus", "num_merges", "context_window"}
        unknown = sorted(set(kwargs) - allowed)
        if unknown:
            raise AI9414Error(
                code="invalid_option_value",
                message=f"Unknown option(s): {', '.join(unknown)}.",
                details={"allowed_options": sorted(allowed)},
            )

        if "playback_speed" in kwargs:
            playback_speed = float(kwargs["playback_speed"])
            if not 0.5 <= playback_speed <= 5.0:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="Playback speed must be between 0.5 and 5.0.",
                    details={"allowed_range": [0.5, 5.0]},
                )
            self.options["playback_speed"] = playback_speed

        if "tokeniser_mode" in kwargs:
            tokeniser_mode = str(kwargs["tokeniser_mode"])
            if tokeniser_mode not in {"character", "word", "bpe"}:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="tokeniser_mode must be 'character', 'word', or 'bpe'.",
                )
            self.options["tokeniser_mode"] = tokeniser_mode

        if "corpus" in kwargs:
            corpus_name = str(kwargs["corpus"])
            if corpus_name not in self.corpora:
                raise AI9414Error(
                    code="invalid_option_value",
                    message=f"Corpus '{corpus_name}' was not found.",
                    details={"available_corpora": self.list_corpora()},
                )
            self.options["corpus"] = corpus_name

        if "num_merges" in kwargs:
            num_merges = int(kwargs["num_merges"])
            if not 0 <= num_merges <= 24:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="num_merges must be between 0 and 24.",
                    details={"allowed_range": [0, 24]},
                )
            self.options["num_merges"] = num_merges

        if "context_window" in kwargs:
            context_window = int(kwargs["context_window"])
            if not 8 <= context_window <= 512:
                raise AI9414Error(
                    code="invalid_option_value",
                    message="context_window must be between 8 and 512.",
                    details={"allowed_range": [8, 512]},
                )
            self.options["context_window"] = context_window

    def set_text(self, text: str) -> None:
        cleaned = str(text)
        if not cleaned.strip():
            raise AI9414Error(
                code="invalid_option_value",
                message="Custom text must not be empty.",
            )
        self.custom_text = cleaned
        self.reset_runtime()

    def reset_text(self) -> None:
        self.custom_text = None
        self.reset_runtime()

    def load_corpus(self, name: str) -> None:
        self.set_options(corpus=name)
        self.reset_runtime()

    def learn_merges(self, num_merges: int) -> None:
        self.set_options(num_merges=num_merges)
        self.reset_runtime()

    def set_tokeniser_mode(self, mode: str) -> None:
        self.set_options(tokeniser_mode=mode)
        self.reset_runtime()

    def set_context_window(self, context_window: int) -> None:
        self.set_options(context_window=context_window)
        self.reset_runtime()

    def build_initial_state(self) -> dict[str, Any]:
        bundle = self._build_bundle()
        self._trace_bundle = bundle
        data = copy.deepcopy(bundle.initial_state)
        data["playback_speed"] = self.options["playback_speed"]
        data["options"] = {
            "tokeniser_mode": self.options["tokeniser_mode"],
            "corpus": self.options["corpus"],
            "num_merges": self.options["num_merges"],
            "context_window": self.options["context_window"],
        }
        data["foundation_models"]["available_corpora"] = [
            {
                "value": corpus.name,
                "label": corpus.title,
                "subtitle": corpus.subtitle,
            }
            for corpus in self.corpora.values()
        ]
        return {
            "schema_version": "1.0",
            "app_type": self.app_type,
            "example_name": self.example_name,
            "config_name": self.config_name,
            "options": self.options,
            "view": {"current_step": self.current_step},
            "data": data,
        }

    def build_trace(self) -> dict[str, Any]:
        if self._trace_bundle is None:
            self._trace_bundle = self._build_bundle()
        return self._trace_bundle.model_dump()

    def handle_app_command(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        if command == "set_text":
            text = payload.get("text")
            if not isinstance(text, str):
                raise AI9414Error(
                    code="invalid_action_payload",
                    message="Command 'set_text' requires a string field 'text'.",
                )
            self.set_text(text)
        elif command == "reset_text":
            self.reset_text()
        else:
            raise AI9414Error(
                code="unsupported_action",
                message=f"Tokenisation command '{command}' is not supported.",
            )

        return {
            "ok": True,
            "state": self.build_state_payload(),
            "trace": self.get_trace_payload(),
            "trace_complete": True,
        }

    def reset_runtime(self) -> None:
        self.current_step = 0
        self._base_state_data = {}
        self._current_state_data = {}
        self._trace_bundle = None
        self._trace_cache_complete = False
        self.ensure_runtime_ready()

    def _build_bundle(self):
        return build_foundation_trace(
            self._build_problem(),
            custom_text_active=self.custom_text is not None,
        )

    def _build_problem(self) -> TokenisationProblem:
        corpus = self._selected_corpus()
        return TokenisationProblem(
            title=self.base_title or "Tokenisation explorer",
            subtitle=self.base_subtitle or "Compare text representations across several tokenisers.",
            text=self.custom_text or self.base_text,
            corpus_name=corpus.name,
            corpus_texts=corpus.texts,
            tokeniser_mode=self.options["tokeniser_mode"],
            num_merges=self.options["num_merges"],
            context_window=self.options["context_window"],
        )

    def _selected_corpus(self) -> TokenisationCorpus:
        corpus_name = str(self.options["corpus"])
        if corpus_name not in self.corpora:
            raise AI9414Error(
                code="invalid_option_value",
                message=f"Corpus '{corpus_name}' was not found.",
                details={"available_corpora": self.list_corpora()},
            )
        return self.corpora[corpus_name]
