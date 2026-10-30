# igl_client

Public Python client for **IGL Memory** — an epistemic memory
layer for AI agents and other long-running systems.

The client is a thin HTTP wrapper. It does **not** define
trust, filter beliefs, implement local forget, perform local
replay, or access the server's database. All memory semantics
live on the server.

- SDK version: 0.1.0
- Server contract: OpenAPI 3.1.0 (snapshot at `sdk/openapi.json`)
- Status: locally installable, documented, tested. Not yet
  packaged for public release.

---

## 1. What this client is (and is not)

The client is a thin layer over the public HTTP API.

It **is**:

- a synchronous Python client for the 9 core public endpoints;
- typed: request and response models are Pydantic v2;
- independent: it never imports from the server package `app`;
- explicit about errors: every HTTP failure maps to a typed
  exception;
- honest about transport: no automatic retry, because a
  timeout on a mutating request does not tell us whether the
  server executed it.

It is **not**:

- a memory engine — semantics live on the server;
- an LLM client — it does not call OpenAI, AITunnel, or any
  other provider;
- a bypass for Gate, trust, rejection, or forget — those are
  enforced on the server;
- an admin tool — admin endpoints (token issuance, backup,
  restore) are intentionally not exposed.

---

## 2. Install

From the repository root (`igl-memory/`):

pip install -e ./sdk/python

Verify:

```python
import igl_client
print(igl_client.__version__ if hasattr(igl_client, "__version__") else "ok") 
```

The package name for import is igl_client. The distribution
name for pip is igl-client.

## 3. Authentication and ownership

Every user-facing endpoint requires a bearer token:

    Authorization: Bearer <token>

The bearer token determines **who** the caller is. The client
never sends a `user_id` in request bodies; ownership is
established by the credential on the server side.

### 3.1 How to obtain a token

Token issuance is an **admin** operation on the server and is
**not** part of SDK v0.1. Do the following **outside** the
application that uses the SDK:

1. On a trusted machine with the server's `IGL_ADMIN_KEY`,
   issue a user token via the admin HTTP endpoint.
2. Pass the resulting token to the SDK via
   `IGL_USER_TOKEN` (for examples) or via your application's
   own secret management.

Example admin-side issuance (run once, outside the SDK):

```python
import os
import httpx

BASE = "http://localhost:8000"
ADMIN_KEY = os.environ["IGL_ADMIN_KEY"]      # server-side secret
USER_ID = "sdk-demo-001"

with httpx.Client(base_url=BASE, timeout=10.0) as raw:
    r = raw.post(
        "/auth/token",
        json={"user_id": USER_ID},
        headers={"Authorization": f"Bearer {ADMIN_KEY}"},
    )
    r.raise_for_status()
    print(r.json()["token"])
```

### 3.2 Security warning
The admin credential (IGL_ADMIN_KEY) is a server-side
secret.

Never embed it in a client application.

Never commit it to source control.

Never log it.

Never ship it inside a package or an example.

In production, user tokens must be issued by a trusted server
component, not by the application that uses the SDK.

---

## 4. Quick start

``` python
from igl_client import IglClient

with IglClient(base_url="http://localhost:8000", token=token) as client:
    
    # 1. record a structured event (M)

    event = client.record(
        "explicit_preference",
        {"key": "favorite_color", "value": "blue", "applicability": {}},
    )

    # 2. compile it into a belief (D)

    result = client.compile([event.id], use_llm=False)
    for belief in result.committed:
        print(belief.id, belief.status.value, belief.value)

    # 3. ask Gate what is applicable here and now

    gate = client.gate(purpose="assistant_response", context={"mode": "casual"})
    for a in gate.accepted:
        print("accepted:", a.belief.value)
    for w in gate.withheld:
        print("withheld:", w.belief_id, w.reason)
    for c in gate.constraints:
        print("constraint:", c.kind.value, c.semantic_key)
```
---

## 5. Public methods (v0.1)

The SDK exposes nine methods. All other endpoints are
intentionally out of scope for v0.1 (see section 8).

### health
``` python
client.health()  # -> dict
```
Returns {"status": "ok", "architecture": "..."}. No
authentication required by the server.


### record
``` python
event = client.record(
    event_type: str,
    content: dict,
    *,
    sensitivity: str = "private",
    evidence_group: str | None = None,
)  # -> Event
```

Writes an event (M). The content shape depends on
event_type. For explicit_preference, the deterministic
compiler expects {"key": ..., "value": ..., "applicability": {...}}.
For other event types, the shape must match what the server's
compiler or LLM extractor expects.

### compile
``` python
result = client.compile(
    event_ids: list[str],
    *,
    use_llm: bool = False,
)  # -> CompileResult
```

Compiles one or more events into beliefs (D).

use_llm=False uses the deterministic compiler. Raw natural
language will not produce beliefs in this mode.

use_llm=True calls the configured LLM extractor on the
server side. This requires the server to be configured with
an LLM provider key. The SDK itself does not call any LLM.

