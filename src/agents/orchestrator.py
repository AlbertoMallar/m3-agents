"""Intent classifier for the multi-agent orchestrator."""

from __future__ import annotations

import os
from typing import Final, Literal

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

load_dotenv()

Route = Literal["hr", "tech", "finance", "out_of_scope"]

DEFAULT_MODEL_ENV_VARS: Final[tuple[str, ...]] = ("OPENAI_MODEL", "MODEL_NAME")

ORCHESTRATOR_SYSTEM_PROMPT: Final = """
You are the intent classifier for PI internal support.

Your only responsibility is to classify the user's request into exactly one route:
- hr
- tech
- finance
- out_of_scope

Route definitions for PI internal support:

hr:
- Employee people-support topics.
- Time off, vacations, leaves, benefits, payroll receipts, onboarding, offboarding,
  performance processes, internal HR policies, employee documentation and manager / people operations requests.
- Use hr when the core question is about the employment relationship or HR processes.

tech:
- Internal technical support and systems topics.
- Access issues, accounts, passwords, permissions, laptop or device issues, VPN, email,
  internal tools, software incidents, bugs, integrations, infrastructure, development tooling,
  application behavior, data pipelines and technical troubleshooting.
- Use tech when the core question is about technology, systems or IT support.

finance:
- Internal financial operations and administrative money topics.
- Budgets, invoices, expense reports, reimbursements, purchase approvals, procurement,
  cost centers, supplier payments, billing operations, financial controls and similar requests.
- Use finance when the core question is about money, spending, budgeting or financial administration.

out_of_scope:
- The request is outside PI internal support.
- The request is too vague to classify confidently.
- The request mixes multiple domains without one clearly primary owner.

Important rules:
- Return exactly one route.
- Do not answer the user question.
- Do not explain your reasoning.
- Prefer out_of_scope only when no single domain clearly owns the request.
""".strip()


class OrchestratorConfigurationError(ValueError):
    """Raised when the orchestrator cannot be configured from the environment."""


class OrchestratorClassificationError(RuntimeError):
    """Raised when the model does not return a valid routing decision."""


class OrchestratorDecision(BaseModel):
    """Structured classification output used by the orchestrator."""

    model_config = ConfigDict(extra="forbid")

    route: Route = Field(
        description=(
            "Single routing decision for PI internal support. "
            "Must be one of: hr, tech, finance, out_of_scope."
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
    raise OrchestratorConfigurationError(
        "No OpenAI model configured for the orchestrator. "
        f"Set one of these environment variables: {expected_vars}."
    )


def _validate_api_key_presence() -> None:
    """Fail fast with a clear configuration error when no API key is available."""

    if os.getenv("OPENAI_API_KEY", "").strip():
        return

    raise OrchestratorConfigurationError(
        "OPENAI_API_KEY is required to classify queries with the orchestrator."
    )


class OrchestratorAgent:
    """Classifies internal support queries into a single domain route."""

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

        self._classifier = model.with_structured_output(
            OrchestratorDecision,
            method="json_schema",
        )

    def classify(self, user_query: str) -> Route:
        """Return a single route for the given PI internal support query."""

        decision = self.classify_decision(user_query)
        return decision.route

    def classify_decision(self, user_query: str) -> OrchestratorDecision:
        """Return the validated structured classification decision."""

        if not isinstance(user_query, str):
            raise TypeError("user_query must be a string.")

        normalized_query = user_query.strip()
        if not normalized_query:
            return OrchestratorDecision(route="out_of_scope")

        result = self._classifier.invoke(
            [
                {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
                {"role": "user", "content": normalized_query},
            ]
        )

        if isinstance(result, OrchestratorDecision):
            return result

        try:
            return OrchestratorDecision.model_validate(result)
        except ValidationError as exc:
            raise OrchestratorClassificationError(
                "The orchestrator model returned an invalid structured routing decision."
            ) from exc

    def route(self, user_query: str) -> Route:
        """Compatibility alias for future workflow integration."""

        return self.classify(user_query)
