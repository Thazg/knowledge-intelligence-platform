"use client";

import {
  FormEvent,
  Fragment,
  KeyboardEvent,
  MouseEvent,
  ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  consumeEventStream,
  StreamEvent,
} from "../lib/stream";

const REPOSITORY_URL =
  "https://github.com/Thazg/knowledge-intelligence-platform";
const API_DOCS_URL = "https://enterprise-kip-api.onrender.com/docs";

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
    source: "Docker",
    question:
      "What is Docker BuildKit and how is it used during image builds?",
  },
  {
    source: "Kubernetes",
    question: "What does kubectl apply do?",
  },
  {
    source: "Kubernetes",
    question:
      "What should Kubernetes users consider when moving from KMS v1 to KMS v2?",
  },
  {
    source: "FastAPI",
    question: "What problem does FastAPI dependency injection solve?",
  },
  {
    source: "Transformers",
    question:
      "What does generate() do when generating text with a Transformers model?",
  },
  {
    source: "Qdrant",
    question:
      "How does a Qdrant payload index help filtered vector search?",
  },
  {
    source: "Cross-tool",
    question:
      "What responsibilities belong to FastAPI versus Qdrant when building a vector-search API?",
  },
  {
    source: "Docker",
    question:
      "How does current Docker documentation distinguish docker-compose from docker compose?",
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

const PIPELINE_STEPS = [
  "Query",
  "Hybrid retrieval",
  "Grounded generation",
  "Citations",
] as const;

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

function ExternalIcon() {
  return (
    <svg
      className="external-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  );
}

function isSafeHttpUrl(url: string): boolean {  try {
    const parsed = new URL(url);

    return (
      parsed.protocol === "http:" ||
      parsed.protocol === "https:"
    );
  } catch {
    return false;
  }
}

function renderAnswer(answer: string): ReactNode[] {
  return answer.split(/(\[\d+\])/g).map((part, index) => {
    const match = /^\[(\d+)\]$/.exec(part);

    if (!match) {
      return <Fragment key={index}>{part}</Fragment>;
    }

    return (
      <button
        key={index}
        type="button"
        className="citation-link"
        data-citation={match[1]}
        aria-label={`Jump to source ${match[1]}`}
      >
        {part}
      </button>
    );
  });
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
  const [history, setHistory] = useState<string[]>(() => loadHistory());
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const flashTimer = useRef<number | null>(null);

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
    idle: "Ready for a corpus-grounded question",
    connecting: "Connecting to the documentation service…",
    retrieving: "Retrieving documentation…",
    generating: "Generating grounded answer…",
    complete: "Grounded answer complete",
  }[status];

  const activePipelineStep = {
    idle: -1,
    connecting: 0,
    retrieving: 1,
    generating: 2,
    complete: 3,
  }[status];

  return (
    <main>
      <header className="site-header">
        <a className="wordmark" href="#top" aria-label="Enterprise KIP home">
          <span className="wordmark-mark" aria-hidden="true">
            EK
          </span>
          <span>Enterprise KIP</span>
        </a>
        <nav className="header-actions" aria-label="Project links">
          <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">
            GitHub <span aria-hidden="true"><ExternalIcon /></span>
          </a>
          <a href={API_DOCS_URL} target="_blank" rel="noreferrer">
            API Docs <span aria-hidden="true"><ExternalIcon /></span>
          </a>
        </nav>
      </header>

      <section className="hero" id="top" aria-labelledby="hero-title">
        <h1 id="hero-title">
          Enterprise <em>Knowledge Intelligence</em> Platform
        </h1>
        <p className="hero-subtitle">
          Production RAG over curated technical documentation
        </p>
        <p className="hero-description">
          Enterprise KIP retrieves evidence from a curated corpus of engineering
          documentation using Dense + BM25 hybrid retrieval, Weighted RRF,
          grounded generation, and citations.
        </p>
        <div className="pipeline" aria-label="Enterprise KIP query pipeline">
          {isActive ? (
            <span className="pulse" aria-hidden="true" />
          ) : null}
          {PIPELINE_STEPS.map((step, index) => (
            <Fragment key={step}>
              <span
                className={
                  index <= activePipelineStep ? "active" : undefined
                }
              >
                {step}
              </span>
              {index < PIPELINE_STEPS.length - 1 ? (
                <i aria-hidden="true">→</i>
              ) : null}
            </Fragment>
          ))}
        </div>
      </section>

      <div className="content-grid">
        <div className="main-column">
          <section className="panel corpus-panel" aria-labelledby="corpus-title">
            <div className="section-kicker">Indexed scope</div>
            <h2 id="corpus-title">What can Enterprise KIP answer?</h2>
            <p>
              Enterprise KIP searches a curated corpus of official technical
              documentation. It does not perform open-web search.
            </p>
            <div className="source-badges" aria-label="Indexed documentation sources">
              {CORPUS_SOURCES.map((source) => (
                <span key={source}>{source}</span>
              ))}
            </div>
            <div className="scope-note">
              <span aria-hidden="true">i</span>
              <div>
                <strong>Ask within the indexed scope</strong>
                <p>
                  Best results come from questions about the technologies
                  represented in this corpus. This demo answers from indexed
                  documentation rather than the general internet.
                </p>
              </div>
            </div>
          </section>

          <section className="examples" aria-labelledby="examples-title">
            <div className="section-heading">
              <div>
                <div className="section-kicker">Validated prompts</div>
                <h2 id="examples-title">Try an example</h2>
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

          <section className="query-section" aria-labelledby="query-title">
            <div className="query-header">
              <div>
                <div className="section-kicker">Live query</div>
                <h2 id="query-title">Ask the documentation</h2>
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
                rows={4}
                placeholder="Ask about Docker builds, Kubernetes operations, FastAPI patterns, vector search…"
                disabled={isActive}
              />
              <div className="form-footer">
                <span>
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
                    {isActive ? "Working…" : "Ask Enterprise KIP"}
                    <span aria-hidden="true">→</span>
                  </button>
                </div>
              </div>
            </form>

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
                        EK
                      </span>
                      <div>
                        <strong>Grounded answer</strong>
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
                        {renderAnswer(answer)}
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
                              <p className="source-excerpt">{source.excerpt}</p>
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
                              Open source <span aria-hidden="true"><ExternalIcon /></span>
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
        </div>

        <aside className="about-panel" aria-labelledby="about-title">
          <div className="section-kicker">About this demo</div>
          <h2 id="about-title">A production-minded RAG system</h2>
          <p>
            Enterprise KIP is an end-to-end RAG platform built around
            benchmark-driven hybrid retrieval, grounded generation, production
            observability, CI, and cloud deployment.
          </p>
          <dl>
            <div>
              <dt>Retrieval</dt>
              <dd>Dense + BM25</dd>
            </div>
            <div>
              <dt>Fusion</dt>
              <dd>Weighted RRF</dd>
            </div>
            <div>
              <dt>Vector store</dt>
              <dd>Qdrant</dd>
            </div>
            <div>
              <dt>API</dt>
              <dd>FastAPI</dd>
            </div>
          </dl>
          <div className="about-links">
            <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">
              GitHub Repository <span aria-hidden="true"><ExternalIcon /></span>
            </a>
            <a href={API_DOCS_URL} target="_blank" rel="noreferrer">
              API Documentation <span aria-hidden="true"><ExternalIcon /></span>
            </a>
          </div>
        </aside>
      </div>

      <footer>
        <span>© 2026 Nguyen Tam Thang. All rights reserved.</span>
        <span>Answers from curated documentation, not the open web.</span>
      </footer>
    </main>
  );
}
