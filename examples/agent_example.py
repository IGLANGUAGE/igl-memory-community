"""
Minimal agent memory example.

The SDK does not generate assistant responses. It provides a
memory context that an application can use when generating
its own responses.

Uses structured events with deterministic compilation. No
LLM provider is required.

State requirement:

    This example assumes a FRESH demo account. It records a
    structured event, compiles it into a belief, and reads
    the Gate context. If the account already contains state
    that prevents compilation, the example fails closed
    rather than silently skipping steps.

    To run this example repeatedly, issue a new token for a
    new user_id via the server's admin issuance endpoint.
    The SDK does not create users or issue tokens.

Environment:

    IGL_BASE_URL     optional, default http://localhost:8000
    IGL_USER_TOKEN   required, a fresh user bearer token
"""

import os
from igl_client import IglClient


BASE = os.environ.get("IGL_BASE_URL", "http://localhost:8000")
USER_TOKEN = os.environ.get("IGL_USER_TOKEN")


def main() -> None:
    if not USER_TOKEN:
        raise SystemExit(
            "IGL_USER_TOKEN is not set. Issue a fresh demo "
            "token via the server admin API and export it."
        )

    with IglClient(BASE, USER_TOKEN) as client:
        event = client.record(
            "explicit_preference",
            {
                "key": "response_style",
                "value": "concise",
                "applicability": {"mode": "coding"},
            },
        )

        result = client.compile([event.id], use_llm=False)
        if not result.committed:
            raise RuntimeError(
                "Compilation produced zero committed beliefs. "
                "The account may contain state that blocks or "
                "conflicts with the event. Cause is not "
                "asserted here. Use a fresh demo account."
            )

        print("compiled beliefs:")
        for b in result.committed:
            print(" ", b.id, b.status.value, b.value)

        gate = client.gate(
            purpose="assistant_response",
            context={"mode": "coding"},
        )

        print("gate accepted:")
        for a in gate.accepted:
            print("  accepted:", a.belief.value)

        print("gate withheld:")
        for w in gate.withheld:
            print("  withheld:", w.belief_id, "|", w.reason)

        print("gate constraints:", len(gate.constraints))
        for c in gate.constraints:
            print("  constraint:", c.kind.value, c.scope.value, c.semantic_key)


if __name__ == "__main__":
    main()