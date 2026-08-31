"""Offline unit tests for the interactive CLI presentation layer."""

from __future__ import annotations

import unittest

from scripts import chat_cli
from src.evaluation.evaluator import EvaluationResult


def fake_workflow_runner(input_state, *, observer):
    """Yield observable workflow updates without OpenAI, Chroma, or Langfuse."""

    observer({"name": "classification", "data": {"route": "hr"}})
    yield {"orchestrator": {"route": "hr"}}
    observer(
        {
            "name": "retrieval",
            "data": {
                "chunk_references": [{"source_name": "hr.md", "section_path": "Vacaciones"}],
                "context_documents": [],
            },
        }
    )
    observer(
        {
            "name": "generation",
            "data": {"has_sufficient_context": True, "response_ready": True},
        }
    )
    yield {"hr": {"response": "Respuesta de prueba."}}


class FakeEvaluator:
    calls = 0

    def evaluate_safely(self, **_kwargs):
        self.__class__.calls += 1
        return EvaluationResult(
            relevance=9,
            completeness=8,
            accuracy=9,
            overall_score=9,
            reason="Respuesta respaldada por el contexto mock.",
        )


class FailingEvaluator:
    def evaluate_safely(self, **_kwargs):
        raise RuntimeError("evaluator failure")


class ChatCliTests(unittest.TestCase):
    def test_example_options_map_to_real_domain_queries(self) -> None:
        self.assertIn("vacaciones", chat_cli.resolve_input("1").query.casefold())
        self.assertIn("vpn", chat_cli.resolve_input("2").query.casefold())
        self.assertIn("reintegro", chat_cli.resolve_input("3").query.casefold())

    def test_free_query_is_preserved(self) -> None:
        query = "Cambie de celular y no puedo usar MFA"
        self.assertEqual(chat_cli.resolve_input(query).query, query)

    def test_exit_and_empty_input_are_handled(self) -> None:
        self.assertEqual(chat_cli.resolve_input("salir").action, "exit")
        self.assertEqual(chat_cli.resolve_input("   ").action, "empty")

    def test_normal_execution_does_not_run_evaluator(self) -> None:
        FakeEvaluator.calls = 0
        report = chat_cli.collect_workflow_report("consulta", workflow_runner=fake_workflow_runner)
        self.assertEqual(FakeEvaluator.calls, 0)
        self.assertEqual(report.route, "hr")
        self.assertTrue(report.has_sufficient_context)

    def test_evaluate_runs_the_optional_evaluator(self) -> None:
        FakeEvaluator.calls = 0
        report = chat_cli.collect_workflow_report("consulta", workflow_runner=fake_workflow_runner)
        result = chat_cli.run_evaluation(report, evaluator_factory=FakeEvaluator)
        self.assertEqual(FakeEvaluator.calls, 1)
        self.assertIsNotNone(result)
        self.assertEqual(result.overall_score, 9)

    def test_evaluator_error_keeps_the_main_report(self) -> None:
        report = chat_cli.collect_workflow_report("consulta", workflow_runner=fake_workflow_runner)
        self.assertIsNone(chat_cli.run_evaluation(report, evaluator_factory=FailingEvaluator))
        self.assertEqual(report.response, "Respuesta de prueba.")


if __name__ == "__main__":
    unittest.main()
