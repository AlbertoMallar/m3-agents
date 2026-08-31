"""Shared state and LangGraph workflow skeleton for the multi-agent system.

This module owns the workflow contract and topology only.
Specialized logic can be wired in later from ``src.agents`` without changing
the graph structure defined here.
"""

from __future__ import annotations

from collections.abc import Callable as CollectionCallable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache, partial
from typing import TYPE_CHECKING, Any, Callable, Final, Literal, NotRequired, TypedDict, cast

from src.agents.finance_agent import FinanceAgent
from src.agents.hr_agent import HRAgent
from src.agents.orchestrator import OrchestratorAgent
from src.agents.tech_agent import TechAgent
from src.knowledge.finance_retriever import (
    DEFAULT_RETRIEVER_K as FINANCE_RETRIEVER_K,
    FINANCE_COLLECTION_NAME,
    get_finance_retriever,
)
from src.knowledge.hr_retriever import (
    DEFAULT_RETRIEVER_K as HR_RETRIEVER_K,
    HR_COLLECTION_NAME,
    get_hr_retriever,
)
from src.knowledge.tech_retriever import (
    DEFAULT_RETRIEVER_K as TECH_RETRIEVER_K,
    TECH_COLLECTION_NAME,
    get_tech_retriever,
)
from src.observability.langfuse import (
    configured_model_name,
    document_references,
    observe,
    update_observation,
)

if TYPE_CHECKING:
    from langchain_core.vectorstores import VectorStoreRetriever
    from langgraph.graph.state import CompiledStateGraph


Route = Literal["hr", "tech", "finance", "out_of_scope"]

ORCHESTRATOR_NODE: Final = "orchestrator"
HR_NODE: Final = "hr"
TECH_NODE: Final = "tech"
FINANCE_NODE: Final = "finance"
OUT_OF_SCOPE_NODE: Final = "out_of_scope"

HR_FALLBACK_RESPONSE: Final = (
    "No se pudo generar una respuesta de Recursos Humanos en este momento."
)
TECH_FALLBACK_RESPONSE: Final = (
    "No se pudo generar una respuesta de Tecnologia en este momento."
)
FINANCE_FALLBACK_RESPONSE: Final = (
    "No se pudo generar una respuesta de Finanzas en este momento."
)
OUT_OF_SCOPE_PLACEHOLDER_RESPONSE: Final = (
    "No pude determinar si tu consulta corresponde a Recursos Humanos, Soporte "
    "Tecnico o Finanzas. Indica el area o agrega un poco mas de contexto para "
    "poder orientarte."
)

ROUTE_TO_NODE: Final[dict[Route, str]] = {
    "hr": HR_NODE,
    "tech": TECH_NODE,
    "finance": FINANCE_NODE,
    "out_of_scope": OUT_OF_SCOPE_NODE,
}


class InputState(TypedDict):
    """Public input accepted by the workflow."""

    user_query: str


class OverallState(TypedDict):
    """Internal shared state across all nodes."""

    user_query: str
    route: NotRequired[Route]
    response: NotRequired[str]


class OutputState(TypedDict):
    """Public output returned by the workflow."""

    route: Route
    response: str


class RoutingUpdate(TypedDict):
    """Partial state emitted by the orchestrator node."""

    route: Route


class ResponseUpdate(TypedDict):
    """Partial state emitted by specialized and fallback nodes."""

    response: str


OrchestratorHandler = Callable[[InputState], RoutingUpdate]
SpecialistHandler = Callable[[OverallState], ResponseUpdate]


class WorkflowEvent(TypedDict):
    """Optional runtime diagnostics emitted without changing workflow state."""

    name: Literal["classification", "retrieval", "generation", "out_of_scope"]
    data: dict[str, Any]


WorkflowObserver = CollectionCallable[[WorkflowEvent], None]
_workflow_observer: ContextVar[WorkflowObserver | None] = ContextVar(
    "workflow_observer",
    default=None,
)


