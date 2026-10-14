"use client";

import {
  FormEvent,
  KeyboardEvent,
  MouseEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  consumeEventStream,
  StreamEvent,
} from "../lib/stream";
import {
  isSafeHttpUrl,
  renderRichText,
} from "../lib/markdown";

const REPOSITORY_URL =
  "https://github.com/Thazg/knowledge-intelligence-platform";
const API_DOCS_URL = "https://enterprise-kip-api.onrender.com/docs";
const RETRIEVAL_REPORT_URL = `${REPOSITORY_URL}/blob/main/benchmarks/retrieval/reports/cloud-hybrid-v1.md`;
const FEATURED_QUESTION = "What is Docker BuildKit and how is it used during image builds?";
const FEATURED_SOURCES = [
  {
    number: "1",
    title: "BuildKit",
    url: "https://github.com/docker/docs/blob/main/content/manuals/build/buildkit/_index.md",
  },
  {
    number: "2",
    title: "Docker Build Overview",
    url: "https://github.com/docker/docs/blob/main/content/manuals/build/concepts/overview.md",
  },
] as const;

const CORPUS_SOURCES = [
  "Docker",
  "FastAPI",
  "Hugging Face Transformers",
  "Kubernetes",
  "LangChain",
  "LangGraph",
  "Qdrant",
];

const EXAMPLE_QUESTIONS = [
  {
    source: "Kubernetes",
    question: "What does kubectl apply do?",
  },
  {
    source: "FastAPI",
    question: "What problem does FastAPI dependency injection solve?",
  },
  {
    source: "Qdrant",
    question:
      "How does a Qdrant payload index help filtered vector search?",
  },
];

type Source = {
  citation_id: string;
  document_id: string;
  chunk_id: string;
  title: string | null;
  source: string | null;
  url: string | null;
  excerpt: string | null;
};

const HISTORY_STORAGE_KEY = "ekip-recent-queries";
const MAX_HISTORY_ITEMS = 8;
const MAX_QUERY_CHARS = 1024;

type QueryStatus =
  | "idle"
  | "connecting"
  | "retrieving"
  | "generating"
  | "complete";

function loadHistory(): string[] {
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_KEY);

    if (!raw) {
      return [];
    }

    const parsed: unknown = JSON.parse(raw);

    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed
      .filter(
        (item): item is string => typeof item === "string",
      )
      .slice(0, MAX_HISTORY_ITEMS);
  } catch {
    return [];
  }
}

function asSource(value: unknown): Source | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const candidate = value as Partial<Source>;

  if (
    typeof candidate.citation_id !== "string" ||
    typeof candidate.document_id !== "string" ||
    typeof candidate.chunk_id !== "string"
  ) {
    return null;
  }

  return {
    citation_id: candidate.citation_id,
    document_id: candidate.document_id,
    chunk_id: candidate.chunk_id,
    title:
      typeof candidate.title === "string"
        ? candidate.title
        : null,
    source:
      typeof candidate.source === "string"
        ? candidate.source
        : null,
    url:
      typeof candidate.url === "string"
        ? candidate.url
        : null,
    excerpt:
      typeof candidate.excerpt === "string"
        ? candidate.excerpt
        : null,
  };
}

function GitHubIcon() {
  return (
    <svg className="header-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true" focusable="false">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.65 7.65 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8" />
    </svg>
  );
}

function DocsIcon() {
  return (
    <svg className="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="M12 7v14M3 18V5a2 2 0 0 1 2-2h3a4 4 0 0 1 4 4v14a4 4 0 0 0-4-3H3Zm18 0V5a2 2 0 0 0-2-2h-3a4 4 0 0 0-4 4v14a4 4 0 0 1 4-3h5Z" />
    </svg>
  );
}

