"""Shared Markdown loading and chunking utilities for domain knowledge bases."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
HEADERS_TO_SPLIT_ON: Final[list[tuple[str, str]]] = [
    ("#", "document_title"),
    ("##", "section"),
    ("###", "subsection"),
]


def load_markdown_knowledge_base_text(path: str | Path) -> str:
    """Read a Markdown knowledge-base file as UTF-8 text."""

    return Path(path).expanduser().resolve().read_text(encoding="utf-8")


def load_markdown_sections(path: str | Path) -> list[Document]:
    """Split a Markdown file by headers and preserve source metadata."""

    source_path = Path(path).expanduser().resolve()
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=False,
    )
    sections = markdown_splitter.split_text(load_markdown_knowledge_base_text(source_path))

    return [
        Document(
            page_content=section.page_content,
            metadata=_build_section_metadata(section.metadata, source_path),
        )
        for section in sections
    ]


def load_markdown_documents(
    path: str | Path,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    """Load a Markdown knowledge base and return metadata-preserving chunks."""

    _validate_chunking_configuration(chunk_size, chunk_overlap)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunked_documents = splitter.split_documents(load_markdown_sections(path))

    return [
        Document(
            page_content=document.page_content,
            metadata={
                **document.metadata,
                "chunk_index": index,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            },
        )
        for index, document in enumerate(chunked_documents)
    ]


def _validate_chunking_configuration(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be zero or greater.")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")


def _build_section_metadata(
    metadata: dict[str, str],
    source_path: Path,
) -> dict[str, str]:
    """Enrich header metadata with source information and a section path."""

    enriched_metadata: dict[str, str] = {
        **metadata,
        "source": str(source_path),
        "source_name": source_path.name,
    }
    section_path_parts = [
        enriched_metadata[key]
        for key in ("document_title", "section", "subsection")
        if enriched_metadata.get(key)
    ]
    if section_path_parts:
        enriched_metadata["section_path"] = " > ".join(section_path_parts)

    return enriched_metadata
