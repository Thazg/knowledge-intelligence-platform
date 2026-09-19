import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import QueryDemo from "./QueryDemo";

function streamingResponse(): Response {
  const encoder = new TextEncoder();
  const chunks = [
    "event: status\ndata: {\"status\":\"retrieving\"}\n\nevent: status\n",
    "data: {\"status\":\"generating\"}\n\nevent: answer_delta\ndata: {\"delta\":\"BuildKit improves \"}\n\n",
    "event: answer_delta\ndata: {\"delta\":\"Docker image builds [1].\"}\n\nevent: citations\ndata: {\"citations\":[{\"citation_id\":\"1\",\"document_id\":\"doc-1\",\"chunk_id\":\"chunk-1\"}],\"sources\":[{\"citation_id\":\"1\",\"document_id\":\"doc-1\",\"chunk_id\":\"chunk-1\",\"title\":\"BuildKit\",\"source\":\"docker\",\"url\":\"https://docs.docker.com/build/buildkit/\",\"excerpt\":\"BuildKit speeds up builds.\"}]}\n\n",
    "event: done\ndata: {\"query\":\"What is BuildKit?\",\"model\":\"fake\",\"metrics\":{}}\n\n",
  ];

  return {
    ok: true,
    status: 200,
    body: new ReadableStream<Uint8Array>({
      start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk));
        }
        controller.close();
      },
    }),
  } as Response;
}

function streamingResponseWithUrl(url: string): Response {
  const encoder = new TextEncoder();
  const chunks = [
    "event: answer_delta\ndata: {\"delta\":\"BuildKit improves Docker image builds [1].\"}\n\n",
    `event: citations\ndata: {"citations":[{"citation_id":"1","document_id":"doc-1","chunk_id":"chunk-1"}],"sources":[{"citation_id":"1","document_id":"doc-1","chunk_id":"chunk-1","title":"BuildKit","source":"docker","url":${JSON.stringify(url)},"excerpt":"BuildKit excerpt."}]}\n\n`,
    "event: done\ndata: {\"query\":\"What is BuildKit?\",\"model\":\"fake\",\"metrics\":{}}\n\n",
  ];

  return {
    ok: true,
    status: 200,
    body: new ReadableStream<Uint8Array>({
      start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk));
        }
        controller.close();
      },
    }),
  } as Response;
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.useRealTimers();
  localStorage.clear();
});

describe("QueryDemo", () => {
  it("populates the input from an example question", async () => {
    const user = userEvent.setup();
    render(<QueryDemo />);

    await user.click(
      screen.getByRole("button", {
        name: /What is Docker BuildKit and how is it used during image builds/i,
      }),
    );

    expect(screen.getByLabelText("Technical question")).toHaveValue(
      "What is Docker BuildKit and how is it used during image builds?",
    );
  });

  it("updates the answer from stream deltas and renders citations", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(streamingResponse()));
    render(<QueryDemo />);

    await user.type(screen.getByLabelText("Technical question"), "What is BuildKit?");
    await user.click(screen.getByRole("button", { name: /Ask Enterprise KIP/i }));

    expect(
      await screen.findByRole("button", { name: "Jump to source 1" }),
    ).toHaveTextContent("[1]");
    expect(
      await screen.findByRole("heading", { name: "BuildKit" }),
    ).toBeInTheDocument();
    expect(screen.getByText("1 cited")).toBeInTheDocument();
    expect(screen.getByText("BuildKit speeds up builds.")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Open source/i }),
    ).toHaveAttribute("href", "https://docs.docker.com/build/buildkit/");
  });

  it("jumps to and flashes the cited source when a citation is clicked", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(streamingResponse()));
    render(<QueryDemo />);

    await user.type(screen.getByLabelText("Technical question"), "What is BuildKit?");
    await user.click(screen.getByRole("button", { name: /Ask Enterprise KIP/i }));
    await user.click(
      await screen.findByRole("button", { name: "Jump to source 1" }),
    );

    const card = document.getElementById("source-1");

    expect(card).not.toBeNull();
    expect(card?.className).toMatch(/flash/);
  });

  it("copies the grounded answer to the clipboard", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(streamingResponse()));
    render(<QueryDemo />);

    await user.type(screen.getByLabelText("Technical question"), "What is BuildKit?");
    await user.click(screen.getByRole("button", { name: /Ask Enterprise KIP/i }));
    await user.click(await screen.findByRole("button", { name: "Copy" }));

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("BuildKit improves Docker image builds"),
    );
    expect(await screen.findByRole("button", { name: "Copied" })).toBeInTheDocument();
  });

  it("shows a character count and clears the input", async () => {
    const user = userEvent.setup();
    render(<QueryDemo />);

    await user.type(screen.getByLabelText("Technical question"), "Hi");

    expect(screen.getByText("2/1024", { selector: ".char-count" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Clear" }));

    expect(screen.getByLabelText("Technical question")).toHaveValue("");
  });

  it("remembers recent questions across queries", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(streamingResponse()));
    render(<QueryDemo />);

    await user.type(screen.getByLabelText("Technical question"), "What is BuildKit?");
    await user.click(screen.getByRole("button", { name: /Ask Enterprise KIP/i }));
    await screen.findByRole("heading", { name: "BuildKit" });

    expect(
      screen.getByRole("button", { name: "What is BuildKit?" }),
    ).toBeInTheDocument();
  });

  it("does not render links for unsafe source URLs", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(streamingResponseWithUrl("javascript:alert(1)")),
    );
    render(<QueryDemo />);

    await user.type(screen.getByLabelText("Technical question"), "What is BuildKit?");
    await user.click(screen.getByRole("button", { name: /Ask Enterprise KIP/i }));
    await screen.findByRole("heading", { name: "BuildKit" });

    expect(screen.queryByRole("link", { name: /Open source/i })).not.toBeInTheDocument();
  });

  it("renders a friendly retryable network error", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network unavailable")));
    render(<QueryDemo />);

    await user.type(screen.getByLabelText("Technical question"), "What is Qdrant?");
    await user.click(screen.getByRole("button", { name: /Ask Enterprise KIP/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The demo backend is unavailable. It may still be waking up.",
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("explains a free-tier cold start while the first event is pending", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(() => undefined)));
    render(<QueryDemo />);

    fireEvent.change(screen.getByLabelText("Technical question"), {
      target: {
        value: "What is Kubernetes?",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: /Ask Enterprise KIP/i }));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(6500);
    });

    expect(screen.getByText("The demo backend may be waking up.")).toBeVisible();
  });
});