@contextmanager
def _observe_workflow_events(observer: WorkflowObserver | None) -> Iterator[None]:
    """Scope optional presentation diagnostics to one workflow invocation."""

    token = _workflow_observer.set(observer)
    try:
        yield
    finally:
        _workflow_observer.reset(token)


def _emit_workflow_event(
    name: WorkflowEvent["name"],
    **data: Any,
) -> None:
    """Send safe runtime diagnostics without affecting the workflow result."""

    observer = _workflow_observer.get()
    if observer is None:
        return
    try:
        observer({"name": name, "data": data})
    except Exception:
        # Presentation observers are optional and must never break support flows.
        return


def default_orchestrator_handler(state: InputState) -> RoutingUpdate:
    """Delegate routing to the real orchestrator classifier."""

    agent = get_default_orchestrator_agent()
    return {"route": agent.classify(state["user_query"])}


def default_hr_handler(state: OverallState) -> ResponseUpdate:
    """Retrieve HR evidence and generate a grounded HR response."""

    return _run_specialist_handler(
        state,
        domain="hr",
        collection_name=HR_COLLECTION_NAME,
        k=HR_RETRIEVER_K,
        retriever=get_default_hr_retriever(),
        agent=get_default_hr_agent(),
    )


def default_tech_handler(state: OverallState) -> ResponseUpdate:
    """Retrieve Tech evidence and generate a grounded Tech response."""

    return _run_specialist_handler(
        state,
        domain="tech",
        collection_name=TECH_COLLECTION_NAME,
        k=TECH_RETRIEVER_K,
        retriever=get_default_tech_retriever(),
        agent=get_default_tech_agent(),
    )


def default_finance_handler(state: OverallState) -> ResponseUpdate:
    """Retrieve Finance evidence and generate a grounded Finance response."""

    return _run_specialist_handler(
        state,
        domain="finance",
        collection_name=FINANCE_COLLECTION_NAME,
        k=FINANCE_RETRIEVER_K,
        retriever=get_default_finance_retriever(),
        agent=get_default_finance_agent(),
    )


def default_out_of_scope_handler(state: OverallState) -> ResponseUpdate:
    """Fallback response for unsupported or ambiguous routing results."""

    with observe(
        name="out-of-scope",
        as_type="span",
        input={"user_query": state["user_query"]},
        error_stage="out_of_scope",
    ) as observation:
        response = OUT_OF_SCOPE_PLACEHOLDER_RESPONSE
        update_observation(observation, output={"response": response})
        return {"response": response}


def _run_specialist_handler(
    state: OverallState,
    *,
    domain: Literal["hr", "tech", "finance"],
    collection_name: str,
    k: int,
    retriever: "VectorStoreRetriever",
    agent: HRAgent | TechAgent | FinanceAgent,
) -> ResponseUpdate:
    """Execute one RAG specialist while recording safe diagnostic observations."""

    user_query = state["user_query"]
    with observe(
        name=f"{domain}-agent",
        as_type="agent",
        input={"user_query": user_query},
        metadata={"domain": domain},
        error_stage=f"{domain}_agent",
    ) as agent_observation:
        with observe(
            name=f"{domain}-retrieval",
            as_type="retriever",
            input={"user_query": user_query},
            metadata={"domain": domain, "collection": collection_name, "k": k},
            error_stage=f"{domain}_retrieval",
        ) as retrieval_observation:
            context_documents = retriever.invoke(user_query)
            references = document_references(context_documents)
            _emit_workflow_event(
                "retrieval",
                domain=domain,
                chunk_count=len(context_documents),
                chunk_references=references,
                context_documents=context_documents,
            )
            update_observation(
                retrieval_observation,
                output={"chunk_count": len(context_documents), "chunks": references},
            )

        with observe(
            name=f"{domain}-generation",
            as_type="generation",
            input={"user_query": user_query, "chunks": references},
            metadata={"domain": domain},
            model=configured_model_name(),
            error_stage=f"{domain}_generation",
        ) as generation_observation:
            result = agent.answer(user_query, context_documents=context_documents)
            generation_output = {
                "response": result.response,
                "has_sufficient_context": result.has_sufficient_context,
            }
            _emit_workflow_event(
                "generation",
                domain=domain,
                has_sufficient_context=result.has_sufficient_context,
                response_ready=bool(result.response.strip()),
            )
            update_observation(generation_observation, output=generation_output)

        update_observation(agent_observation, output=generation_output)
        return {"response": result.response}


