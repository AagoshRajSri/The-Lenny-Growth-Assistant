# Architecture

## User & problem
[Placeholder]

## Success metric
[Placeholder]

## Assumptions
[Placeholder]

## Scope choices
- **Transcripts Data Source:** Since full transcripts are not strictly publicly available in the RSS feed by default, we use the RSS feed's `<description>`/`<content:encoded>` element as a proxy for the text content.
- **Chunking Strategy:** We chunk text into windows of 600 tokens with a 15% overlap using `tiktoken` (cl100k_base). 
- **Embeddings:** We use `sentence-transformers/all-MiniLM-L6-v2`. Given this model has a native limit (typically 256 or 512 tokens), it will truncate chunks longer than its limit. This trade-off is accepted for simplicity.

## Security Model
- **Artifact Sanitization:** To prevent Cross-Site Scripting (XSS), agent-generated HTML artifacts undergo strict server-side sanitization via `bleach` before persistence.
  - **Allowed:** Basic semantic HTML (e.g., `h1`-`h6`, `p`, `span`, `div`, `ul`, `ol`, `li`, `a`, `img`, `code`).
  - **Blocked:** Explicit blocking of `<script>`, `<iframe>`, `<object>`, `<embed>`, inline event handlers (like `onerror`), and `javascript:` URIs.
  - **Serving:** The API (`/api/artifacts/{id}`) exclusively returns `sanitized_content`. The raw content is kept for auditing and re-processing but never served directly to frontend clients.

## Risks & trade-offs
[Placeholder]

## Flows
- **Ingestion Pipeline:**
  1. A script fetches the latest ~25 episodes from `https://www.lennysnewsletter.com/feed`.
  2. HTML is stripped, and the metadata + text is saved locally in JSON files.
  3. `ingestion/ingest.py` discovers these files, checks the database for idempotency against the `episode_url`, and skips existing records unless `--refresh` is passed.
  4. Records are chunked, embedded in batches via `all-MiniLM-L6-v2`, and upserted into PostgreSQL using SQLAlchemy.

## Acceptance criteria
[Placeholder]
