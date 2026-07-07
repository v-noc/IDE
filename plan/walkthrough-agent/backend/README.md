# Walkthrough Backend — MVP Plan

> How the walkthrough agent lands in the existing FastAPI backend: what we reuse, the
> LLM provider layer (**configurable: OpenAI, Vercel AI Gateway, any OpenAI-compatible
> endpoint — hardcoded in settings for now**), routes, persistence, and testing.

Parent plan: [`plan/walkthrough-agent/`](../README.md). Traversal rules (03), types
(04), the LangGraph pipeline (05), context (06), and prompts (07) are specified there —
this folder is about **wiring them into the real backend**, and does not repeat them.
Sibling: [`frontend/`](../frontend/README.md).

## MVP stance (read this first)

1. **Four new dependencies**: `langchain`, `langchain-openai`, `langgraph`,
   `jsonpatch`. Nothing else — FastAPI, pydantic(-settings), TerminusDB client,
   loguru, orjson are already in the project.
2. **One provider class, many providers.** OpenAI, Vercel AI Gateway, GLM/Kimi direct
   endpoints, OpenRouter, and local servers are all OpenAI-compatible. The provider
   layer is a **registry of base URLs + keys**, not an abstraction over N SDKs.
   Selection is a settings value (env/hardcoded default) — no UI, no per-request
   override in MVP, but the seam for both is left.
3. **A `fake` provider ships in the registry.** It returns canned structured outputs
   with zero network calls — the backend equivalent of the frontend's mock mode. The
   whole pipeline runs and is tested without an API key.
4. **Feature-folder isolation.** Everything walkthrough lives in `app/walkthrough/`;
   the only shared new code is the provider layer, which goes in the reserved (and
   currently empty) `app/agent/llm/` so the future chat agent inherits it.
5. **Reuse the data layer.** Traversal and context builders call the same
   repositories/services that `/read-code/`, `/descendants`, and `/lineage` already
   use. No new graph queries are invented for MVP.

## Files

| # | File | Answers |
|---|------|---------|
| 00 | [00-scope.md](00-scope.md) | What MVP builds, reuses, and skips; the dependency list. |
| 01 | [01-folder-structure.md](01-folder-structure.md) | Where every file goes; house-style conventions followed. |
| 02 | [02-llm-provider.md](02-llm-provider.md) | The provider registry: OpenAI / Vercel / custom / fake, config, structured-output helper. |
| 03 | [03-routes-and-service.md](03-routes-and-service.md) | Endpoints, session lifecycle, patcher + NDJSON transport, abort. |
| 04 | [04-persistence.md](04-persistence.md) | TerminusDB schema, commit pinning, incremental writes, replay reads. |
| 05 | [05-testing.md](05-testing.md) | Fake-provider tests, validator tests, the CLI harness, fixture recording. |
| 06 | [06-build-order.md](06-build-order.md) | Build sequence; each stage runnable, most without an API key. |
