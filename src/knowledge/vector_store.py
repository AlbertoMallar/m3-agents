"""Reusable vector-store infrastructure for domain knowledge bases."""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

EMBEDDING_MODEL_ENV_VAR: Final = "EMBEDDING_MODEL"


class EmbeddingConfigurationError(ValueError):
    """Raised when OpenAI embeddings cannot be configured from the environment."""


def get_openai_embeddings(*, model_name: str | None = None) -> OpenAIEmbeddings:
    """Create OpenAI embeddings from an explicit model or ``EMBEDDING_MODEL``."""

    _validate_openai_api_key()
    resolved_model_name = _resolve_embedding_model_name(model_name)
    return OpenAIEmbeddings(model=resolved_model_name)


def get_or_create_vector_store(
    documents: Sequence[Document],
    *,
    collection_name: str,
    persist_directory: str | Path,
    embeddings: OpenAIEmbeddings,
) -> Chroma:
    """Open a persisted collection or index documents when it is empty.

    Documents, including their metadata, are added exactly as received. Existing
    non-empty collections are reused to avoid re-embedding on each execution.
    """

    if not documents:
        raise ValueError("documents must contain at least one Document.")
    if not collection_name.strip():
        raise ValueError("collection_name must not be empty.")

    storage_path = Path(persist_directory).expanduser().resolve()
    storage_path.mkdir(parents=True, exist_ok=True)
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(storage_path),
    )

    existing = vector_store.get(limit=1, include=[])
    if existing["ids"]:
        return vector_store

    vector_store.add_documents(list(documents))
    return vector_store


def _resolve_embedding_model_name(explicit_model_name: str | None = None) -> str:
    """Resolve the embedding model name without hard-coding provider settings."""

    if explicit_model_name and explicit_model_name.strip():
        return explicit_model_name.strip()

    model_name = os.getenv(EMBEDDING_MODEL_ENV_VAR, "").strip()
    if model_name:
        return model_name

    raise EmbeddingConfigurationError(
        f"{EMBEDDING_MODEL_ENV_VAR} is required to configure OpenAI embeddings."
    )


def _validate_openai_api_key() -> None:
    """Fail fast before making embedding requests without credentials."""

    if os.getenv("OPENAI_API_KEY", "").strip():
        return

    raise EmbeddingConfigurationError(
        "OPENAI_API_KEY is required to create OpenAI embeddings."
    )
