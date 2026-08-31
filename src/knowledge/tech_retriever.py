"""Retriever factory for the Tech knowledge base."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from langchain_core.vectorstores import VectorStoreRetriever
from langchain_chroma import Chroma

from src.knowledge.hr_documents import REPO_ROOT
from src.knowledge.tech_documents import load_tech_documents
from src.knowledge.vector_store import (
    get_openai_embeddings,
    get_or_create_vector_store,
)

TECH_COLLECTION_NAME: Final = "tech_knowledge_base"
TECH_VECTOR_STORE_DIRECTORY: Final = REPO_ROOT / "data" / "vector_stores" / "tech"
DEFAULT_RETRIEVER_K: Final = 4


def get_tech_vector_store(
    *,
    persist_directory: str | Path = TECH_VECTOR_STORE_DIRECTORY,
) -> Chroma:
    """Open or build the persisted Chroma collection for Tech documents."""

    return get_or_create_vector_store(
        load_tech_documents(),
        collection_name=TECH_COLLECTION_NAME,
        persist_directory=persist_directory,
        embeddings=get_openai_embeddings(),
    )


def get_tech_retriever(
    *,
    k: int = DEFAULT_RETRIEVER_K,
    persist_directory: str | Path = TECH_VECTOR_STORE_DIRECTORY,
) -> VectorStoreRetriever:
    """Return the Tech similarity retriever configured with ``k`` results."""

    if k <= 0:
        raise ValueError("k must be greater than zero.")
    return get_tech_vector_store(persist_directory=persist_directory).as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
