# PRD: Lenny Growth Assistant

## User & problem
Growth PMs, marketing leaders, and founders need a fast, authoritative research tool to query the extensive corpus of Lenny's Podcast and Newsletter. Currently, finding specific frameworks (e.g., "how did Airbnb measure retention?") requires manual searching across hours of audio or reading dozens of long-form newsletters. They need a tool that provides immediate, cited answers without hallucinating general web knowledge.

## Success metrics
1. **Accuracy (0 Hallucinations):** The assistant must explicitly refuse to answer questions outside the provided corpus ("Out of corpus"). 
2. **Speed:** Time-to-first-token (TTFT) under 1.5s to ensure a snappy user experience.
3. **Citations:** 100% of generated claims must include a verifiable episode title and URL.
4. **Resilience:** Zero dropped requests due to transient database or LLM provider timeouts (must degrade gracefully with JSON errors).

## Assumptions
- We have legal/ethical clearance to ingest and RAG over the public/freely available RSS feed summaries and texts.
- Users prefer high accuracy and slightly higher latency over fast, hallucinated answers.
- Modern browsers support SSE (Server-Sent Events) for token streaming.

## Scope choices
- **In Scope:** 
  - Dual LLM support (Anthropic Claude via SDK, and local Ollama via raw HTTP).
  - Semantic search via `pgvector` and `sentence-transformers`.
  - Artifact generation (Markdown/HTML) safely rendered in a sandboxed iframe.
  - Streaming UI with a deep-slate, technical aesthetic.
- **Deliberate Cuts (Phase 0):**
  - User authentication/login (Single-tenant by default).
  - Chat history persistence across browser restarts (history is kept in DB but not mapped to a persistent user account yet).
  - Hybrid search (BM25 keyword search is cut; relying entirely on vector cosine similarity).
  - Complex conversation branching/editing past messages.

## Risks & mitigations
- **Hallucination:** 
  - *Mitigation:* Strict system prompts, explicit "Out of Corpus" override if retrieval yields no chunks, and required inline citations.
- **Latency:** 
  - *Mitigation:* Streaming tokens via SSE to maintain user engagement. Chunk size kept at 500-800 tokens to limit context window size.
- **Cost:**
  - *Mitigation:* Support for local Ollama (`llama3.2:3b`) allows for zero-cost local development and inference.
- **Artifact Security (XSS):**
  - *Mitigation:* Strict server-side HTML sanitization using `bleach`. The frontend renders artifacts in an `<iframe sandbox="allow-same-origin">` (stripping `allow-scripts`) protected by a strict Content Security Policy.

## Flows
1. **Session Creation:** User clicks "New Chat", frontend posts to `/api/sessions`, returning a unique Session ID.
2. **Chat Interaction:** User sends a query. Backend embeds the query, searches `pgvector`, builds the prompt, and streams tokens back via SSE.
3. **Artifact Generation:** If the LLM generates a long-form document, it uses the `render_artifact` tool. The backend sanitizes it and returns an artifact ID. The frontend detects the ID and opens a split-pane viewer.
4. **Resilience Flow:** If the database disconnects, the backend retries once. If it fails again, it returns a 503 error envelope. The frontend displays this in a dismissable error bar instead of crashing.

## Acceptance criteria
- [x] RAG correctly retrieves top K chunks based on semantic similarity.
- [x] UI streams responses token-by-token.
- [x] UI displays HTML/Markdown artifacts in a sandboxed iframe.
- [x] Application successfully runs entirely locally using Docker Compose and Ollama.
- [x] System gracefully handles missing LLM API keys and disconnected databases.
