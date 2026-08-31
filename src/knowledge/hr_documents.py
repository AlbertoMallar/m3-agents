"""Utilities for loading and chunking the HR knowledge base."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from langchain_core.documents import Document

from src.knowledge.markdown_documents import (
    REPO_ROOT,
    load_markdown_documents,
    load_markdown_knowledge_base_text,
    load_markdown_sections,
)

DEFAULT_HR_KNOWLEDGE_BASE_PATH: Final = (
    REPO_ROOT / "data" / "hr_docs" / "hr_knowledge_base.md"
)
DEFAULT_CHUNK_SIZE: Final = 800
DEFAULT_CHUNK_OVERLAP: Final = 120


def resolve_hr_knowledge_base_path(path: str | Path | None = None) -> Path:
    """Resolve the HR knowledge base path, defaulting to the project document."""

    if path is None:
        return DEFAULT_HR_KNOWLEDGE_BASE_PATH
    return Path(path).expanduser().resolve()


def load_hr_knowledge_base_text(path: str | Path | None = None) -> str:
    """Read the HR knowledge base Markdown file as UTF-8 text."""

    return load_markdown_knowledge_base_text(resolve_hr_knowledge_base_path(path))


def load_hr_markdown_sections(path: str | Path | None = None) -> list[Document]:
    """Split the HR Markdown file by headers while preserving section metadata."""

    return load_markdown_sections(resolve_hr_knowledge_base_path(path))


def load_hr_documents(
    path: str | Path | None = None,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    """Load the HR knowledge base and return chunked LangChain documents."""

    return load_markdown_documents(
        resolve_hr_knowledge_base_path(path),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def count_hr_document_chunks(
    path: str | Path | None = None,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> int:
    """Return the total number of HR chunks for the given configuration."""

    return len(
        load_hr_documents(
            path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    )
