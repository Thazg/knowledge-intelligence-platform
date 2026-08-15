from __future__ import annotations

import httpx
import pytest

from backend.generation.models import GenerationContext
from backend.generation.providers.ollama_generator import (
    OllamaGenerator,
)
from backend.core.errors import (
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