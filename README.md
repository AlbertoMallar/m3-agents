# Proyecto Integrador M3

## Problema

Sistema interno de soporte que clasifica consultas y responde con documentacion
interna ficticia de una empresa SaaS. Los dominios soportados son Recursos Humanos
(HR), Tecnologia (Tech) y Finanzas (Finance).

## Arquitectura

```text
Usuario
  -> Orchestrator (structured output)
  -> routing condicional de LangGraph
  -> HR RAG | Tech RAG | Finance RAG | out_of_scope
  -> respuesta final
```

El orchestrator solo clasifica una consulta en `hr`, `tech`, `finance` u
`out_of_scope`. Cada especialista recupera primero documentos de su propio dominio
y genera respuestas basadas exclusivamente en ese contexto.

- LangChain: prompts, modelos OpenAI, `Document` y splitters.
- LangGraph: estado tipado, nodos y routing condicional.
- OpenAI: chat model y embeddings.
- Chroma: vector stores locales persistidos por dominio.
- Langfuse: traces de workflow, routing, retrieval, generacion y evaluator.

## Estructura del proyecto

```text
data/
  hr_docs/hr_knowledge_base.md
  tech_docs/tech_knowledge_base.md
  finance_docs/finance_knowledge_base.md
scripts/
  run_mvp_tests.py
src/
  agents/                 # Orchestrator y especialistas HR, Tech y Finance
  evaluation/evaluator.py # Bonus: evaluator opcional con structured output
  knowledge/              # Chunking, Chroma y retrievers por dominio
  observability/langfuse.py
  multi_agent_system.py   # Topologia y entradas trazadas del workflow
test_queries.json
```

## Instalacion

1. Crear y activar un entorno virtual.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias.

```powershell
python -m pip install -r requirements.txt
```

3. Crear `.env` a partir de `.env.example` y configurar las variables.

```env
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

Langfuse es opcional para ejecucion local: si las tres variables `LANGFUSE_*` no
estan presentes, la instrumentacion funciona en modo no-op. Una configuracion
parcial genera un error explicito. `LANGFUSE_HOST` debe corresponder a la region
del proyecto de Langfuse; este proyecto fue validado con
`https://hipaa.cloud.langfuse.com`.

## Ejecucion

El entry point minimo compila e invoca el workflow:

```powershell
python -m src.multi_agent_system
```

Para usar el flujo trazado desde Python, importar `invoke_workflow` o
`stream_workflow` desde `src.multi_agent_system`.

## Tests

La suite reproducible ejecuta 12 consultas end-to-end:

```powershell
python scripts\run_mvp_tests.py
```

Ultima ejecucion verificada: `12/12` rutas correctas, accuracy de routing `1.00`.
Los casos cubren HR, Tech, Finance, out-of-scope, una consulta ambigua y un caso
sin evidencia suficiente.

## Knowledge Bases y RAG

Cada dominio tiene un documento Markdown principal. El proceso conserva metadata
de encabezados con `MarkdownHeaderTextSplitter` y subdivide secciones con
`RecursiveCharacterTextSplitter` (`chunk_size=800`, `chunk_overlap=120`).

- HR: 119 chunks.
- Tech: 53 chunks.
- Finance: 52 chunks.

Los retrievers usan `OpenAIEmbeddings`, Chroma persistido y `k=4` por defecto.
Los indices se crean en `data/vector_stores/`, pero no se versionan: se pueden
reconstruir automaticamente desde las knowledge bases y las credenciales OpenAI.

## Orchestrator

`OrchestratorAgent` usa structured output para devolver exactamente una ruta:
`hr`, `tech`, `finance` u `out_of_scope`. Las consultas mixtas sin un dominio
principal claro y las consultas ajenas al soporte interno usan el fallback
`out_of_scope`.

## Langfuse

Con credenciales validas, cada ejecucion trazada registra:

- `multi-agent-workflow` con query, route y respuesta final.
- `orchestrator-classification` con modelo y ruta elegida.
- Agente especializado, retrieval y generation del dominio seleccionado.
- Referencias seguras de chunks: fuente, seccion, indice y tamano; no el texto
  completo de la knowledge base.
- Errores con etapa, tipo y mensaje saneado.

Los scripts cortos hacen `flush()` antes de finalizar.

## Evaluator

El bonus `ResponseEvaluator` evalua de forma aislada una respuesta con structured
output: `relevance`, `completeness`, `accuracy`, `overall_score` (1 a 10) y
`reason`. Puede usar los documentos recuperados como evidencia y registra los
scores en Langfuse. No forma parte del handler del workflow, por lo que una falla
del evaluator no bloquea la respuesta principal.

## Decisiones tecnicas

- LangGraph implementa el workflow mediante un estado tipado, nodos y routing
  condicional.
- LangChain aporta componentes LLM y RAG sin APIs deprecadas.
- Structured output evita parsing fragil para routing y evaluacion.
- Chroma local mantiene un vector store por dominio.
- Retrieval permanece separado de generation y de la topologia del grafo.
- Cada especialista solo usa su propia knowledge base.

## Limitaciones

- Una consulta se asigna a un unico dominio; no hay multi-intent ni handoffs.
- No hay routing paralelo ni reranking.
- Si cambia una knowledge base, el indice local debe reconstruirse.
- El sistema depende de OpenAI para embeddings, clasificacion, respuestas y
  evaluator.
- Langfuse es opcional en local, pero necesario para observabilidad Cloud.

## Próximas mejoras

La mejora principal propuesta es una interfaz interactiva de consola para
demostrar, probar manualmente y observar el workflow actual sin alterar su
comportamiento ni realizar llamadas adicionales al LLM solo para explicarlo.

- Permitir consultas libres y reutilizar el workflow multiagente existente.
- Mostrar la clasificación del Orchestrator, el agente seleccionado y las
  actualizaciones relevantes del estado.
- Indicar cuándo se ejecuta retrieval, cuántos chunks se recuperan y su metadata
  útil, sin imprimir el contexto completo.
- Presentar la respuesta final e indicar si el especialista encontró contexto
  interno suficiente para responder.

Como extensiones posteriores, se podrían incorporar multi-intent, handoffs,
reranking y evaluaciones de regresión más amplias.
