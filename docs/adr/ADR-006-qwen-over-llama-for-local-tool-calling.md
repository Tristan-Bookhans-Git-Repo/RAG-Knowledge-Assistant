# ADR-006: qwen2.5:7b over llama3.2 as the default local chat model

**Date:** 2026-07-18
**Status:** Validated

## Context

The agent (`app/services/agent.py`) depends entirely on structured tool calling: `create_agent` binds `retrieve`, `web_search_tool`, and `clarify_tool` to the chat model via `bind_tools()`, and routes on `AIMessage.tool_calls`. If the model never populates `tool_calls`, the graph treats whatever text it produced as a final answer and terminates — `retrieve` never runs, so `sources` is always `[]`, regardless of how well `retrieve_tool.py`, `query_service.py`, or the graph itself are implemented.

`llama3.2` (the 3.2B, Q4_K_M-quantized default pulled by `make pull-models`) was the original default `OLLAMA_CHAT_MODEL`. In production use, every query against a real uploaded document returned an empty `sources` list and an answer along the lines of *"I don't have any information about that."*

Isolated reproduction — binding `retrieve` directly to `ChatOllama(model="llama3.2")` with the same system prompt used in `agent.py`:

```python
model_with_tools = ChatOllama(model="llama3.2").bind_tools([retrieve])
response = model_with_tools.invoke([...])

response.content     # '{"name": "Search", "parameters": {"query": "mascot name"}}'
response.tool_calls   # []
```

The model attempts a tool call, but writes it out as plain text instead of using Ollama's structured tool-calling response format — and even gets the tool name wrong ("Search" vs the actual `retrieve`). `response.tool_calls` comes back empty either way, which is all `create_agent`'s router checks. This reproduced with 100% consistency across multiple questions and phrasings — it is a model capability limitation, not a prompting issue or a one-off flake.

The same test against `qwen2.5:7b`:

```python
response.content      # ''
response.tool_calls    # [{'name': 'retrieve', 'args': {'query': 'mascot name'}, 'id': '...', 'type': 'tool_call'}]
```

Correct tool name, correct args, populated in the field LangChain/LangGraph actually reads. An end-to-end run (upload a `.txt` fixture → ask a question about its content) returned a grounded answer with the correct source cited.

## Decision

Set `qwen2.5:7b` as the default `OLLAMA_CHAT_MODEL` — in `app/config.py`, `.env`, `.env.example`, and `Makefile`'s `pull-models` target.

`llama3.2` remains usable by overriding `OLLAMA_CHAT_MODEL` in `.env`, but is no longer the default since it silently breaks the core retrieval feature.

## Consequences

- `qwen2.5:7b` is a larger download (~4.7GB vs ~2GB) and a larger model to run locally — slower inference on constrained hardware
- The one integration test suite that exercises tool-calling behavior against a real LLM would have caught this regression, but `tests/integration/test_query.py` deliberately mocks the LLM (`_FakeRAGModel`) per `CONTRIBUTING.md`'s "do not call real Ollama in integration tests" rule — so a model-capability regression like this is invisible to CI and only surfaces in manual end-to-end use. This is an accepted gap: pinning CI to real local-model output would make tests slow, flaky, and hardware-dependent.
- Any future change to `OLLAMA_CHAT_MODEL` should be spot-checked the same way this was diagnosed: bind a real tool and inspect `response.tool_calls` directly, not just eyeball an answer's plausibility.
