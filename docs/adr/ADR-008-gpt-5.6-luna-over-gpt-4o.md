# ADR-008: GPT-5.6 Luna over GPT-4o for the OpenAI provider

**Date:** 2026-08-28
**Status:** Accepted

## Context

`get_chat_model()` in `app/services/llm.py` hardcodes the OpenAI model used by `create_agent` (the LangGraph agent with `retrieve`, `clarify`, and `web_search` tools) when `LLM_PROVIDER=openai`. It was set to `gpt-4o`, which was OpenAI's flagship model at the time this project started but is no longer OpenAI's current recommendation; it is kept available mainly for backward compatibility.

OpenAI's current lineup (as of August 2026) is the GPT-5.6 family, released in three tiers: Sol, Terra, and Luna, from most to least capable, with pricing scaled to match. Per-1M-token pricing:

| Model | Input | Output |
|---|---|---|
| GPT-4o | $2.50 | $10.00 |
| GPT-5.6 Sol | $5.00 | $30.00 |
| GPT-5.6 Terra | $2.00 | $12.00 |
| GPT-5.6 Luna | $0.20 | $1.20 |

Luna is roughly 12x cheaper on input and 8x cheaper on output than `gpt-4o`. Unlike a typical cheap/small model tradeoff, Luna isn't far behind on capability: on the Artificial Analysis Coding Agent Index, Sol scores 80, Terra 77.4, Luna 74.6, a 2.4-point gap between the frontier tier and the budget tier. All three GPT-5.6 tiers, including Luna, support Programmatic Tool Calling (the model writes and runs its own orchestration code for tool calls), which is directly relevant here since the agent's usefulness depends on reliable tool-calling across `retrieve`/`clarify`/`web_search`.

Given this project runs on-demand rather than continuously (see [ADR-007](ADR-007-on-demand-infrastructure-lifecycle.md)), LLM cost during any given demo session is small regardless of model choice, so this decision is driven primarily by "use OpenAI's current recommended model" rather than by a pressing cost problem. It also happens to be markedly cheaper.

## Decision

Switch the hardcoded model in `get_chat_model()` from `gpt-4o` to `gpt-5.6-luna`.

This was not benchmarked against this project's actual agent and tool set before switching; the decision rests on published third-party benchmarks (Artificial Analysis) and OpenAI's own pricing/capability positioning, not on an internal evaluation harness (there isn't one, per the project's known gaps). The agent's tool-calling behavior with Luna should be manually verified against a live query before this is relied on for a demo.

## Consequences

- OpenAI-provider queries cost substantially less per token.
- The agent now depends on a specific OpenAI model tier (Luna) whose real-world tool-calling reliability for this project's exact tool set (`retrieve`, `clarify`, `web_search`) has not been directly tested as of this ADR, only inferred from published benchmarks. If Luna underperforms in practice, Terra is the documented fallback at roughly the same capability tier as `gpt-4o` (Terra $2/$12 vs GPT-4o $2.50/$10) rather than reverting to `gpt-4o` outright.
- `LLM_PROVIDER=ollama` (the local/free path) is unaffected; this only changes the OpenAI branch.
- No evaluation harness exists to catch a quality regression automatically; manual verification is the only current safeguard (a known gap, consistent with what's already unbuilt in this project).
