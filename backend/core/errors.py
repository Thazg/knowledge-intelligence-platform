from __future__ import annotations


class DependencyError(RuntimeError):
    def __init__(
        self,
        dependency: str,
        message: str,
    ) -> None:
        self.dependency = dependency
        super().__init__(message)


class DependencyUnavailableError(DependencyError):
    def __init__(self, dependency: str) -> None:
        super().__init__(
            dependency=dependency,
            message=f"{dependency} is unavailable",
        )


class DependencyTimeoutError(DependencyError):
    def __init__(self, dependency: str) -> None:
        super().__init__(
            dependency=dependency,
            message=f"{dependency} timed out",
        )


class DependencyResponseError(DependencyError):
    def __init__(self, dependency: str) -> None:
        super().__init__(
            dependency=dependency,
            message=f"{dependency} returned an error",
        )