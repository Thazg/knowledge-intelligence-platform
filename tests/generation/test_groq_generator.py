from __future__ import annotations

import threading

import httpx
import pytest

from backend.core.errors import (
    DependencyBusyError,
    DependencyResponseError,
    DependencyTimeoutError,
    DependencyUnavailableError,
)
from backend.generation.models import (
    GenerationContext,
    SourceReference,
)
from backend.generation.providers.groq_generator import (
    GroqGenerator,
)


def _context() -> GenerationContext:
    return GenerationContext(
        query="What is Kubernetes?",
        context_text=(
            "[1] Kubernetes is a "
            "container orchestration system."
        ),
        sources=[
            SourceReference(
                citation_id="1",
                document_id="doc-1",
                chunk_id="chunk-1",
                title="Kubernetes",
            )
        ],
        token_count=20,
    )


def _generator(
    *,
    model: str = "openai/gpt-oss-20b",
    max_concurrent_generations: int = 1,
) -> GroqGenerator:
    return GroqGenerator(
        model=model,
        api_key="test-secret",
        max_concurrent_generations=(
            max_concurrent_generations
        ),
    )


def test_generate_sends_expected_gpt_oss_chat_completion_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_post(
        _client: httpx.Client,
        url: str,
        **kwargs: object,
    ) -> httpx.Response:
        captured["url"] = url
        captured.update(kwargs)

        request = httpx.Request(
            "POST",
            url,
        )

        return httpx.Response(
            status_code=200,
            request=request,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Kubernetes manages "
                                "containers [1]."
                            )
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 20,
                    "total_tokens": 120,
                },
            },
        )

    monkeypatch.setattr(
        httpx.Client,
        "post",
        fake_post,
    )

    result = _generator().generate(
        _context()
    )

    assert captured["url"] == (
        "https://api.groq.com/openai/v1/"
        "chat/completions"
    )

    headers = captured["headers"]

    assert isinstance(
        headers,
        dict,
    )
    assert headers["Authorization"] == (
        "Bearer test-secret"
    )

    payload = captured["json"]

    assert isinstance(
        payload,
        dict,
    )
    assert payload["model"] == (
        "openai/gpt-oss-20b"
    )
    assert payload["stream"] is False
    assert payload["temperature"] == 0.0
    assert (
        payload["max_completion_tokens"]
        == 1024
    )
    assert payload["reasoning_effort"] == (
        "low"
    )
    assert payload["include_reasoning"] is False

    messages = payload["messages"]

    assert isinstance(
        messages,
        list,
    )
    assert messages[0]["role"] == (
        "system"
    )
    assert messages[1]["role"] == (
        "user"
    )

    assert result.answer == (
        "Kubernetes manages "
        "containers [1]."
    )
    assert result.prompt_tokens == 100
    assert result.completion_tokens == 20
    assert result.total_tokens == 120
    assert result.metadata[
        "provider"
    ] == "groq"


def test_non_gpt_oss_payload_does_not_send_gpt_oss_reasoning_options() -> None:
    generator = _generator(
        model="qwen/qwen3.6-27b",
    )

    payload = generator._build_payload(
        system_prompt="system",
        user_prompt="user",
    )

    assert (
        payload["max_completion_tokens"]
        == 1024
    )
    assert "reasoning_effort" not in payload
    assert "include_reasoning" not in payload


def test_generate_maps_valid_citations() -> None:
    generator = _generator()

    citations = (
        generator._extract_citations(
            answer=(
                "Supported by [1], "
                "again [1], ignore [99]."
            ),
            context=_context(),
        )
    )

    assert len(citations) == 1
    assert (
        citations[0].citation_id
        == "1"
    )
    assert (
        citations[0].document_id
        == "doc-1"
    )
    assert (
        citations[0].chunk_id
        == "chunk-1"
    )


def test_generate_translates_connect_error_to_dependency_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request(
        "POST",
        (
            "https://api.groq.com/"
            "openai/v1/chat/completions"
        ),
    )

    def fail_post(
        _client: httpx.Client,
        _url: str,
        **_kwargs: object,
    ) -> httpx.Response:
        raise httpx.ConnectError(
            "Groq unavailable",
            request=request,
        )

    monkeypatch.setattr(
        httpx.Client,
        "post",
        fail_post,
    )

    with pytest.raises(
        DependencyUnavailableError,
    ) as exc_info:
        _generator().generate(
            _context()
        )

    assert (
        exc_info.value.dependency
        == "groq"
    )
    assert isinstance(
        exc_info.value.__cause__,
        httpx.ConnectError,
    )


def test_generate_translates_timeout_to_dependency_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request(
        "POST",
        (
            "https://api.groq.com/"
            "openai/v1/chat/completions"
        ),
    )

    def fail_post(
        _client: httpx.Client,
        _url: str,
        **_kwargs: object,
    ) -> httpx.Response:
        raise httpx.ReadTimeout(
            "Groq timed out",
            request=request,
        )

    monkeypatch.setattr(
        httpx.Client,
        "post",
        fail_post,
    )

    with pytest.raises(
        DependencyTimeoutError,
    ) as exc_info:
        _generator().generate(
            _context()
        )

    assert (
        exc_info.value.dependency
        == "groq"
    )
    assert isinstance(
        exc_info.value.__cause__,
        httpx.TimeoutException,
    )


