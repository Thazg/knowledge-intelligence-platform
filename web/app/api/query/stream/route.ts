import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 180;

function jsonError(message: string, status: number): Response {
  return Response.json(
    {
      detail: message,
    },
    {
      status,
      headers: {
        "Cache-Control": "no-store",
      },
    },
  );
}

export async function POST(request: NextRequest): Promise<Response> {
  const apiBaseUrl = process.env.ENTERPRISE_KIP_API_BASE_URL?.trim();

  if (!apiBaseUrl) {
    return jsonError(
      "The Enterprise KIP backend is not configured.",
      500,
    );
  }

  let requestBody: string;

  try {
    requestBody = await request.text();
  } catch {
    return jsonError("The query request could not be read.", 400);
  }

  let upstream: Response;

  try {
    upstream = await fetch(
      new URL("/v1/query/stream", apiBaseUrl),
      {
        method: "POST",
        headers: {
          Accept: "text/event-stream",
          "Content-Type": "application/json",
        },
        body: requestBody,
        cache: "no-store",
        signal: request.signal,
      },
    );
  } catch {
    return jsonError(
      "The Enterprise KIP backend is unavailable. It may still be waking up.",
      502,
    );
  }

  if (!upstream.ok) {
    let message = "The Enterprise KIP backend could not process the query.";

    try {
      const payload = (await upstream.json()) as {
        detail?: unknown;
      };

      if (typeof payload.detail === "string") {
        message = payload.detail;
      }
    } catch {
      // Keep the safe, normalized message above.
    }

    return jsonError(message, upstream.status);
  }

  if (!upstream.body) {
    return jsonError("The backend returned an empty answer stream.", 502);
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Cache-Control": "no-cache, no-transform",
      "Content-Type": "text/event-stream; charset=utf-8",
      "X-Accel-Buffering": "no",
    },
  });
}
