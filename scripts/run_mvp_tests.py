"""Run the MVP end-to-end checks defined in ``test_queries.json``."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TypedDict

REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_QUERIES_PATH = REPO_ROOT / "test_queries.json"
SAFE_RESPONSE_MARKERS = ("no hay", "insuficiente", "no se encontro")
sys.path.insert(0, str(REPO_ROOT))

from src.multi_agent_system import stream_workflow
from src.observability.langfuse import flush_langfuse


class TestQuery(TypedDict):
    """Minimal contract for each manual MVP test case."""

    id: str
    domain: str
    query: str
    expects_safe_response: bool


def load_test_queries() -> list[TestQuery]:
    """Load the test cases from the project JSON file."""

    raw_queries = json.loads(TEST_QUERIES_PATH.read_text(encoding="utf-8"))
    return [
        {
            "id": item["id"],
            "domain": item["domain"],
            "query": item["query"],
            "expects_safe_response": item.get("expects_safe_response", False),
        }
        for item in raw_queries
    ]


def run_mvp_tests() -> list[dict[str, object]]:
    """Execute every case and return simple, serializable validation results."""

    results: list[dict[str, object]] = []
    try:
        for case in load_test_queries():
            route: str | None = None
            response: str | None = None
            nodes: list[str] = []
            for update in stream_workflow({"user_query": case["query"]}):
                node_name, node_update = next(iter(update.items()))
                nodes.append(node_name)
                route = node_update.get("route", route)
                response = node_update.get("response", response)

            expected_node = case["domain"]
            normalized_response = response.lower() if response else ""
            safe_response_ok = not case["expects_safe_response"] or (
                "contexto interno" in normalized_response
                and any(marker in normalized_response for marker in SAFE_RESPONSE_MARKERS)
            )
            passed = (
                route == case["domain"]
                and bool(nodes and nodes[-1] == expected_node)
                and bool(response and response.strip())
                and safe_response_ok
            )
            results.append(
                {
                    "id": case["id"],
                    "expected_route": case["domain"],
                    "obtained_route": route,
                    "route_correct": route == case["domain"],
                    "executed_node": nodes[-1] if nodes else None,
                    "node_correct": bool(nodes and nodes[-1] == expected_node),
                    "has_response": bool(response and response.strip()),
                    "safe_response_ok": safe_response_ok,
                    "final_response": response,
                    "status": "PASS" if passed else "FAIL",
                }
            )
    finally:
        flush_langfuse()

    return results


def main() -> None:
    """Print results and basic routing accuracy for local reproducible checks."""

    results = run_mvp_tests()
    correct_routes = sum(result["route_correct"] for result in results)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"routing_accuracy={correct_routes}/{len(results)}")


if __name__ == "__main__":
    main()