def _normalize_route(route: object) -> Route:
    """Guarantee that future routing integrations always land on a valid path."""

    if isinstance(route, str) and route in ROUTE_TO_NODE:
        return cast(Route, route)
    return "out_of_scope"


def _normalize_response(response: object, *, fallback: str) -> str:
    """Guarantee a minimal textual response from every terminal node."""

    if isinstance(response, str) and response.strip():
        return response
    return fallback


def orchestrator_node(
    state: InputState,
    *,
    handler: OrchestratorHandler,
) -> RoutingUpdate:
    """Write the route selected by the orchestrator into shared state."""

    with observe(
        name="orchestrator-classification",
        as_type="generation",
        input={"user_query": state["user_query"]},
        model=configured_model_name(),
        error_stage="orchestrator",
    ) as observation:
        update = handler(state)
        route = _normalize_route(update.get("route"))
        _emit_workflow_event("classification", route=route)
        update_observation(observation, output={"route": route})
        return {"route": route}


def hr_node(
    state: OverallState,
    *,
    handler: SpecialistHandler,
) -> ResponseUpdate:
    """Terminal HR node."""

    update = handler(state)
    return {
        "response": _normalize_response(
            update.get("response"),
            fallback=HR_FALLBACK_RESPONSE,
        )
    }


def tech_node(
    state: OverallState,
    *,
    handler: SpecialistHandler,
) -> ResponseUpdate:
    """Terminal Tech node."""

    update = handler(state)
    return {
        "response": _normalize_response(
            update.get("response"),
            fallback=TECH_FALLBACK_RESPONSE,
        )
    }


def finance_node(
    state: OverallState,
    *,
    handler: SpecialistHandler,
) -> ResponseUpdate:
    """Terminal Finance node."""

    update = handler(state)
    return {
        "response": _normalize_response(
            update.get("response"),
            fallback=FINANCE_FALLBACK_RESPONSE,
        )
    }


def out_of_scope_node(
    state: OverallState,
    *,
    handler: SpecialistHandler,
) -> ResponseUpdate:
    """Terminal fallback node for unsupported routes."""

    update = handler(state)
    response = _normalize_response(
        update.get("response"),
        fallback=OUT_OF_SCOPE_PLACEHOLDER_RESPONSE,
    )
    _emit_workflow_event("out_of_scope", response_ready=bool(response.strip()))
    return {
        "response": response
    }


def route_from_state(state: OverallState) -> Route:
    """Read the orchestrator output and choose the next node."""

    return _normalize_route(state.get("route"))


def build_workflow(
    *,
    orchestrator_handler: OrchestratorHandler | None = None,
    hr_handler: SpecialistHandler | None = None,
    tech_handler: SpecialistHandler | None = None,
    finance_handler: SpecialistHandler | None = None,
    out_of_scope_handler: SpecialistHandler | None = None,
) -> "CompiledStateGraph":
    """Create and compile the initial LangGraph workflow."""

    from langgraph.graph import END, START, StateGraph

    builder = StateGraph(
        OverallState,
        input_schema=InputState,
        output_schema=OutputState,
    )

    builder.add_node(
        ORCHESTRATOR_NODE,
        partial(
            orchestrator_node,
            handler=orchestrator_handler or default_orchestrator_handler,
        ),
    )
    builder.add_node(
        HR_NODE,
        partial(hr_node, handler=hr_handler or default_hr_handler),
    )
    builder.add_node(
        TECH_NODE,
        partial(tech_node, handler=tech_handler or default_tech_handler),
    )
    builder.add_node(
        FINANCE_NODE,
        partial(finance_node, handler=finance_handler or default_finance_handler),
    )
    builder.add_node(
        OUT_OF_SCOPE_NODE,
        partial(
            out_of_scope_node,
            handler=out_of_scope_handler or default_out_of_scope_handler,
        ),
    )

    builder.add_edge(START, ORCHESTRATOR_NODE)
    builder.add_conditional_edges(
        ORCHESTRATOR_NODE,
        route_from_state,
        ROUTE_TO_NODE,
    )
    builder.add_edge(HR_NODE, END)
    builder.add_edge(TECH_NODE, END)
    builder.add_edge(FINANCE_NODE, END)
    builder.add_edge(OUT_OF_SCOPE_NODE, END)

    return builder.compile()


