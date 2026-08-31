"""Loading and chunking interface for the Finance knowledge base."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from langchain_core.documents import Document

from src.knowledge.hr_documents import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from src.knowledge.markdown_documents import (
    REPO_ROOT,
    load_markdown_documents,
    load_markdown_knowledge_base_text,
)

DEFAULT_FINANCE_KNOWLEDGE_BASE_PATH: Final = (
    REPO_ROOT / "data" / "finance_docs" / "finance_knowledge_base.md"
)


def resolve_finance_knowledge_base_path(path: str | Path | None = None) -> Path:
    """Resolve the Finance knowledge-base path."""

    if path is None:
        return DEFAULT_FINANCE_KNOWLEDGE_BASE_PATH
    return Path(path).expanduser().resolve()


def load_finance_knowledge_base_text(path: str | Path | None = None) -> str:
    """Read the Finance knowledge base Markdown file."""

    return load_markdown_knowledge_base_text(resolve_finance_knowledge_base_path(path))


def load_finance_documents(
    path: str | Path | None = None,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    """Load the Finance knowledge base as metadata-preserving chunks."""

    return load_markdown_documents(
        resolve_finance_knowledge_base_path(path),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def count_finance_document_chunks(**kwargs: int) -> int:
    """Return the number of Finance chunks for a chunking configuration."""

    return len(load_finance_documents(**kwargs))
