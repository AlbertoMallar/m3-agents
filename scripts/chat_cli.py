"""Interactive terminal demo for the existing M3 multi-agent workflow."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from langchain_core.documents import Document

from src.evaluation.evaluator import EvaluationResult, ResponseEvaluator
from src.multi_agent_system import WorkflowEvent, stream_workflow
from src.observability.langfuse import flush_langfuse

EXAMPLE_QUERIES = {
    "1": "Cuantos dias de vacaciones me corresponden?",
    "2": "No puedo conectarme a la VPN corporativa. Que debo hacer?",
    "3": "Como solicito el reintegro de un gasto?",
}
EXIT_COMMANDS = {"salir", "exit"}
HELP_COMMANDS = {"ayuda", "help"}
AGENT_NAMES = {
    "hr": "HRAgent",
    "tech": "TechAgent",
    "finance": "FinanceAgent",
}


@dataclass(frozen=True)
class InputResolution:
    """Normalized terminal input without invoking the workflow."""

    action: Literal["query", "exit", "help", "empty"]
    query: str | None = None


@dataclass
class WorkflowReport:
    """Observable data produced by one real workflow execution."""

    user_query: str
    route: str | None = None
    response: str | None = None
    nodes: list[str] = field(default_factory=list)
    chunk_references: list[dict[str, Any]] = field(default_factory=list)
    context_documents: list[Document] = field(default_factory=list)
    has_sufficient_context: bool | None = None


def parse_args() -> argparse.Namespace:
    """Parse optional display and evaluator flags."""

    parser = argparse.ArgumentParser(description="Interactive M3 workflow demo.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show observable workflow events and compact chunk references.",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run the evaluator after each answer (uses one additional model call).",
    )
    return parser.parse_args()


def resolve_input(raw_input: str) -> InputResolution:
    """Map examples and commands while preserving arbitrary user queries."""

    value = raw_input.strip()
    if not value:
        return InputResolution("empty")
    normalized = value.casefold()
    if normalized in EXIT_COMMANDS:
        return InputResolution("exit")
    if normalized in HELP_COMMANDS:
        return InputResolution("help")
    return InputResolution("query", EXAMPLE_QUERIES.get(value, value))


def show_menu() -> None:
    """Print a compact welcome and input guide."""

    print("=" * 50)
    print("M3 - Multi-Agent Support System")
    print("=" * 50)
    print("Consultas de ejemplo:")
    print("1. Recursos Humanos")
    print("2. Soporte Tecnico")
    print("3. Finanzas")
    print("Tambien podes escribir cualquier consulta libre.")
    print("Comandos: salir / exit, ayuda / help")


def show_help() -> None:
    """Print help without consuming any model calls."""

    print("1, 2 y 3 recorren el workflow completo con consultas representativas.")
    print("--verbose muestra eventos observables y referencias compactas de chunks.")
    print("--evaluate ejecuta el evaluator despues de la respuesta y consume un llamado extra.")


def collect_workflow_report(
    user_query: str,
    *,
    workflow_runner: Callable[..., Any] = stream_workflow,
) -> WorkflowReport:
    """Run the real workflow once and retain only safe, observable diagnostics."""

    report = WorkflowReport(user_query=user_query)

    def on_event(event: WorkflowEvent) -> None:
        data = event["data"]
        if event["name"] == "classification":
            report.route = data.get("route")
        elif event["name"] == "retrieval":
            report.chunk_references = list(data.get("chunk_references", []))
            report.context_documents = list(data.get("context_documents", []))
        elif event["name"] == "generation":
            report.has_sufficient_context = data.get("has_sufficient_context")

    for update in workflow_runner({"user_query": user_query}, observer=on_event):
        node_name, node_update = next(iter(update.items()))
        report.nodes.append(node_name)
        report.route = node_update.get("route", report.route)
        report.response = node_update.get("response", report.response)

    return report


def run_evaluation(
    report: WorkflowReport,
    *,
    evaluator_factory: Callable[[], Any] = ResponseEvaluator,
) -> EvaluationResult | None:
    """Optionally evaluate a completed response without blocking the CLI."""

    if not report.response:
        return None
    try:
        evaluator = evaluator_factory()
        return evaluator.evaluate_safely(
            user_query=report.user_query,
            final_response=report.response,
            context_documents=report.context_documents,
            domain=report.route,
        )
    except Exception:
        return None


def display_report(report: WorkflowReport, *, verbose: bool) -> None:
    """Render the workflow result without exposing prompts or document contents."""

    print("\n" + "-" * 50)
    print("[CONSULTA]")
    print(report.user_query)
    print("\n[ORCHESTRATOR]")
    print(f"Ruta seleccionada: {report.route or 'no disponible'}")
    print("\n[WORKFLOW]")
    if report.route in AGENT_NAMES:
        print(f"Agente ejecutado: {AGENT_NAMES[report.route]}")
    else:
        print("No se ejecuto un especialista RAG.")

    if report.route in AGENT_NAMES:
        print("\n[RETRIEVAL]")
        print(f"Chunks recuperados: {len(report.chunk_references)}")

    if report.has_sufficient_context is not None:
        print("\n[CONCLUSION]")
        if report.has_sufficient_context:
            print("Contexto interno suficiente: SI")
        else:
            print("Contexto interno suficiente: NO")
            print("El sistema respondio de forma segura sin evidencia interna suficiente.")

    if verbose:
        print("\n[STATE]")
        print(f"Nodos observados: {' -> '.join(report.nodes) or 'ninguno'}")
        print(f"route: {report.route or 'no disponible'}")
        print(f"response_ready: {'true' if bool(report.response) else 'false'}")
        if report.chunk_references:
            print("\n[CHUNKS]")
            for index, reference in enumerate(report.chunk_references, start=1):
                source = reference.get("source_name") or "fuente desconocida"
                section = reference.get("section_path") or "seccion sin metadata"
                print(f"{index}. {source} | {section}")

    print("\n[RESPUESTA]")
    print(report.response or "No se recibio una respuesta del workflow.")
    print("-" * 50)


def display_evaluation(result: EvaluationResult | None) -> None:
    """Render evaluator scores, keeping failures isolated from the main response."""

    print("\n[EVALUATION]")
    if result is None:
        print("No se pudo completar la evaluacion. La respuesta principal permanece valida.")
        return
    print(f"Relevance: {result.relevance}/10")
    print(f"Completeness: {result.completeness}/10")
    print(f"Accuracy: {result.accuracy}/10")
    print(f"Overall: {result.overall_score}/10")
    print(f"Reason: {result.reason}")


def main() -> None:
    """Start an input loop that keeps recoverable failures local to one query."""

    args = parse_args()
    show_menu()
    try:
        while True:
            try:
                resolution = resolve_input(input("\nUsuario > "))
            except EOFError:
                print("\nSesion finalizada.")
                break

            if resolution.action == "exit":
                print("Sesion finalizada.")
                break
            if resolution.action == "help":
                show_help()
                continue
            if resolution.action == "empty":
                print("Ingresá una consulta, 1, 2, 3, ayuda o salir.")
                continue

            try:
                report = collect_workflow_report(resolution.query or "")
                display_report(report, verbose=args.verbose)
                if args.evaluate:
                    display_evaluation(run_evaluation(report))
            except Exception as exc:
                print(
                    "No se pudo procesar la consulta "
                    f"({type(exc).__name__}). Revisá la configuracion y volvé a intentar."
                )
    except KeyboardInterrupt:
        print("\nSesion interrumpida.")
    finally:
        try:
            flush_langfuse()
        except Exception:
            pass


if __name__ == "__main__":
    main()