@lru_cache(maxsize=1)
def get_default_orchestrator_agent() -> OrchestratorAgent:
    """Create and cache the real orchestrator classifier used by default."""

    return OrchestratorAgent()


@lru_cache(maxsize=1)
def get_default_hr_agent() -> HRAgent:
    """Create and cache the HR specialist used by the default workflow."""

    return HRAgent()


@lru_cache(maxsize=1)
def get_default_hr_retriever() -> "VectorStoreRetriever":
    """Create and cache the persisted HR retriever used by the workflow."""

    return get_hr_retriever()


@lru_cache(maxsize=1)
def get_default_tech_agent() -> TechAgent:
    """Create and cache the Tech specialist used by the default workflow."""

    return TechAgent()


@lru_cache(maxsize=1)
def get_default_tech_retriever() -> "VectorStoreRetriever":
    """Create and cache the persisted Tech retriever used by the workflow."""

    return get_tech_retriever()


@lru_cache(maxsize=1)
def get_default_finance_agent() -> FinanceAgent:
    """Create and cache the Finance specialist used by the default workflow."""

    return FinanceAgent()


@lru_cache(maxsize=1)
def get_default_finance_retriever() -> "VectorStoreRetriever":
    """Create and cache the persisted Finance retriever used by the workflow."""

    return get_finance_retriever()


@lru_cache(maxsize=1)
def get_default_workflow() -> "CompiledStateGraph":
    """Compile and cache the default production workflow."""

    return build_workflow()


def invoke_workflow(
    input_state: InputState,
    *,
    workflow: "CompiledStateGraph | None" = None,
    observer: WorkflowObserver | None = None,
) -> OutputState:
    """Invoke a workflow under one end-to-end Langfuse root observation."""

    active_workflow = workflow or get_default_workflow()
    with _observe_workflow_events(observer):
        with observe(
            name="multi-agent-workflow",
            as_type="agent",
            input={"user_query": input_state["user_query"]},
            error_stage="workflow",
        ) as observation:
            result = cast(OutputState, active_workflow.invoke(input_state))
            update_observation(
                observation,
                output={"route": result["route"], "response": result["response"]},
            )
            return result


def stream_workflow(
    input_state: InputState,
    *,
    workflow: "CompiledStateGraph | None" = None,
    observer: WorkflowObserver | None = None,
) -> Iterator[dict[str, dict[str, Any]]]:
    """Stream a workflow while preserving one end-to-end Langfuse trace context."""

    active_workflow = workflow or get_default_workflow()
    route: Route | None = None
    response: str | None = None
    with _observe_workflow_events(observer):
        with observe(
            name="multi-agent-workflow",
            as_type="agent",
            input={"user_query": input_state["user_query"]},
            error_stage="workflow",
        ) as observation:
            for update in active_workflow.stream(input_state, stream_mode="updates"):
                node_name, node_update = next(iter(update.items()))
                route = node_update.get("route", route)
                response = node_update.get("response", response)
                yield cast(dict[str, dict[str, Any]], {node_name: node_update})

            update_observation(
                observation,
                output={"route": route, "response": response},
            )


def main() -> None:
    """Minimal smoke entrypoint for local manual checks once deps are installed."""

    try:
        workflow = get_default_workflow()
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "langgraph"
        print(
            "No se pudo compilar el workflow porque falta la dependencia "
            f"'{missing_package}'."
        )
        return

    result = workflow.invoke({"user_query": "Consulta de ejemplo"})
    print(result)


if __name__ == "__main__":
    main()
