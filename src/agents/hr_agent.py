"""HR specialist agent prepared for future RAG integration."""

from __future__ import annotations

import os
from typing import Final, Sequence

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

load_dotenv()

DEFAULT_MODEL_ENV_VARS: Final[tuple[str, ...]] = ("OPENAI_MODEL", "MODEL_NAME")
NO_CONTEXT_RESPONSE_TEXT: Final = (
    "No hay contexto interno suficiente de Recursos Humanos para responder "
    "con seguridad esta consulta."
)

HR_SYSTEM_PROMPT: Final = """
You are the HR specialist for PI internal support.

Your only responsibility is to answer Human Resources questions using the
internal HR context provided to you.

Rules:
- Answer only with information supported by the provided internal HR context.
- Do not use general world knowledge, prior assumptions, or unstated company policies.
- If the provided context does not contain enough evidence to answer safely,
  say that there is not enough internal HR context to answer.
- Do not invent benefits, policies, numbers, deadlines, or procedures.
- Be concise, clear, and practical.
- Respond in the same language as the user's question when possible.
- Return structured output that matches the requested schema.
""".strip()

HR_RESPONSE_PROMPT: Final = ChatPromptTemplate.from_messages(
    [
        ("system", HR_SYSTEM_PROMPT),
        (
            "human",
            "Consulta del usuario:\n{user_query}\n\n"
            "Contexto interno de HR:\n{context}",
        ),
    ]
)


class HRConfigurationError(ValueError):
    """Raised when the HR agent cannot be configured from the environment."""


class HRGenerationError(RuntimeError):
    """Raised when the model returns an invalid HR response payload."""


class HRResponse(BaseModel):
    """Typed response contract for the HR specialist."""

    model_config = ConfigDict(extra="forbid")

    response: str = Field(
        description="Answer for the HR query based only on internal HR context."
    )
    has_sufficient_context: bool = Field(
        description=(
            "True only when the provided internal HR context contains enough "
            "evidence to answer safely."
        )
    )


def _resolve_model_name(explicit_model_name: str | None = None) -> str:
    """Resolve the OpenAI model name from arguments or environment variables."""

    if explicit_model_name and explicit_model_name.strip():
        return explicit_model_name.strip()

    for env_var in DEFAULT_MODEL_ENV_VARS:
        value = os.getenv(env_var, "").strip()
        if value:
            return value

    expected_vars = ", ".join(DEFAULT_MODEL_ENV_VARS)
    raise HRConfigurationError(
        "No OpenAI model configured for the HR agent. "
        f"Set one of these environment variables: {expected_vars}."
    )


def _validate_api_key_presence() -> None:
    """Fail fast with a clear configuration error when no API key is available."""

    if os.getenv("OPENAI_API_KEY", "").strip():
        return

    raise HRConfigurationError(
        "OPENAI_API_KEY is required to generate HR answers with the agent."
    )


def _build_no_context_response() -> HRResponse:
    """Return the safe fallback used when no internal HR context is available."""

    return HRResponse(
        response=NO_CONTEXT_RESPONSE_TEXT,
        has_sufficient_context=False,
    )


class HRAgent:
    """Human Resources specialist that answers only from provided internal context."""

    def __init__(
        self,
        *,
        model_name: str | None = None,
        model: ChatOpenAI | object | None = None,
    ) -> None:
        if model is None:
            _validate_api_key_presence()
            resolved_model_name = _resolve_model_name(model_name)
            model = ChatOpenAI(
                model=resolved_model_name,
                temperature=0,
            )

        self._response_chain = HR_RESPONSE_PROMPT | model.with_structured_output(
            HRResponse,
            method="json_schema",
        )

    def answer(
        self,
        user_query: str,
        *,
        context_documents: Sequence[Document] | None = None,
    ) -> HRResponse:
        """Answer an HR query using only externally provided internal documents."""

        if not isinstance(user_query, str):
            raise TypeError("user_query must be a string.")

        normalized_query = user_query.strip()
        if not normalized_query:
            return _build_no_context_response()

        context = self._format_context_documents(context_documents)
        if not context:
            return _build_no_context_response()

        result = self._response_chain.invoke(
            {
                "user_query": normalized_query,
                "context": context,
            }
        )

        if isinstance(result, HRResponse):
            return result

        try:
            return HRResponse.model_validate(result)
        except ValidationError as exc:
            raise HRGenerationError(
                "The HR agent model returned an invalid structured response."
            ) from exc

    def handle(
        self,
        user_query: str,
        *,
        context_documents: Sequence[Document] | None = None,
    ) -> HRResponse:
        """Compatibility alias for future workflow integration."""

        return self.answer(user_query, context_documents=context_documents)

    def _format_context_documents(
        self,
        context_documents: Sequence[Document] | None,
    ) -> str:
        """Convert retrieved HR documents into a prompt-ready context string."""

        if not context_documents:
            return ""

        chunks: list[str] = []
        for index, document in enumerate(context_documents, start=1):
            content = document.page_content.strip()
            if not content:
                continue

            source = str(document.metadata.get("source", f"hr_doc_{index}"))
            section = document.metadata.get("section")
            header = f"[HR Document {index}] Source: {source}"
            if section:
                header = f"{header} | Section: {section}"

            chunks.append(f"{header}\n{content}")

        return "\n\n".join(chunks)
