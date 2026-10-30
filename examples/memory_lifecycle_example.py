"""
Memory lifecycle example.

Demonstrates inspect and semantic forget.

This is NOT experience transfer between models. Transfer
through export/import is a candidate for a future SDK
version.

State requirement:

    This example assumes a FRESH demo account. It records
    and compiles a belief, inspects memory, performs a
    semantic forget, and inspects again. If the account
    already contains state that prevents compilation, the
    example fails closed.

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
            {"key": "home_city", "value": "Berlin", "applicability": {}},
        )
        r = client.compile([event.id], use_llm=False)
        if not r.committed:
            raise RuntimeError(
                "Compilation produced zero committed beliefs. "
                "The account may contain state that blocks or "
                "conflicts with the event. Cause is not "
                "asserted here. Use a fresh demo account."
            )
        belief = r.committed[0]
        print("belief:", belief.value, "| key:", belief.semantic_key)

        memory = client.inspect()
        print("active beliefs before forget:", len(memory.active))

        result = client.forget_semantic(belief.semantic_key)
        print("forget result keys:", list(result.keys()))
        print("beliefs affected:", len(result.get("beliefs_affected", [])))
        print("replay status:", result.get("replay", {}).get("status"))

        memory = client.inspect()
        print("active beliefs after forget:", len(memory.active))


if __name__ == "__main__":
    main()