from __future__ import annotations


class DependencyUnavailableError(RuntimeError):
    def __init__(self, dependency: str) -> None:
        self.dependency = dependency
        super().__init__(f"{dependency} is unavailable")