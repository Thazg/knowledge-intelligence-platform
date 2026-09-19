import { Fragment, ReactNode } from "react";

export function isSafeHttpUrl(url: string): boolean {
  try {
    const parsed = new URL(url);

    return (
      parsed.protocol === "http:" ||
      parsed.protocol === "https:"
    );
  } catch {
    return false;
  }
}

const INLINE_PATTERN =
  /(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`|\[\d+\])/g;

const LINK_PATTERN = /^\[([^\]]+)\]\(([^)]+)\)$/;
const BOLD_PATTERN = /^\*\*([^*]+)\*\*$/;
const CODE_PATTERN = /^`([^`]+)`$/;
const CITATION_PATTERN = /^\[(\d+)\]$/;
const UNORDERED_PATTERN = /^\s*[-*]\s+(.*)$/;
const ORDERED_PATTERN = /^\s*\d+[.)]\s+(.*)$/;
const HEADING_PATTERN = /^\s*#{1,4}\s+(.*)$/;
const QUOTE_PATTERN = /^\s*>\s?(.*)$/;
const CALLOUT_PATTERN = /\[\s*!(TIP|NOTE|WARNING|IMPORTANT)\s*\]/g;

function renderInline(
  text: string,
  keyPrefix: string,
  citations: boolean,
): ReactNode[] {
  return text.split(INLINE_PATTERN).map((part, index) => {
    const key = `${keyPrefix}-${index}`;
    let match = LINK_PATTERN.exec(part);

    if (match) {
      const label = match[1];
      const url = match[2];

      if (isSafeHttpUrl(url)) {
        return (
          <a
            key={key}
            href={url}
            target="_blank"
            rel="noreferrer noopener"
          >
            {label}
          </a>
        );
      }

      return <Fragment key={key}>{part}</Fragment>;
    }

    match = BOLD_PATTERN.exec(part);

    if (match) {
      return <strong key={key}>{match[1]}</strong>;
    }

    match = CODE_PATTERN.exec(part);

    if (match) {
      return (
        <code key={key} className="md-code">
          {match[1]}
        </code>
      );
    }

    match = CITATION_PATTERN.exec(part);

    if (match && citations) {
      return (
        <button
          key={key}
          type="button"
          className="citation-link"
          data-citation={match[1]}
          aria-label={`Jump to source ${match[1]}`}
        >
          {part}
        </button>
      );
    }

    return <Fragment key={key}>{part}</Fragment>;
  });
}

export function renderRichText(
  text: string,
  options?: {
    citations?: boolean;
  },
): ReactNode[] {
  const withCitations = options?.citations ?? true;
  const cleaned = text.replace(CALLOUT_PATTERN, "");
  const lines = cleaned.split("\n");
  const blocks: ReactNode[] = [];
  let key = 0;
  let inFence = false;
  let fenceLines: string[] = [];
  let listItems: string[] = [];
  let listOrdered = false;
  let paragraphLines: string[] = [];

  const flushParagraph = () => {
    if (!paragraphLines.length) {
      return;
    }

    const joined = paragraphLines.join(" ").trim();
    paragraphLines = [];

    if (joined) {
      blocks.push(
        <p key={key++}>{renderInline(joined, `p-${key}`, withCitations)}</p>,
      );
    }
  };

  const flushList = () => {
    if (!listItems.length) {
      return;
    }

    const items = listItems;
    listItems = [];
    const ListTag = listOrdered ? "ol" : "ul";

    blocks.push(
      <ListTag key={key++} className="md-list">
        {items.map((item, itemIndex) => (
          <li key={itemIndex}>
            {renderInline(item, `li-${key}-${itemIndex}`, withCitations)}
          </li>
        ))}
      </ListTag>,
    );
  };

  const flushFence = () => {
    if (!fenceLines.length) {
      return;
    }

    const code = fenceLines.join("\n");
    fenceLines = [];

    blocks.push(
      <pre key={key++} className="md-pre">
        <code>{code}</code>
      </pre>,
    );
  };

  for (const line of lines) {
    const stripped = line.trim();

    if (stripped.startsWith("```")) {
      if (inFence) {
        inFence = false;
        flushFence();
      } else {
        flushParagraph();
        flushList();
        inFence = true;
      }

      continue;
    }

    if (inFence) {
      fenceLines.push(line);
      continue;
    }

    if (!stripped) {
      flushParagraph();
      flushList();
      continue;
    }

    const unordered = UNORDERED_PATTERN.exec(line);
    const ordered = ORDERED_PATTERN.exec(line);

    if (unordered || ordered) {
      const itemOrdered = ordered !== null;
      const itemText = (unordered ?? ordered)?.[1] ?? "";

      if (
        !listItems.length ||
        listOrdered !== itemOrdered
      ) {
        flushParagraph();
        flushList();
        listOrdered = itemOrdered;
      }

      listItems.push(itemText);
      continue;
    }

    flushList();

    const heading = HEADING_PATTERN.exec(line);

    if (heading) {
      flushParagraph();
      blocks.push(
        <p key={key++} className="md-heading">
          <strong>
            {renderInline(
              heading[1],
              `h-${key}`,
              withCitations,
            )}
          </strong>
        </p>,
      );
      continue;
    }

    const quote = QUOTE_PATTERN.exec(line);

    if (quote) {
      flushParagraph();
      blocks.push(
        <p key={key++} className="md-quote">
          {renderInline(quote[1], `q-${key}`, withCitations)}
        </p>,
      );
      continue;
    }

    paragraphLines.push(stripped);
  }

  flushParagraph();
  flushList();

  if (inFence) {
    inFence = false;
    flushFence();
  }

  return blocks;
}
