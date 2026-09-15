# Manual Test Plan (Phase 11)

This checklist covers edge cases and visual UI states that are not fully captured by automated backend tests.

## 1. Streaming Cursor & Network Resilience
- [ ] Create a new session and send a message.
- [ ] Observe the streaming cursor `|` blinking while the response is streaming.
- [ ] Observe the cursor disappears immediately when the stream completes.
- [ ] Force a network interruption (e.g., stop the Ollama service mid-stream). Verify the UI gracefully displays an error alert bar instead of hanging indefinitely.

## 2. Artifact Viewer & Sandbox
- [ ] Trigger an artifact generation (e.g., ask to "Write a Ship 30 essay").
- [ ] Verify the artifact viewer automatically slides out from the right.
- [ ] Click the "Raw Source" toggle. Verify the raw markdown/HTML is visible in a `<pre>` block.
- [ ] Click "Rendered". Verify HTML artifacts load inside an `<iframe>` and markdown artifacts render directly.
- [ ] Inspect the DOM to confirm the `<iframe>` has `sandbox="allow-same-origin"` and no `allow-scripts`.

## 3. Provider State Sync
- [ ] Stop the Ollama daemon.
- [ ] Refresh the page. Verify the provider badge says `ollama` but is marked degraded/unreachable (or falls back appropriately based on your config).
- [ ] Switch the `.env` `LLM_PROVIDER` to `anthropic`. Restart the backend.
- [ ] Refresh the page. Verify the provider badge immediately reflects `anthropic · claude`.

## 4. Sidebar & Layout Toggle
- [ ] Shrink the window width to simulate a mobile viewport.
- [ ] Verify the sidebar is hidden or can be toggled via the hamburger menu `☰`.
- [ ] Create a new chat. Verify it immediately appears at the top of the sidebar session list.
- [ ] Select an older session. Verify the background color highlights the active session (`accent-subtle`).