// FileTypeCorner © 2026 Lucide Icons and Contributors (ISC).
// Permission to use, copy, modify, and/or distribute this icon for any purpose
// with or without fee is granted when this copyright and permission notice remain.
// https://lucide.dev/icons/file-type-corner
function FileTypeCornerIcon() {
  return (
    <svg className="source-document-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="M12 22h6a2 2 0 0 0 2-2V8a2.4 2.4 0 0 0-.706-1.706l-3.588-3.588A2.4 2.4 0 0 0 14 2H6a2 2 0 0 0-2 2v6" />
      <path d="M14 2v5a1 1 0 0 0 1 1h5" />
      <path d="M3 16v-1.5a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 .5.5V16" />
      <path d="M6 22h2" />
      <path d="M7 14v8" />
    </svg>
  );
}

function BrandMark() {
  return (
    <svg viewBox="0 0 40 40" fill="none" aria-hidden="true" focusable="false">
      <path
        d="M10 8v24M16 20 29 8M16 20l13 12"
        stroke="currentColor"
        strokeWidth="3.5"
        strokeLinecap="square"
      />
      <circle cx="30" cy="8" r="2.3" fill="currentColor" />
      <circle cx="30" cy="32" r="2.3" fill="currentColor" />
    </svg>
  );
}

function sourceLabel(source: Source): string {
  if (!source.source) {
    return "Documentation";
  }

  if (source.source === "huggingface") {
    return "Hugging Face Transformers";
  }

  return source.source.charAt(0).toUpperCase() + source.source.slice(1);
}

function friendlyHttpError(status: number, detail?: string): string {
  if (status === 422) {
    return "Please enter a technical question between 1 and 1,024 characters.";
  }

  if (status === 404) {
    return "The configured backend does not expose the streaming endpoint yet. Check the deployment and retry.";
  }

  if (status === 503) {
    return "The generation service is busy or temporarily unavailable. Please retry shortly.";
  }

  if (status === 504) {
    return "Answer generation timed out. Please retry.";
  }

  if (status >= 500) {
    return (
      detail ??
      "The demo backend is unavailable. It may still be waking up from a cold start."
    );
  }

  return detail ?? "The query could not be processed. Please try again.";
}

