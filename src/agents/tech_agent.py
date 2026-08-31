"""Technology specialist grounded only in retrieved internal context."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.agents.grounded_agent_utils import format_context_documents, get_chat_model

NO_CONTEXT_RESPONSE_TEXT: Final = (
    "No hay contexto interno suficiente de Tecnologia para responder con seguridad "
    "esta consulta."
)
TECH_SYSTEM_PROMPT: Final = """
You are the Technology specialist for PI internal support.

Answer only Technology questions using the internal Tech context provided.
Do not use general knowledge, assumptions, or unstated company procedures.
If the context is insufficient, clearly say so. Do not invent configuration steps,
permissions, security guidance, incident status, or deadlines.
Respond in the user's language when possible and return the requested structured output.
""".strip()
TECH_RESPONSE_PROMPT: Final = ChatPromptTemplate.from_messages(
    [
        ("system", TECH_SYSTEM_PROMPT),
        ("human", "Consulta del usuario:\n{user_query}\n\nContexto interno de Tecnologia:\n{context}"),
    ]
)


class TechGenerationError(RuntimeError):
    """Raised when the model returns an invalid Tech response payload."""


class TechResponse(BaseModel):
    """Typed response contract for the Technology specialist."""

    model_config = ConfigDict(extra="forbid")
    response: str = Field(description="Grounded answer for the Tech query.")
    has_sufficient_context: bool = Field(
        description="True only when the provided Tech context supports the answer."
    )


class TechAgent:
    """Technology specialist that answers only from supplied internal documents."""

    def __init__(self, *, model_name: str | None = None, model: object | None = None) -> None:
        chat_model = get_chat_model(model_name=model_name, model=model)
        self._response_chain = TECH_RESPONSE_PROMPT | chat_model.with_structured_output(
            TechResponse,
            method="json_schema",
        )

    def answer(
        self,
        user_query: str,
        *,
        context_documents: Sequence[Document] | None = None,
    ) -> TechResponse:
        """Answer a Tech query using only externally supplied evidence."""

        if not isinstance(user_query, str):
            raise TypeError("user_query must be a string.")
        context = format_context_documents(context_documents, domain_label="Tech")
        if not user_query.strip() or not context:
            return TechResponse(
                response=NO_CONTEXT_RESPONSE_TEXT,
                has_sufficient_context=False,
            )
        result = self._response_chain.invoke({"user_query": user_query.strip(), "context": context})
        if isinstance(result, TechResponse):
            return result
        try:
            return TechResponse.model_validate(result)
        except ValidationError as exc:
            raise TechGenerationError(
                "The Tech agent returned an invalid structured response."
            ) from exc

    def handle(
        self,
        user_query: str,
        *,
        context_documents: Sequence[Document] | None = None,
    ) -> TechResponse:
        """Compatibility alias for future workflow integration."""

        return self.answer(user_query, context_documents=context_documents)
