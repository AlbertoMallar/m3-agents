"""Retriever factory for the Finance knowledge base."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from langchain_core.vectorstores import VectorStoreRetriever
from langchain_chroma import Chroma

from src.knowledge.finance_documents import load_finance_documents
from src.knowledge.hr_documents import REPO_ROOT
from src.knowledge.vector_store import (
    get_openai_embeddings,
    get_or_create_vector_store,
)

FINANCE_COLLECTION_NAME: Final = "finance_knowledge_base"
FINANCE_VECTOR_STORE_DIRECTORY: Final = (
    REPO_ROOT / "data" / "vector_stores" / "finance"
)
DEFAULT_RETRIEVER_K: Final = 4


def get_finance_vector_store(
    *,
    persist_directory: str | Path = FINANCE_VECTOR_STORE_DIRECTORY,
) -> Chroma:
    """Open or build the persisted Chroma collection for Finance documents."""

    return get_or_create_vector_store(
        load_finance_documents(),
        collection_name=FINANCE_COLLECTION_NAME,
        persist_directory=persist_directory,
        embeddings=get_openai_embeddings(),
    )


def get_finance_retriever(
    *,
    k: int = DEFAULT_RETRIEVER_K,
    persist_directory: str | Path = FINANCE_VECTOR_STORE_DIRECTORY,
) -> VectorStoreRetriever:
    """Return the Finance similarity retriever configured with ``k`` results."""

    if k <= 0:
        raise ValueError("k must be greater than zero.")
    return get_finance_vector_store(persist_directory=persist_directory).as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
