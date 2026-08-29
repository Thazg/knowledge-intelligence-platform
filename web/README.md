# Enterprise KIP Web Demo

A small Next.js interface for the Enterprise Knowledge Intelligence Platform. It helps recruiters understand the indexed corpus, run benchmark-backed example questions, watch grounded answers stream, and inspect cited documentation.

The browser never calls Render directly:

```text
Browser
  → Next.js POST /api/query/stream
  → FastAPI POST /v1/query/stream
  → existing RAGService and RAGPipeline
```

The interface is intentionally a single-query demo. It has no authentication, persistence, analytics, or conversation database.

## Local development

Requirements:

- Node.js 20.9 or newer
- The existing Enterprise KIP backend, including its configured Qdrant and generation dependencies

Terminal 1, from the repository root:

```bash
python -m uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2:

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

On PowerShell, copy the environment file with:

```powershell
Copy-Item .env.example .env.local
```

Then open [http://localhost:3000](http://localhost:3000).

The only frontend environment variable is server-side:

```ini
ENTERPRISE_KIP_API_BASE_URL=http://localhost:8000
```

To use the public Render backend locally, keep the value from `.env.example`.

## Stream contract

`POST /v1/query/stream` returns `text/event-stream` using the existing query validation and citation/source models.

```text
event: status
data: {"status":"retrieving"}

event: status
data: {"status":"generating"}

event: answer_delta
data: {"delta":"..."}

event: citations
data: {"citations":[...],"sources":[...]}

event: done
data: {"query":"...","model":"...","metrics":{...}}
```

Failures after streaming begins use one safe event:

```text
event: error
data: {"code":"generation_timeout","message":"...","retryable":true}
```

The stream exposes only answer text and user-safe operational states. It does not expose model reasoning. Groq and Ollama use their native streaming responses; a generator without native streaming support may emit one completed answer delta.

## Checks

```bash
npm run lint
npm test
npm run build
```

## Deploy to Vercel

1. Import `https://github.com/Thazg/knowledge-intelligence-platform` into Vercel.
2. Set **Root Directory** to `web`.
3. Keep the detected **Framework Preset** as Next.js.
4. Add this Production, Preview, and Development environment variable:

   ```ini
   ENTERPRISE_KIP_API_BASE_URL=https://enterprise-kip-api.onrender.com
   ```

5. Deploy. No database, persistent volume, or `NEXT_PUBLIC_` variable is required.

After deployment, replace `<VERCEL_WEB_DEMO_URL>` in the root [`README.md`](../README.md) with the assigned Vercel URL.
