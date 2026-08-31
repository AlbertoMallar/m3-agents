# AGENTS.md

## Project
AI Engineering M3 – Multi-Agent Support System.

The system will contain:
- one orchestrator agent;
- specialized RAG agents for HR, Tech and Finance;
- conditional routing;
- LangChain / LangGraph orchestration;
- Langfuse tracing;
- test queries and evaluation.

## Working style
- Work incrementally, one responsibility at a time.
- Do not implement future parts unless explicitly requested.
- Preserve the existing architecture unless a change is necessary and justified.
- Prefer simple, modular and testable code.
- Keep responsibilities separated across modules.
- Reuse existing code instead of duplicating logic.

## Libraries and APIs
- Use current recommended APIs from LangChain and LangGraph.
- Avoid deprecated APIs such as old `LLMChain`, `RetrievalQA`, `initialize_agent`, `.run()`, etc., unless explicitly requested.
- Use `langchain-openai` integrations for OpenAI models.
- Never hard-code API keys or secrets.
- Load configuration from environment variables.

## Architecture
Expected high-level flow:

User query
→ Orchestrator
→ conditional routing
→ HR / Tech / Finance specialized agent
→ RAG retrieval
→ grounded response
→ Langfuse tracing

The orchestrator should classify and route; it should not contain domain knowledge.

Each specialized agent should only handle its own domain.

## State and contracts
- Use explicit, typed state/contracts where appropriate.
- Keep field names consistent across modules.
- Prefer structured outputs for routing decisions instead of fragile free-text parsing.
- Validate outputs before using them for routing.

## RAG
- Each domain must have its own knowledge base/retriever.
- Retrieval logic must remain separate from orchestration logic.
- Responses should be grounded in retrieved company documentation.
- Do not invent information when retrieval does not provide enough evidence.

## Testing
- Test components independently before end-to-end integration.
- Routing tests must cover HR, Tech, Finance, ambiguous and out-of-scope queries.
- After modifying code, run the relevant tests or execution checks when possible.

## Code changes
For each requested change:
1. inspect the relevant existing files;
2. implement only the requested scope;
3. avoid unrelated refactors;
4. briefly summarize what changed;
5. mention any important assumptions, risks or deprecated code found.

## Current development approach
We are intentionally building the project in stages:

1. basic state and multi-agent routing;
2. mock specialized agents;
3. test routing;
4. domain documents and vector stores;
5. specialized RAG agents;
6. full integration;
7. Langfuse observability;
8. evaluator bonus.

Do not skip ahead unless explicitly asked.