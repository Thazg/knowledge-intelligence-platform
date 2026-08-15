from __future__ import annotations

import pytest

from pydantic import ValidationError

from backend.core.config import Settings


def test_generation_timeout_defaults_to_120_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "GENERATION_TIMEOUT_SECONDS",
        raising=False,
    )

    settings = Settings(
        _env_file=None,
    )

    assert settings.generation_timeout_seconds == 120.0


def test_generation_timeout_can_be_loaded_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GENERATION_TIMEOUT_SECONDS",
        "45",
    )

    settings = Settings(
        _env_file=None,
    )

    assert settings.generation_timeout_seconds == 45.0


@pytest.mark.parametrize(
    "timeout_seconds",
    [
        0.0,
        -1.0,
    ],
)
def test_generation_timeout_must_be_positive(
    timeout_seconds: float,
) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            generation_timeout_seconds=timeout_seconds,
        )