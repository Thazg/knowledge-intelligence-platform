# Enterprise KIP Web Demo

This folder contains the web interface for Enterprise KIP.

The page makes the RAG project easier to try without going through Swagger. It places the seven indexed documentation sets before the question form, offers example questions and a labeled sample answer, streams markdown-formatted answers from the existing backend, and displays cited evidence with links to upstream documentation when available.

Live demo:

https://enterprisekip.vercel.app

## How it works

The frontend is built with Next.js.

The browser sends requests through a Next.js API route instead of calling the Render backend directly:

```text
Browser
  ↓
Next.js /api/query/stream
  ↓
FastAPI /v1/query/stream
  ↓
RAGService / RAGPipeline
```

The existing Enterprise KIP retrieval and generation pipeline is reused as-is.

The UI is a focused RAG demo, not an account-based chat product. Up to 8 recent questions are saved in the browser's `localStorage` (`ekip-recent-queries`), deduplicated and clearable anytime. **Submitting a question sends that question to the API**; the browser history itself is not uploaded as a separate dataset.

## Interface

The sticky header shows the project identity and links to GitHub and API documentation. The hero sketches the five-stage path: query → hybrid retrieval → evidence selection → grounded generation → citations. **Indexed scope** lists Docker, FastAPI, Hugging Face Transformers, Kubernetes, LangChain, LangGraph, and Qdrant before the form. The demo does not search the open web.

The example questions fill the form without auto-submitting. A separate Docker BuildKit answer is condensed from a local run and links to two original documents; its wording is a preview, not the result of a live request. The evidence panel reports the **cloud retrieval profile** on 100 verified queries (Hit@10 **0.9300**, MRR **0.7119**) and links to the [benchmark](../benchmarks/retrieval/reports/cloud-hybrid-v1.md). These retrieval scores are not answer-quality scores. The separate [E2E review](../benchmarks/e2e/reports/e2e_v1_decision.md) records that structural checks passed while the semantic release gate did not.

Query form:

- Technical question textarea, capped at 1,024 characters to match the backend (`max_length=1024`), with a live `x/1024` counter and a Clear button.
- `Enter` submits, `Shift` + `Enter` inserts a newline.
- Up to 8 recent questions are remembered locally; clicking one fills the input (it does not auto-submit). History never touches the server.

Answer rendering:

- Answers stream in token-by-token with a typing caret and skeleton shimmer while waiting.
- A small safe markdown renderer (`lib/markdown.tsx`, no HTML passthrough) supports bold, inline code, fenced code blocks, lists, headings, quotes, and `http(s)` links. Unsafe URLs (`javascript:`, `data:`) render as plain text.
- `[N]` citations render as buttons: clicking one scrolls to the matching source card and flashes it for ~1.6s.
- A Copy button copies the plain answer text via the clipboard.

Sources:

- Only sources actually cited in the answer are shown (uncited or malformed entries are dropped), with an `N cited` counter.
- Each card shows the source label, title, an excerpt (≤500 characters, cleaned of HTML comments and code-fence markers by the backend), collapsible document/chunk identifiers, and an `Open source` link only for safe `http(s)` URLs with `noopener`. Links identify current upstream documentation paths, not immutable revisions of the indexed corpus; see [citation provenance](../docs/07_citation_provenance.md).

Status and errors:

- A status pill and animated progress track show the live phase: `idle → connecting → retrieving → generating → complete`.
- A cold-start notice appears if the first event takes longer than ~6.5s (Render free-tier wake-up).
- Failures show an error card with a Retry button; stream errors arrive as `error` events without leaking internals.

## Local development

Requirements:

- Node.js 20.9+
- An available Enterprise KIP backend (the example environment points to the public API)

If you want to use your own local backend, follow the [deployment runbook](../docs/05_deployment_runbook.md) to configure its corpus, Qdrant, and generator, then start the API from the repository root:

```bash
python -m uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Then start the frontend:

```bash
cd web
npm ci
```

Copy the environment file:

```bash
cp .env.example .env.local
```

On PowerShell:

```powershell
Copy-Item .env.example .env.local
```

For a local backend, set:

```ini
ENTERPRISE_KIP_API_BASE_URL=http://localhost:8000
```

Then run:

```bash
npm run dev
```

Open:

http://localhost:3000

If you want to use the public backend instead, keep the API URL from `.env.example`. `ENTERPRISE_KIP_API_BASE_URL` is read server-side by the Next.js proxy; it is not a browser-exposed `NEXT_PUBLIC_` variable.

## Streaming

The frontend uses:

```text
POST /v1/query/stream
```

The backend returns Server-Sent Events while a query is processed. Statuses observed by the UI are `idle`, `connecting` (transient, client-side), `retrieving`, `generating`, and `complete`.

A normal request looks roughly like this:

```text
status        retrieving
status        generating
answer_delta  ...
citations     ...
done
error         ...         (only if the stream fails mid-way)
```

The final citation event uses the source information returned by the existing RAG pipeline, filtered to cited, well-formed entries.

If something fails after the stream has started, the backend sends an error event instead of exposing the internal exception.

The stream only contains answer text, source information, and basic request status. Model reasoning is not exposed.

The Next.js proxy validates before forwarding:

```text
400   unreadable body or invalid JSON
413   body larger than 8,192 characters
422   query missing or outside 1–1,024 characters
500   backend URL not configured
502   backend unreachable or empty stream
```

Upstream backend errors keep their status code with a normalized message. The proxy allows up to 180 seconds per request (`maxDuration`).

## Checks

From the `web` directory:

```bash
npm run lint
npm test
npx tsc --noEmit
npm run build
npm start
```

`npm test` runs Vitest once (jsdom). The same lint, test, typecheck, and build checks run in [CI](../.github/workflows/ci.yml). `devIndicators` and the `X-Powered-By` header are disabled in `next.config.ts`.
