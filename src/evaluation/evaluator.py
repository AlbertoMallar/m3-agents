"""Optional Langfuse-scored evaluator for grounded specialist responses."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.agents.grounded_agent_utils import format_context_documents, get_chat_model
from src.observability.langfuse import (
    configured_model_name,
    document_references,
    observe,
    update_observation,
)

EVALUATOR_SYSTEM_PROMPT: Final = """
You evaluate an internal-support response using only the user query, the final
response, and any retrieved internal context supplied to you.

Score each dimension from 1 to 10:
- relevance: how directly the response addresses the query.
- completeness: whether it includes the supported practical information needed.
- accuracy: whether it is supported by the provided context. If context is absent
  or insufficient, do not claim objective factual accuracy; score conservatively.

Do not invent evidence. A safe statement that information is unavailable can be
accurate when the supplied context does not support the requested answer.
Return only the requested structured output.
""".strip()
EVALUATOR_PROMPT: Final = ChatPromptTemplate.from_messages(
    [
        ("system", EVALUATOR_SYSTEM_PROMPT),
        (
            "human",
            "User query:\n{user_query}\n\nFinal response:\n{final_response}"
            "\n\nRetrieved internal context:\n{context}",
        ),
    ]
)


class EvaluationResult(BaseModel):
    """Structured quality assessment for a single system response."""

    model_config = ConfigDict(extra="forbid")
    relevance: int = Field(ge=1, le=10)
    completeness: int = Field(ge=1, le=10)
    accuracy: int = Field(ge=1, le=10)
    overall_score: int = Field(ge=1, le=10)
    reason: str = Field(min_length=1)


class EvaluatorGenerationError(RuntimeError):
    """Raised when the evaluator model returns an invalid structured result."""


class ResponseEvaluator:
    """Evaluates responses without participating in the production workflow."""

    def __init__(self, *, model_name: str | None = None, model: object | None = None) -> None:
        chat_model = get_chat_model(model_name=model_name, model=model)
        self._chain = EVALUATOR_PROMPT | chat_model.with_structured_output(
            EvaluationResult,
            method="json_schema",
        )

    def evaluate(
        self,
        *,
        user_query: str,
        final_response: str,
        context_documents: Sequence[Document] | None = None,
        domain: str | None = None,
    ) -> EvaluationResult:
        """Return a structured evaluation and attach its scores to Langfuse."""

        if not isinstance(user_query, str) or not user_query.strip():
            raise ValueError("user_query must be a non-empty string.")
        if not isinstance(final_response, str) or not final_response.strip():
            raise ValueError("final_response must be a non-empty string.")

        documents = list(context_documents or [])
        references = document_references(documents)
        context = format_context_documents(documents, domain_label=domain or "Internal")
        with observe(
            name="response-evaluator",
            as_type="evaluator",
            input={
                "user_query": user_query,
                "final_response": final_response,
                "chunks": references,
            },
            metadata={"domain": domain, "chunk_count": len(documents)},
            model=configured_model_name(),
            error_stage="evaluator",
        ) as observation:
            result = self._chain.invoke(
                {
                    "user_query": user_query,
                    "final_response": final_response,
                    "context": context or "No retrieved context was provided.",
                }
            )
            if not isinstance(result, EvaluationResult):
                try:
                    result = EvaluationResult.model_validate(result)
                except ValidationError as exc:
                    raise EvaluatorGenerationError(
                        "The evaluator returned an invalid structured result."
                    ) from exc

            update_observation(observation, output=result.model_dump())
            if observation is not None:
                for score_name in ("relevance", "completeness", "accuracy", "overall_score"):
                    observation.score_trace(
                        name=score_name,
                        value=float(getattr(result, score_name)),
                        data_type="NUMERIC",
                        comment=result.reason,
                    )
            return result

    def evaluate_safely(
        self,
        *,
        user_query: str,
        final_response: str,
        context_documents: Sequence[Document] | None = None,
        domain: str | None = None,
    ) -> EvaluationResult | None:
        """Return ``None`` on evaluator failure so callers never block responses."""

        try:
            return self.evaluate(
                user_query=user_query,
                final_response=final_response,
                context_documents=context_documents,
                domain=domain,
            )
        except Exception:
            return None
