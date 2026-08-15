from __future__ import annotations

import httpx
import pytest
import threading

from backend.generation.models import GenerationContext
from backend.generation.providers.ollama_generator import (
    OllamaGenerator,
)
from backend.core.errors import (
    DependencyBusyError,
    DependencyResponseError,
    DependencyTimeoutError,
    DependencyUnavailableError,
)


def test_generate_translates_connect_error_to_dependency_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = OllamaGenerator(
        model="qwen3:4b-instruct",
        base_url="http://ollama:11434",
    )

    context = GenerationContext(
        query="What is Kubernetes?",
        context_text="Kubernetes documentation.",
        sources=[],
    )

    request = httpx.Request(
        "POST",
        "http://ollama:11434/api/chat",
    )

    def fail_post(
        _client: httpx.Client,
        _url: str,
        **_kwargs: object,
    ) -> httpx.Response:
        raise httpx.ConnectError(
            "Ollama unavailable",
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
        generator.generate(context)

    assert exc_info.value.dependency == "ollama"
    assert isinstance(
        exc_info.value.__cause__,
        httpx.ConnectError,
    )

def test_generate_translates_timeout_to_dependency_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = OllamaGenerator(
        model="qwen3:4b-instruct",
        base_url="http://ollama:11434",
    )

    context = GenerationContext(
        query="What is Kubernetes?",
        context_text="Kubernetes documentation.",
        sources=[],
    )

    request = httpx.Request(
        "POST",
        "http://ollama:11434/api/chat",
    )

    def fail_post(
        _client: httpx.Client,
        _url: str,
        **_kwargs: object,
    ) -> httpx.Response:
        raise httpx.ReadTimeout(
            "Ollama timed out",
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
        generator.generate(context)

    assert exc_info.value.dependency == "ollama"
    assert isinstance(
        exc_info.value.__cause__,
        httpx.TimeoutException,
    )
    
def test_generate_translates_http_error_to_dependency_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = OllamaGenerator(
        model="qwen3:4b-instruct",
        base_url="http://ollama:11434",
    )

    context = GenerationContext(
        query="What is Kubernetes?",
        context_text="Kubernetes documentation.",
        sources=[],
    )

    request = httpx.Request(
        "POST",
        "http://ollama:11434/api/chat",
    )

    response = httpx.Response(
        status_code=500,
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
        generator.generate(context)

    assert exc_info.value.dependency == "ollama"
    assert isinstance(
        exc_info.value.__cause__,
        httpx.HTTPStatusError,
    )

def test_generate_rejects_second_request_when_generation_is_busy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = OllamaGenerator(
        model="qwen3:4b-instruct",
        base_url="http://ollama:11434",
        max_concurrent_generations=1,
    )

    context = GenerationContext(
        query="What is Qdrant?",
        context_text="",
        sources=[],
        token_count=0,
    )

    first_request_started = threading.Event()
    allow_first_request_to_finish = threading.Event()

    post_call_count = 0
    first_request_errors: list[BaseException] = []

    def blocking_post(
        self: httpx.Client,
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

        assert allow_first_request_to_finish.wait(
            timeout=2.0,
        )

        return httpx.Response(
            status_code=200,
            request=request,
            json={
                "message": {
                    "content": "Qdrant is available."
                },
                "prompt_eval_count": 10,
                "eval_count": 5,
            },
        )

    monkeypatch.setattr(
        httpx.Client,
        "post",
        blocking_post,
    )

    def run_first_request() -> None:
        try:
            generator.generate(context)
        except BaseException as exc:
            first_request_errors.append(exc)

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
        generator.generate(context)

    assert exc_info.value.dependency == "ollama"

    # Request #2 must be rejected before touching Ollama.
    assert post_call_count == 1

    allow_first_request_to_finish.set()

    first_thread.join(
        timeout=2.0,
    )

    assert not first_thread.is_alive()
    assert first_request_errors == []

    # The slot must have been released after request #1.
    result = generator.generate(context)

    assert result.answer == "Qdrant is available."
    assert post_call_count == 2