# Enterprise KIP Web Demo

This folder contains the web interface for Enterprise KIP.

I added it mainly to make the project easier to try without going through Swagger. The page shows what documentation is available in the corpus, provides a few example questions, streams answers from the existing RAG backend, and displays the sources used for each response.

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

The UI is intentionally small. It is meant to demonstrate the RAG system, not provide accounts, saved conversations, analytics, or a full chat product.

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

The backend returns Server-Sent Events while a query is processed.

A normal request looks roughly like this:

```text
status        retrieving
status        generating
answer_delta  ...
citations     ...
done
```

The final citation event uses the same source information returned by the existing RAG pipeline.

If something fails after the stream has started, the backend sends an error event instead of exposing the internal exception.

The stream only contains answer text, source information, and basic request status. Model reasoning is not exposed.

## Checks

From the `web` directory:

```bash
npm run lint
npm test
npm run build
```
