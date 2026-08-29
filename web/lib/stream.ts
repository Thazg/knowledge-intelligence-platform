export type StreamEventName =
  | "status"
  | "answer_delta"
  | "citations"
  | "done"
  | "error";

export type StreamEvent = {
  event: StreamEventName;
  data: Record<string, unknown>;
};

function parseFrame(frame: string): StreamEvent | null {
  let event = "message";
  const dataLines: string[] = [];

  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (!dataLines.length) {
    return null;
  }

  if (
    ![
      "status",
      "answer_delta",
      "citations",
      "done",
      "error",
    ].includes(event)
  ) {
    return null;
  }

  return {
    event: event as StreamEventName,
    data: JSON.parse(dataLines.join("\n")) as Record<string, unknown>,
  };
}

export async function consumeEventStream(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      buffer += decoder.decode();
      break;
    }

    buffer += decoder.decode(value, {
      stream: true,
    });
    buffer = buffer.replaceAll("\r\n", "\n");

    let boundary = buffer.indexOf("\n\n");

    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      const event = parseFrame(frame);

      if (event) {
        onEvent(event);
      }

      boundary = buffer.indexOf("\n\n");
    }
  }

  const remaining = buffer.replaceAll("\r\n", "\n").trim();

  if (remaining) {
    const event = parseFrame(remaining);

    if (event) {
      onEvent(event);
    }
  }
}
