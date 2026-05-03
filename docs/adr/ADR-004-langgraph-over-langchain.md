# ADR-004: LangGraph over raw LangChain chains

**Date:** 2026-05-01
**Status:** Validated

## Context

The query flow requires an agent that can:
1. Receive a question
2. Decide which tool to call (retrieve, web search, or clarify)
3. Inspect the tool result and decide whether to call another tool or generate a final answer
4. Loop if the retrieved context is insufficient

Options considered:

| Option | Loop support | State | Tool calling |
|--------|-------------|-------|-------------|
| **LangGraph** `create_react_agent` | Yes — cyclical graph | Persistent across steps | Native |
| **LangChain** | No — linear pipeline | Stateless between steps | Via `AgentExecutor` (deprecated direction) |
| **LlamaIndex** | Yes | Yes | Yes |
| **Hand-rolled ReAct loop** | Yes | Manual | Manual |

LangChain LCEL chains are linear: input flows through steps and exits. They cannot natively branch or loop based on intermediate results. `AgentExecutor` added looping on top of chains but is now superseded by LangGraph in LangChain's own roadmap.

LlamaIndex is a valid alternative but introduces a second framework alongside LangChain, which is already required for the LLM/embedding abstractions (`ChatOllama`, `ChatOpenAI`, `OllamaEmbeddings`) and mixing frameworks adds complexity.

A hand-rolled ReAct loop gives full control but requires re-implementing tool dispatch, memory management, and termination logic — all of which LangGraph provides.

## Decision

Use LangGraph's `create_react_agent`:

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=get_chat_model(),
    tools=[make_retrieve_tool(user_id, db), web_search_tool, clarify_tool],
    prompt=SYSTEM_PROMPT
)
```

Set `max_iterations` on the agent to prevent infinite loops (default guard is 10 steps).

## Consequences

- Agent can loop: retrieve → inspect → retrieve again if context is thin, then generate
- Tool call trace is available in the execution graph — sources are extracted from `retrieve_tool` call records, not parsed from LLM output. This prevents citation hallucination.
- LangGraph is more complex to debug than a linear chain — the execution graph must be inspected to trace what happened
- `max_iterations` guard prevents runaway loops at the cost of potentially incomplete answers on very complex queries — acceptable for v1
- Stateful graphs open the door to multi-turn conversation with memory in v2 without changing the agent architecture
