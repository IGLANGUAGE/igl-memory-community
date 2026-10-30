"""Typed exceptions for the IGL Memory SDK v0.1.

Every HTTP error response is mapped to a typed exception.
Unknown statuses also produce a typed exception, never a bare
Exception and never a silently ignored response.

Transport errors (network failure, timeout) are a distinct
class. They do NOT imply the server rejected the request,
only that the client did not receive a response. See the SDK
contract (section 6) for the retry policy.
"""

from __future__ import annotations

from typing import Any


class IglError(Exception):
    """Base class for all SDK exceptions."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        detail: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"status_code={self.status_code!r}, "
            f"message={self.message!r})"
        )


class TransportError(IglError):
    """Network or timeout error. Server response unknown.

    A TransportError on a mutating request does NOT imply the
    server did not execute it. The SDK never auto-retries.
    """


class BadRequest(IglError):
    """HTTP 400 - invalid request body or domain rejection."""


class AuthenticationError(IglError):
    """HTTP 401 - missing, malformed, or unknown credential."""


class ForbiddenError(IglError):
    """HTTP 403 - ownership violation."""


class NotFoundError(IglError):
    """HTTP 404 - resource not found or not owned by caller."""


class ConflictError(IglError):
    """HTTP 409 - state conflict (e.g. non-empty import target)."""


class GoneError(IglError):
    """HTTP 410 - resource forgotten (deleted_at is set)."""


class ValidationError(IglError):
    """HTTP 422 - malformed payload / schema mismatch."""


class ServiceUnavailable(IglError):
    """HTTP 503 - admin endpoint without configured admin key."""


_STATUS_MAP: dict[int, type[IglError]] = {
    400: BadRequest,
    401: AuthenticationError,
    403: ForbiddenError,
    404: NotFoundError,
    409: ConflictError,
    410: GoneError,
    422: ValidationError,
    503: ServiceUnavailable,
}


def error_from_response(
    status_code: int,
    message: str,
    detail: Any = None,
) -> IglError:
    cls = _STATUS_MAP.get(status_code, IglError)
    return cls(message, status_code=status_code, detail=detail)
