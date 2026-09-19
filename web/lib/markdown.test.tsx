import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { isSafeHttpUrl, renderRichText } from "./markdown";

function renderText(
  text: string,
  options?: {
    citations?: boolean;
  },
) {
  return render(<div>{renderRichText(text, options)}</div>);
}

describe("isSafeHttpUrl", () => {
  it("allows http and https URLs", () => {
    expect(isSafeHttpUrl("https://docs.docker.com/x")).toBe(true);
    expect(isSafeHttpUrl("http://localhost:8000/docs")).toBe(true);
  });

  it("rejects javascript, data, and malformed URLs", () => {
    expect(isSafeHttpUrl("javascript:alert(1)")).toBe(false);
    expect(isSafeHttpUrl("data:text/html,<h1>x</h1>")).toBe(false);
    expect(isSafeHttpUrl("not a url")).toBe(false);
  });
});

describe("renderRichText", () => {
  it("renders bold and inline code", () => {
    const { container } = renderText(
      "Use **docker compose** instead of `docker-compose`.",
    );

    expect(container.querySelector("strong")).toHaveTextContent(
      "docker compose",
    );
    expect(container.querySelector("code")).toHaveTextContent(
      "docker-compose",
    );
  });

  it("renders fenced code blocks as plain text", () => {
    const { container } = renderText(
      "Run this:\n```py\nprint('hi')\n```\nDone.",
    );
    const pre = container.querySelector("pre");

    expect(pre).not.toBeNull();
    expect(pre).toHaveTextContent("print('hi')");
    expect(container.textContent).not.toContain("```");
  });

  it("renders unordered and ordered lists", () => {
    const { container } = renderText(
      "- greedy\n- sampling\n\n1. first\n2. second",
    );

    expect(container.querySelectorAll("ul li")).toHaveLength(2);
    expect(container.querySelectorAll("ol li")).toHaveLength(2);
  });

  it("renders headings and quotes without markers", () => {
    const { container } = renderText(
      "## Pipeline\n> quoted text",
    );

    expect(container.querySelector(".md-heading")).toHaveTextContent(
      "Pipeline",
    );
    expect(container.querySelector(".md-quote")).toHaveTextContent(
      "quoted text",
    );
    expect(container.textContent).not.toContain("##");
  });

  it("renders safe links and drops unsafe ones", () => {
    const { container } = renderText(
      "See [docs](https://example.test/x) and [evil](javascript:alert(1)).",
    );
    const link = container.querySelector("a");

    expect(link).toHaveAttribute("href", "https://example.test/x");
    expect(container.textContent).toContain("[evil](javascript:alert(1))");
  });

  it("renders citations as buttons and escapes raw HTML", () => {
    const { container } = renderText(
      "Answer here [1] <script>alert(1)</script>.",
    );

    expect(
      container.querySelector('button[data-citation="1"]'),
    ).toHaveTextContent("[1]");
    expect(container.querySelector("script")).toBeNull();
  });

  it("renders citations as plain text when disabled", () => {
    const { container } = renderText("See [12] for details.", {
      citations: false,
    });

    expect(container.querySelector("button")).toBeNull();
    expect(container.textContent).toContain("[12]");
  });

  it("strips callout markers", () => {
    const { container } = renderText(
      "[!TIP] Skip ahead to the next section.",
    );

    expect(container.textContent).not.toContain("[!TIP]");
    expect(container.textContent).toContain("Skip ahead");
  });

  it("splits paragraphs on blank lines", () => {
    const { container } = renderText("First.\n\nSecond.");

    expect(container.querySelectorAll("p")).toHaveLength(2);
  });
});