### gate
``` python
gate = client.gate(
    purpose: str,
    *,
    context: dict | None = None,
    limit: int = 20,
)  # -> GateResult
```

Asks the server which beliefs are applicable for a given
purpose and context. Returns three independent lists:

accepted — beliefs the server has decided are trusted and
applicable;

withheld — beliefs the server has decided are not to be
applied here (with a reason);

constraints — generation constraints derived from the
user's rejection state.

The SDK preserves all three lists. Do not flatten them.

### correct
``` python
result = client.correct(
    belief_id: str,
    value: dict,
    *,
    reason: dict | None = None,
)  # -> CorrectResult
```

Appends a correction for an existing belief. The old belief
becomes SUPERSEDED; the new belief becomes ACTIVE.

The value shape must be compatible with the existing
belief's value field. The server derives the semantic key
from the existing belief, not from the request.

### reject
``` python
result = client.reject(
    belief_id: str,
    *,
    reason: dict | None = None,
)  # -> RejectResult
```

Creates a semantic block for the belief's semantic key. The
belief is not deleted; it is prevented from being applied.
The block survives recompilation and is cross-generation.

### forget_event
``` python
result = client.forget_event(
    event_id: str,
    *,
    mode: str = "HARD_LOGICAL",
    reason: dict | None = None,
)  # -> ForgetResult
```

Forgets a single event (M). Only HARD_LOGICAL is supported
in v1. Physical erasure is not promised.

### forget_semantic
``` python
result = client.forget_semantic(
    semantic_key: str,
    *,
    mode: str = "HARD_LOGICAL",
    reason: dict | None = None,
)  # -> dict
```

Semantic forget. Applies a historical cutoff for the
semantic key. Events at or before the cutoff are no longer
replayable for that key. Post-epoch learning under the same
key is allowed (C7).

Returns the raw server payload, which includes the marker
id, the cutoff, the affected beliefs, and the replay outcome.

### inspect
``` python
result = client.inspect()  # -> MemoryInspectResult
```

Returns the user's current memory view: active beliefs,
candidates, suspects, history, semantic blocks, and
generations.


## 6. Error handling

All HTTP errors map to typed exceptions in igl_client.errors:

400  BadRequest
401  AuthenticationError
403  ForbiddenError
404  NotFoundError
409  ConflictError
410  GoneError
422  ValidationError
503  ServiceUnavailable
(other)  IglError
Each exception carries:

status_code: int | None;

message: str;

detail: object | None.

The exceptions do not include the Authorization header or
any other secret in str() or repr().

Example:

``` python
from igl_client import NotFoundError, TransportError

try:
    client.correct("d_missing", {"key": "color", "value": "green"})
except NotFoundError as exc:
    print("no such belief:", exc.status_code, exc.detail)
except TransportError as exc:
    print("network problem:", exc)
```

## 7. Timeout and retry policy

Default timeouts:

connect: 5 seconds;

read: 30 seconds.

Configurable via IglClient(..., connect_timeout=..., read_timeout=...).

The SDK never auto-retries. This is a deliberate design
choice:

On a mutating request, a network timeout does not tell
us whether the server executed the operation.

The server is transactionally atomic (Gate D), but HTTP is
not idempotent. An automatic retry could duplicate an
event, double-compile, or re-trigger a supersession.

If you need to retry a mutating request, do so explicitly,
and verify the server state first via inspect().

## 8. Explicitly out of scope for v0.1

Admin endpoints: token issuance, backup, restore.
Export / import.
Trust lifecycle (validate / challenge / invalidate / restore).
Semantic block management (create / list / delete).
Generation management (list / get / recompile / activate).
Asynchronous client.
Node, Go, or other language clients.
Token persistence.
Client-side caching of Gate results.
Any client-side policy enforcement.

## 9. Contract and compatibility

The public contract is fixed in sdk/SDK_CONTRACT.md, derived
from sdk/openapi.json (an OpenAPI 3.1.0 snapshot).

Tests live in tests/sdk/:

test_all_exports.py — every name in igl_client.__all__
exists.
test_errors.py — HTTP status mapping, secret non-leakage.
test_transport.py — timeout → TransportError, no
auto-retry.
test_models.py — request/response shape, reason={} not
null.
test_lifecycle.py — owned vs injected httpx.Client.
test_client_mock.py — 9 methods through httpx.MockTransport.
test_contract.py — SDK models vs sdk/openapi.json.
test_openapi_snapshot.py — app.openapi() vs snapshot.
test_live.py — opt-in live tests (-m live).

Run the mock suite:

pytest tests/sdk/ -q
Run live tests (requires a running server and IGL_ADMIN_KEY
in the environment):

pytest tests/sdk/ -q -m live

## 10. What is not promised

The SDK does not guarantee that the LLM extractor produces
correct beliefs from raw text. It only sends the request.
The SDK does not guarantee that Gate accepts or rejects any
particular belief. Gate semantics live on the server.
The SDK does not guarantee that a mutating request that
timed out did or did not execute on the server.
The SDK does not implement any client-side memory behaviour.