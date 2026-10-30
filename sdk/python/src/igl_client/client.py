"""Synchronous HTTP client for IGL Memory.

The client is a thin layer over the public HTTP API. It does
NOT:
    - define trust
    - filter beliefs instead of Gate
    - implement local forget
    - perform local replay
    - access SQLite directly
    - expose admin endpoints

The server is the single source of authoritative memory
semantics.

Retry policy: the SDK NEVER auto-retries. A TransportError on
a mutating request does not imply the server did not execute
it. The caller decides whether to retry, and is responsible
for checking server state.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any

import httpx

from .errors import (
    IglError,
    TransportError,
    error_from_response,
)
from .models import (
    CompileResult,
    CorrectResult,
    CorrectRequest,
    CreateCompileRequest,
    CreateEventRequest,
    CreateGateRequest,
    Event,
    ForgetRequest,
    ForgetResult,
    GateResult,
    MemoryInspectResult,
    RejectRequest,
    RejectResult,
    SemanticForgetRequest,
)


_DEFAULT_CONNECT_TIMEOUT = 5.0
_DEFAULT_READ_TIMEOUT = 30.0


class IglClient:
    """Synchronous IGL Memory public API client.

    Parameters
    ----------
    base_url:
        Server base URL, e.g. "http://localhost:8000".
    token:
        Bearer token issued out of band. Never logged.
    http_client:
        Optional pre-built httpx.Client. If provided, the SDK
        does NOT own it and will not close it. Useful for
        httpx.MockTransport in tests.
    connect_timeout / read_timeout:
        Only used if http_client is not provided.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        http_client: httpx.Client | None = None,
        connect_timeout: float = _DEFAULT_CONNECT_TIMEOUT,
        read_timeout: float = _DEFAULT_READ_TIMEOUT,
    ) -> None:
        if http_client is not None:
            self._client = http_client
            self._owns_client = False
        else:
            self._client = httpx.Client(
                base_url=base_url.rstrip("/"),
                headers={"Authorization": f"Bearer {token}"},
                timeout=httpx.Timeout(
                    read_timeout,
                    connect=connect_timeout,
                ),
            )
            self._owns_client = True

    # --- lifecycle ----------------------------------------------------

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "IglClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # --- low-level request --------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
    ) -> Any:
        try:
            response = self._client.request(
                method,
                path,
                json=json_body,
            )
        except httpx.TransportError as exc:
            raise TransportError(
                f"transport error calling {method} {path}: {exc}"
            ) from exc

        if response.status_code >= 400:
            detail: Any
            try:
                payload = response.json()
                detail = payload.get("detail", payload)
            except Exception:
                detail = response.text
            raise error_from_response(
                response.status_code,
                f"{method} {path} -> {response.status_code}",
                detail=detail,
            )

        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    # --- health -------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """GET /health. No authentication required by the server,
        but the client still sends the bearer header if configured.
        """
        return self._request("GET", "/health")

    # --- events -------------------------------------------------------

    def record(
        self,
        event_type: str,
        content: dict[str, Any],
        *,
        sensitivity: str = "private",
        evidence_group: str | None = None,
    ) -> Event:
        body = CreateEventRequest(
            event_type=event_type,
            content=content,
            sensitivity=sensitivity,
            evidence_group=evidence_group,
        )
        raw = self._request("POST", "/events", json_body=body.model_dump())
        return Event.model_validate(raw)

    def forget_event(
        self,
        event_id: str,
        *,
        mode: str = "HARD_LOGICAL",
        reason: dict[str, Any] | None = None,
    ) -> ForgetResult:
        body = ForgetRequest(mode=mode, reason=reason or {})
        raw = self._request(
            "POST",
            f"/events/{event_id}/forget",
            json_body=body.model_dump(),
        )
        return ForgetResult.model_validate(raw)

    # --- compilation --------------------------------------------------

    def compile(
        self,
        event_ids: list[str],
        *,
        use_llm: bool = False,
    ) -> CompileResult:
        body = CreateCompileRequest(event_ids=event_ids, use_llm=use_llm)
        raw = self._request("POST", "/compile", json_body=body.model_dump())
        return CompileResult.model_validate(raw)

    # --- gate ---------------------------------------------------------

    def gate(
        self,
        purpose: str,
        *,
        context: dict[str, Any] | None = None,
        limit: int = 20,
    ) -> GateResult:
        body = CreateGateRequest(
            purpose=purpose,
            context=context or {},
            limit=limit,
        )
        raw = self._request("POST", "/gate/query", json_body=body.model_dump())
        return GateResult.model_validate(raw)

    # --- sovereignty --------------------------------------------------

    def correct(
        self,
        belief_id: str,
        value: dict[str, Any],
        *,
        reason: dict[str, Any] | None = None,
    ) -> CorrectResult:
        body = CorrectRequest(value=value, reason=reason or {})
        raw = self._request(
            "POST",
            f"/beliefs/{belief_id}/correct",
            json_body=body.model_dump(),
        )
        return CorrectResult.model_validate(raw)

    def reject(self, belief_id, *, reason=None) -> RejectResult:
        body = RejectRequest(reason=reason or {})
        raw = self._request("POST", f"/beliefs/{belief_id}/reject", json_body=body.model_dump())
        return RejectResult.model_validate(raw)


    def forget_semantic(self, semantic_key, *, mode="HARD_LOGICAL", reason=None):
        body = SemanticForgetRequest(semantic_key=semantic_key, mode=mode, reason=reason or {})
        return self._request("POST", "/memory/forget-semantic", json_body=body.model_dump())

    # --- inspect ------------------------------------------------------

    def inspect(self) -> MemoryInspectResult:
        raw = self._request("GET", "/memory")
        return MemoryInspectResult.model_validate(raw)
