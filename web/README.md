# Enterprise KIP Web Demo

This folder contains the web interface for Enterprise KIP.

I added it mainly to make the project easier to try without going through Swagger. The page shows what documentation is available in the corpus, provides a few example questions, streams markdown-formatted answers from the existing RAG backend, and displays the cited sources for each response with text excerpts.

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

The UI is intentionally small. It is meant to demonstrate the RAG system, not provide accounts, server-side history, analytics, or a full chat product. The only persistence is up to 8 recent questions in the browser's `localStorage` (`ekip-recent-queries`), deduplicated and clearable anytime — nothing leaves the browser.

## Interface

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
- Each card shows the source label, title, an excerpt (≤500 characters, cleaned of HTML comments and code-fence markers by the backend), collapsible document/chunk identifiers, and an `Open source` link rendered only for `http(s)` URLs with `noopener`.

Status and errors:

- Pipeline steps light up with the live phase: `idle → connecting → retrieving → generating → complete`.
- A cold-start notice appears if the first event takes longer than ~6.5s (Render free-tier wake-up).
- Failures show an error card with a Retry button; stream errors arrive as `error` events without leaking internals.

## Local development

Requirements:

- Node.js 20.9+
- A running Enterprise KIP backend

Start the backend from the repository root:

```bash
python -m uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Then start the frontend:

```bash
cd web
npm install
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

If you want to use the public backend instead, keep the API URL from `.env.example`.

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
npm run build
npm start
```

`npm test` runs vitest once (jsdom). `npm run build` also type-checks. `devIndicators` and the `X-Powered-By` header are disabled in `next.config.ts`.
