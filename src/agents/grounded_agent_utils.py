"""Small shared utilities for context-only domain agents."""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Final

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

load_dotenv()

DEFAULT_MODEL_ENV_VARS: Final[tuple[str, ...]] = ("OPENAI_MODEL", "MODEL_NAME")


class GroundedAgentConfigurationError(ValueError):
    """Raised when a context-only domain agent lacks model configuration."""


def get_chat_model(
    *,
    model_name: str | None = None,
    model: ChatOpenAI | object | None = None,
) -> ChatOpenAI | object:
    """Return an injected model or a deterministic OpenAI chat model."""

    if model is not None:
        return model
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise GroundedAgentConfigurationError(
            "OPENAI_API_KEY is required to generate grounded domain answers."
        )

    resolved_model_name = model_name.strip() if model_name and model_name.strip() else ""
    if not resolved_model_name:
        for env_var in DEFAULT_MODEL_ENV_VARS:
            value = os.getenv(env_var, "").strip()
            if value:
                resolved_model_name = value
                break
    if not resolved_model_name:
        expected_vars = ", ".join(DEFAULT_MODEL_ENV_VARS)
        raise GroundedAgentConfigurationError(
            "No OpenAI model configured for the domain agent. "
            f"Set one of these environment variables: {expected_vars}."
        )

    return ChatOpenAI(model=resolved_model_name, temperature=0)


def format_context_documents(
    context_documents: Sequence[Document] | None,
    *,
    domain_label: str,
) -> str:
    """Convert retrieved documents into labeled prompt context."""

    if not context_documents:
        return ""

    chunks: list[str] = []
    for index, document in enumerate(context_documents, start=1):
        content = document.page_content.strip()
        if not content:
            continue
        source = str(document.metadata.get("source", f"{domain_label.lower()}_doc_{index}"))
        section = document.metadata.get("section")
        header = f"[{domain_label} Document {index}] Source: {source}"
        if section:
            header = f"{header} | Section: {section}"
        chunks.append(f"{header}\n{content}")

    return "\n\n".join(chunks)