def test_generate_translates_http_error_to_dependency_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request(
        "POST",
        (
            "https://api.groq.com/"
            "openai/v1/chat/completions"
        ),
    )

    response = httpx.Response(
        status_code=429,
        request=request,
    )

    def fail_post(
        _client: httpx.Client,
        _url: str,
        **_kwargs: object,
    ) -> httpx.Response:
        return response

    monkeypatch.setattr(
        httpx.Client,
        "post",
        fail_post,
    )

    with pytest.raises(
        DependencyResponseError,
    ) as exc_info:
        _generator().generate(
            _context()
        )

    assert (
        exc_info.value.dependency
        == "groq"
    )
    assert isinstance(
        exc_info.value.__cause__,
        httpx.HTTPStatusError,
    )


def test_generate_translates_malformed_payload_to_dependency_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(
        _client: httpx.Client,
        url: str,
        **_kwargs: object,
    ) -> httpx.Response:
        request = httpx.Request(
            "POST",
            url,
        )

        return httpx.Response(
            status_code=200,
            request=request,
            json={
                "choices": [],
            },
        )

    monkeypatch.setattr(
        httpx.Client,
        "post",
        fake_post,
    )

    with pytest.raises(
        DependencyResponseError,
    ) as exc_info:
        _generator().generate(
            _context()
        )

    assert (
        exc_info.value.dependency
        == "groq"
    )


def test_generate_translates_blank_content_to_dependency_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(
        _client: httpx.Client,
        url: str,
        **_kwargs: object,
    ) -> httpx.Response:
        request = httpx.Request(
            "POST",
            url,
        )

        return httpx.Response(
            status_code=200,
            request=request,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "reasoning": (
                                "Internal reasoning."
                            ),
                        },
                        "finish_reason": (
                            "length"
                        ),
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 1024,
                    "total_tokens": 1124,
                },
            },
        )

    monkeypatch.setattr(
        httpx.Client,
        "post",
        fake_post,
    )

    with pytest.raises(
        DependencyResponseError,
    ) as exc_info:
        _generator().generate(
            _context()
        )

    assert (
        exc_info.value.dependency
        == "groq"
    )
    assert isinstance(
        exc_info.value.__cause__,
        ValueError,
    )


def test_generate_rejects_second_request_when_generation_is_busy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = _generator(
        max_concurrent_generations=1,
    )

    first_request_started = (
        threading.Event()
    )
    allow_first_request_to_finish = (
        threading.Event()
    )

    post_call_count = 0
    first_request_errors: list[
        BaseException
    ] = []

    def blocking_post(
        _client: httpx.Client,
        url: str,
        **_kwargs: object,
    ) -> httpx.Response:
        nonlocal post_call_count

        post_call_count += 1

        request = httpx.Request(
            "POST",
            url,
        )

        first_request_started.set()

        assert (
            allow_first_request_to_finish
            .wait(
                timeout=2.0,
            )
        )

        return httpx.Response(
            status_code=200,
            request=request,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Kubernetes [1]."
                            )
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                },
            },
        )

    monkeypatch.setattr(
        httpx.Client,
        "post",
        blocking_post,
    )

    def run_first_request() -> None:
        try:
            generator.generate(
                _context()
            )
        except BaseException as exc:
            first_request_errors.append(
                exc
            )

    first_thread = threading.Thread(
        target=run_first_request,
    )

    first_thread.start()

    assert first_request_started.wait(
        timeout=2.0,
    )

    with pytest.raises(
        DependencyBusyError,
    ) as exc_info:
        generator.generate(
            _context()
        )

    assert (
        exc_info.value.dependency
        == "groq"
    )

    allow_first_request_to_finish.set()

    first_thread.join(
        timeout=2.0,
    )

    assert not first_thread.is_alive()
    assert first_request_errors == []

    result = generator.generate(
        _context()
    )

    assert result.answer == (
        "Kubernetes [1]."
    )
    assert post_call_count == 2


@pytest.mark.parametrize(
    (
        "model",
        "api_key",
        "base_url",
        "timeout_seconds",
        "max_concurrent",
    ),
    [
        ("", "key", "https://x", 120.0, 1),
        ("model", "", "https://x", 120.0, 1),
        ("model", "key", "", 120.0, 1),
        ("model", "key", "https://x", 0.0, 1),
        ("model", "key", "https://x", 120.0, 0),
    ],
)
def test_constructor_rejects_invalid_configuration(
    model: str,
    api_key: str,
    base_url: str,
    timeout_seconds: float,
    max_concurrent: int,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        GroqGenerator(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=(
                timeout_seconds
            ),
            max_concurrent_generations=(
                max_concurrent
            ),
        )