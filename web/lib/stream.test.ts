import { describe, expect, it } from "vitest";

import { consumeEventStream, StreamEvent } from "./stream";

describe("consumeEventStream", () => {
  it("parses SSE frames split across byte chunks", async () => {
    const encoder = new TextEncoder();
    const events: StreamEvent[] = [];
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode("event: answer_"));
        controller.enqueue(
          encoder.encode('delta\r\ndata: {"delta":"Hello"}\r\n\r\n'),
        );
        controller.close();
      },
    });

    await consumeEventStream(body, (event) => events.push(event));

    expect(events).toEqual([
      {
        event: "answer_delta",
        data: {
          delta: "Hello",
        },
      },
    ]);
  });
});
