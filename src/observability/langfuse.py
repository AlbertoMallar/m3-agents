"""Centralized, optional Langfuse observability for the multi-agent workflow."""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Iterator, Literal

from dotenv import load_dotenv

load_dotenv()

ObservationType = Literal["agent", "retriever", "generation", "span", "evaluator"]
_LANGFUSE_ENV_VARS = (
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_HOST",
)
_SECRET_PATTERNS = (
    re.compile(r"\b(?:sk|pk)-[A-Za-z0-9_-]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+"),
)


class LangfuseConfigurationError(ValueError):
    """Raised when only part of the Langfuse configuration is present."""


def is_langfuse_enabled() -> bool:
    """Return whether all required Langfuse variables are configured."""

    values = [os.getenv(env_var, "").strip() for env_var in _LANGFUSE_ENV_VARS]
    if not any(values):
        return False
    if not all(values):
        missing = ", ".join(
            env_var
            for env_var, value in zip(_LANGFUSE_ENV_VARS, values, strict=True)
            if not value
        )
        raise LangfuseConfigurationError(
            "Incomplete Langfuse configuration. Missing: " + missing + "."
        )
    return True


@lru_cache(maxsize=1)
def get_langfuse_client():
    """Return the configured Langfuse v4 client or ``None`` in local no-op mode."""

    if not is_langfuse_enabled():
        return None

    from langfuse import Langfuse, get_client

    public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
    Langfuse(
        public_key=public_key,
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        base_url=os.environ["LANGFUSE_HOST"],
    )
    return get_client(public_key=public_key)


@contextmanager
def observe(
    *,
    name: str,
    as_type: ObservationType,
    input: Any | None = None,
    metadata: dict[str, Any] | None = None,
    model: str | None = None,
    error_stage: str | None = None,
) -> Iterator[Any | None]:
    """Create a nested Langfuse observation or yield a no-op local context."""

    client = get_langfuse_client()
    if client is None:
        yield None
        return

    with client.start_as_current_observation(
        name=name,
        as_type=as_type,
        input=input,
        metadata=metadata,
        model=model,
    ) as observation:
        try:
            yield observation
        except Exception as exc:
            observation.update(
                level="ERROR",
                status_message=_safe_error_message(exc),
                metadata={
                    **(metadata or {}),
                    "error_stage": error_stage or name,
                    "error_type": type(exc).__name__,
                },
            )
            raise


def update_observation(
    observation: Any | None,
    *,
    output: Any | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Update an active observation without coupling callers to the SDK type."""

    if observation is not None:
        observation.update(output=output, metadata=metadata)


def document_references(documents: list[Any]) -> list[dict[str, Any]]:
    """Create retrieval-safe chunk descriptors without serializing document text."""

    references: list[dict[str, Any]] = []
    for document in documents:
        metadata = document.metadata
        references.append(
            {
                "source_name": metadata.get("source_name"),
                "section_path": metadata.get("section_path"),
                "chunk_index": metadata.get("chunk_index"),
                "size": len(document.page_content),
            }
        )
    return references


def configured_model_name() -> str | None:
    """Return the configured chat model name for generation metadata."""

    return os.getenv("OPENAI_MODEL", "").strip() or os.getenv(
        "MODEL_NAME", ""
    ).strip() or None


def flush_langfuse() -> None:
    """Flush pending events for short-lived command-line processes."""

    client = get_langfuse_client()
    if client is not None:
        client.flush()


def _safe_error_message(exc: Exception) -> str:
    """Keep useful diagnostics while redacting token-shaped values."""

    message = str(exc)[:500]
    for pattern in _SECRET_PATTERNS:
        message = pattern.sub("[REDACTED]", message)
    return message or type(exc).__name__