export default function QueryDemo() {
  const [query, setQuery] = useState("");
  const [lastQuestion, setLastQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [status, setStatus] = useState<QueryStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [showColdStart, setShowColdStart] = useState(false);
  const [copied, setCopied] = useState(false);
  const [flashCitation, setFlashCitation] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const flashTimer = useRef<number | null>(null);

  useEffect(() => {
    // Browser storage is unavailable during SSR; load it only after hydration.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setHistory(loadHistory());
  }, []);

  useEffect(() => {
    if (!lastQuestion) {
      return;
    }

    const target = resultRef.current;

    if (target && typeof target.scrollIntoView === "function") {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }, [lastQuestion]);

  useEffect(
    () => () => {
      if (flashTimer.current !== null) {
        window.clearTimeout(flashTimer.current);
      }
    },
    [],
  );

  function rememberQuestion(question: string) {
    setHistory((current) => {
      const next = [
        question,
        ...current.filter((item) => item !== question),
      ].slice(0, MAX_HISTORY_ITEMS);

      try {
        localStorage.setItem(
          HISTORY_STORAGE_KEY,
          JSON.stringify(next),
        );
      } catch {
        // Private browsing or disabled storage: history stays in memory.
      }

      return next;
    });
  }

  function clearHistory() {
    setHistory([]);

    try {
      localStorage.removeItem(HISTORY_STORAGE_KEY);
    } catch {
      // Ignore storage failures; in-memory state is already cleared.
    }
  }

  const jumpToSource = useCallback((citationId: string) => {
    setFlashCitation(citationId);

    if (flashTimer.current !== null) {
      window.clearTimeout(flashTimer.current);
    }

    flashTimer.current = window.setTimeout(() => {
      setFlashCitation(null);
    }, 1600);

    const target = document.getElementById(
      `source-${citationId}`,
    );

    if (target && typeof target.scrollIntoView === "function") {
      target.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, []);

  async function copyAnswer() {
    if (!answer) {
      return;
    }

    try {
      await navigator.clipboard.writeText(answer);
      setCopied(true);
      window.setTimeout(() => {
        setCopied(false);
      }, 1600);
    } catch {
      setCopied(false);
    }
  }

  function handleAnswerClick(
    event: MouseEvent<HTMLDivElement>,
  ) {
    const target = event.target;

    if (!(target instanceof HTMLElement)) {
      return;
    }

    const button = target.closest("button[data-citation]");

    if (button instanceof HTMLButtonElement) {
      jumpToSource(button.dataset.citation ?? "");
    }
  }

  function chooseExample(question: string) {
    setQuery(question);
    setError(null);
    inputRef.current?.focus();
  }

  async function runQuery(question: string) {
    const cleanedQuestion = question.trim();

    if (!cleanedQuestion || isActive) {
      return;
    }

    setIsActive(true);
    setLastQuestion(cleanedQuestion);
    setAnswer("");
    setSources([]);
    setError(null);
    setStatus("connecting");
    setShowColdStart(false);
    setCopied(false);
    setFlashCitation(null);
    rememberQuestion(cleanedQuestion);

    let receivedEvent = false;
    let receivedDone = false;
    let receivedError = false;

    const coldStartTimer = window.setTimeout(() => {
      if (!receivedEvent) {
        setShowColdStart(true);
      }
    }, 6500);

    try {
      let response: Response;

      try {
        response = await fetch("/api/query/stream", {
          method: "POST",
          headers: {
            Accept: "text/event-stream",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query: cleanedQuestion,
          }),
        });
      } catch {
        throw new Error(
          "The demo backend is unavailable. It may still be waking up. Please retry shortly.",
        );
      }

      if (!response.ok) {
        let detail: string | undefined;

        try {
          const payload = (await response.json()) as {
            detail?: unknown;
          };

          if (typeof payload.detail === "string") {
            detail = payload.detail;
          }
        } catch {
          // Use the status-specific safe message below.
        }

        throw new Error(friendlyHttpError(response.status, detail));
      }

      if (!response.body) {
        throw new Error("The backend returned an empty answer stream.");
      }

      await consumeEventStream(response.body, (streamEvent: StreamEvent) => {
        receivedEvent = true;
        setShowColdStart(false);

        if (streamEvent.event === "status") {
          const nextStatus = streamEvent.data.status;

          if (nextStatus === "retrieving" || nextStatus === "generating") {
            setStatus(nextStatus);
          }
          return;
        }

        if (streamEvent.event === "answer_delta") {
          const delta = streamEvent.data.delta;

          if (typeof delta === "string") {
            setAnswer((current) => current + delta);
          }
          return;
        }

        if (streamEvent.event === "citations") {
          const rawSources = Array.isArray(streamEvent.data.sources)
            ? streamEvent.data.sources
            : [];
          const rawCitations = Array.isArray(streamEvent.data.citations)
            ? streamEvent.data.citations
            : [];
          const citedIds = new Set(
            rawCitations.flatMap((citation) => {
              if (!citation || typeof citation !== "object") {
                return [];
              }

              const citationId = (citation as { citation_id?: unknown })
                .citation_id;
              return typeof citationId === "string" ? [citationId] : [];
            }),
          );

          setSources(
            rawSources.flatMap((entry) => {
              const source = asSource(entry);

              if (!source || !citedIds.has(source.citation_id)) {
                return [];
              }

              return [source];
            }),
          );
          return;
        }

        if (streamEvent.event === "done") {
          receivedDone = true;
          setStatus("complete");
          return;
        }

        if (streamEvent.event === "error") {
          const message = streamEvent.data.message;
          receivedError = true;
          setError(
            typeof message === "string"
              ? message
              : "The answer stream ended unexpectedly. Please retry.",
          );
        }
      });

      if (!receivedDone && !receivedError) {
        throw new Error("The answer stream was interrupted. Please retry.");
      }
    } catch (requestError) {
      if (!receivedError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "The demo backend is unavailable. Please retry.",
        );
      }
      setStatus("idle");
    } finally {
      window.clearTimeout(coldStartTimer);
      setIsActive(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runQuery(query);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();

      if (!isActive && query.trim()) {
        void runQuery(query);
      }
    }
  }

  const statusCopy = {
    idle: "Ready when you are",
    connecting: "Connecting to the documentation service…",
    retrieving: "Searching the documentation…",
    generating: "Writing an answer with sources…",
    complete: "Answer ready",
  }[status];

  return (
    <main>
      <a className="skip-link" href="#query-title">Skip to question</a>
      <header className="site-header">
        <div className="site-header-inner">
          <a className="wordmark" href="#top" aria-label="Enterprise Knowledge Intelligence Platform home">
            <span className="wordmark-mark" aria-hidden="true">
              <BrandMark />
            </span>
            <span className="wordmark-name">Enterprise Knowledge Intelligence Platform</span>
          </a>
          <nav className="header-actions" aria-label="Project links">
            <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">
              <GitHubIcon /> GitHub
            </a>
            <a href={API_DOCS_URL} target="_blank" rel="noreferrer">
              <DocsIcon /> API Docs
            </a>
          </nav>
        </div>
      </header>

      <section className="hero" id="top" aria-labelledby="hero-title">
        <div className="hero-copy">
          <h1 id="hero-title">Ask the docs.<br />See the source.</h1>
          <p className="hero-subtitle">
            Get a useful answer, then open the documentation behind it.
          </p>
        </div>
        <ol className="hero-workflow" aria-label="How a question becomes an answer">
          <li><span>Query</span></li>
          <li><span>Hybrid retrieval</span></li>
          <li><span>Evidence selection</span></li>
          <li><span>Grounded generation</span></li>
          <li><span>Citations</span></li>
        </ol>
      </section>

      <div className="content-grid">
        <div className="main-column">
          <section className="panel corpus-panel" aria-labelledby="corpus-title">
            <div>
              <h2 id="corpus-title">Indexed scope</h2>
              <p>Seven documentation sets are searchable here. The demo does not search the open web.</p>
            </div>
            <div className="source-badges" aria-label="Indexed documentation sources">
              {CORPUS_SOURCES.map((source) => (
                <span key={source}>{source}</span>
              ))}
            </div>
          </section>

          <section className="query-section" aria-labelledby="query-title">
            <div className="query-header">
              <div>
                <h2 id="query-title" tabIndex={-1}>What would you like to know?</h2>
              </div>
              <span className={`status-pill status-${status}`}>
                <span aria-hidden="true" />
                {statusCopy}
              </span>
            </div>

            <form onSubmit={submit} className="query-form">
              <label htmlFor="query-input">Technical question</label>
              <textarea
                id="query-input"
                ref={inputRef}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={handleKeyDown}
                maxLength={MAX_QUERY_CHARS}
                rows={2}
                placeholder="For example: What does kubectl apply do?"
                aria-describedby="query-help"
                disabled={isActive}
              />
              <div className="form-footer">
                <span id="query-help">
                  <kbd>Enter</kbd> to ask · <kbd>Shift</kbd> + <kbd>Enter</kbd>{" "}
                  for a new line ·{" "}
                  <span className="char-count">
                    {query.length}/{MAX_QUERY_CHARS}
                  </span>
                </span>
                <div className="form-actions">
                  {query && !isActive ? (
                    <button
                      className="clear-button"
                      type="button"
                      onClick={() => {
                        setQuery("");
                        setError(null);
                        inputRef.current?.focus();
                      }}
                    >
                      Clear
                    </button>
                  ) : null}
                  <button
                    className="ask-button"
                    type="submit"
                    disabled={isActive || !query.trim()}
                  >
                    {isActive ? "Searching…" : "Ask the docs"}
                    <span aria-hidden="true">→</span>
                  </button>
                </div>
              </div>
            </form>

            {isActive ? (
              <div className="live-progress" role="status">
                <span className="live-progress-track" aria-hidden="true" />
                {statusCopy}
              </div>
            ) : null}

            {history.length > 0 && !isActive ? (
              <div className="history">
                <div className="history-heading">
                  <span>Recent questions</span>
                  <button
                    className="history-clear"
                    type="button"
                    onClick={clearHistory}
                  >
                    Clear history
                  </button>
                </div>
                <div className="history-list">
                  {history.map((item) => (
                    <button
                      key={item}
                      className="history-item"
                      type="button"
                      onClick={() => {
                        setQuery(item);
                        setError(null);
                        inputRef.current?.focus();
                      }}
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {showColdStart && isActive ? (
              <div className="cold-start" role="status">
                <span className="spinner" aria-hidden="true" />
                <div>
                  <strong>The demo backend may be waking up.</strong>
                  <p>Render free-tier cold starts can take several seconds.</p>
                </div>
              </div>
            ) : null}

            {lastQuestion ? (
              <div className="result" aria-live="polite" ref={resultRef}>
                <div className="question-block">
                  <span>Your question</span>
                  <p>{lastQuestion}</p>
                </div>

                {answer || isActive ? (
                  <div className="answer-block">
                    <div className="answer-heading">
                      <span className="answer-mark" aria-hidden="true">
                        <BrandMark />
                      </span>
                      <div>
                        <strong>Answer from the docs</strong>
                        <span>{isActive ? statusCopy : "From indexed evidence"}</span>
                      </div>
                      {answer && !isActive ? (
                        <button
                          className="copy-button"
                          type="button"
                          onClick={() => void copyAnswer()}
                        >
                          {copied ? "Copied" : "Copy"}
                        </button>
                      ) : null}
                    </div>
                    {answer ? (
                      <div
                        className="answer-copy"
                        onClick={handleAnswerClick}
                      >
                        {renderRichText(answer)}
                        {isActive ? (
                          <span
                            className="typing-caret"
                            aria-hidden="true"
                          />
                        ) : null}
                      </div>
                    ) : (
                      <div className="answer-skeleton" aria-label="Waiting for answer">
                        <span />
                        <span />
                        <span />
                      </div>
                    )}
                  </div>
                ) : null}

                {error ? (
                  <div className="error-card" role="alert">
                    <div>
                      <strong>Enterprise KIP could not finish this query.</strong>
                      <p>{error}</p>
                    </div>
                    <button type="button" onClick={() => void runQuery(lastQuestion)}>
                      Retry
                    </button>
                  </div>
                ) : null}

                {sources.length ? (
                  <section className="sources" aria-labelledby="sources-title">
                    <div className="sources-heading">
                      <div>
                        <h3 id="sources-title">Sources</h3>
                        <p>Documentation cited in the generated answer.</p>
                      </div>
                      <span>{sources.length} cited</span>
                    </div>
                    <div className="source-list">
                      {sources.map((source) => (
                        <article
                          className={
                            flashCitation === source.citation_id
                              ? "source-card flash"
                              : "source-card"
                          }
                          id={`source-${source.citation_id}`}
                          key={source.citation_id}
                        >
                          <span className="citation-number">[{source.citation_id}]</span>
                          <div>
                            <span className="source-name">{sourceLabel(source)}</span>
                            <h4>{source.title ?? "Untitled documentation source"}</h4>
                            {source.excerpt ? (
                              <div className="source-excerpt">
                                {renderRichText(source.excerpt, {
                                  citations: false,
                                })}
                              </div>
                            ) : null}
                            <details>
                              <summary>Source identifiers</summary>
                              <code>Document {source.document_id}</code>
                              <code>Chunk {source.chunk_id}</code>
                            </details>
                          </div>
                          {source.url && isSafeHttpUrl(source.url) ? (
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noreferrer noopener"
                            >
                              <FileTypeCornerIcon /> Open source
                            </a>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  </section>
                ) : null}
              </div>
            ) : null}
          </section>

          <section className="examples" aria-labelledby="examples-title">
            <div className="section-heading">
              <div>
                <h2 id="examples-title">Need a place to start?</h2>
              </div>
              <p>Choose a question to place it in the query box.</p>
            </div>
            <div className="example-grid">
              {EXAMPLE_QUESTIONS.map((example) => (
                <button
                  className="example-card"
                  key={example.question}
                  type="button"
                  onClick={() => chooseExample(example.question)}
                  disabled={isActive}
                >
                  <span>{example.source}</span>
                  <strong>{example.question}</strong>
                  <i aria-hidden="true">Use question →</i>
                </button>
              ))}
            </div>
          </section>

          <section className="sample-result" aria-labelledby="sample-title">
            <div className="sample-heading">
              <div>
                <h2 id="sample-title">An answer with sources</h2>
              </div>
              <span className="sample-badge">2 sources</span>
            </div>
            <p className="sample-question">{FEATURED_QUESTION}</p>
            <p className="sample-answer">
              BuildKit is Docker&apos;s builder backend. It can skip unused build
              stages, run independent stages in parallel, and transfer only
              changed files in the build context{" "}
              <a href={FEATURED_SOURCES[0].url} target="_blank" rel="noreferrer noopener">[1]</a>.
              {" "}Buildx sends build requests to BuildKit, which resolves
              instructions and executes build steps{" "}
              <a href={FEATURED_SOURCES[1].url} target="_blank" rel="noreferrer noopener">[2]</a>.
            </p>
            <div className="sample-sources" aria-label="Example documentation sources">
              {FEATURED_SOURCES.map((source) => (
                <a
                  key={source.number}
                  href={source.url}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  <span>[{source.number}]</span> {source.title} <FileTypeCornerIcon />
                </a>
              ))}
            </div>
            <div className="sample-footer">
              <span>Condensed from a local run. Live wording may vary.</span>
              <button
                type="button"
                onClick={() => chooseExample(FEATURED_QUESTION)}
                disabled={isActive}
              >
                Ask this live <span aria-hidden="true">→</span>
              </button>
            </div>
          </section>

        </div>

        <aside className="about-panel" aria-labelledby="about-title">
          <h2 id="about-title">Evidence behind the demo</h2>
          <p>Cloud deployment profile, evaluated on manually verified questions.</p>
          <div className="metric-grid" aria-label="Cloud retrieval benchmark scores">
            <div><strong>100</strong><span>Verified queries</span></div>
            <div><strong>93%</strong><span>Hit@10</span></div>
            <div><strong>0.7119</strong><span>MRR</span></div>
          </div>
          <p className="metric-scope">Dense + BM25 with Weighted RRF. These are retrieval scores, not answer-quality scores.</p>
          <a className="report-link" href={RETRIEVAL_REPORT_URL} target="_blank" rel="noreferrer noopener">
            Read the retrieval benchmark <FileTypeCornerIcon />
          </a>
          <section className="answer-path" aria-labelledby="answer-path-title">
            <h3 id="answer-path-title">How an answer gets its sources</h3>
            <ol>
              <li>
                <span aria-hidden="true">01</span>
                <strong>Search</strong>
                <p>Dense and BM25 search the seven indexed documentation sets.</p>
              </li>
              <li>
                <span aria-hidden="true">02</span>
                <strong>Rank</strong>
                <p>Weighted RRF combines results before the context builder selects passages.</p>
              </li>
              <li>
                <span aria-hidden="true">03</span>
                <strong>Check</strong>
                <p>Numbered citations let you open the documentation behind an answer.</p>
              </li>
            </ol>
          </section>
        </aside>
      </div>

      <footer>
        <span>© 2026 Nguyen Tam Thang. All rights reserved.</span>
        <span>Answers from curated documentation, not the open web.</span>
      </footer>
    </main>
  );
}
