"""
Character consistency example.

Demonstrates how canonical preferences, corrections, and
rejections are represented in IGL and reach Gate.

Uses structured events only. No LLM provider is required.

State requirement:

    This example assumes a FRESH demo account. It runs the
    full lifecycle:

        create belief
        -> correct
        -> reject
        -> gate

    If the account already contains an active semantic block
    for the headwear key, compilation of the headwear belief
    produces zero committed beliefs and the example fails
    closed rather than silently skipping the reject step.

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

HEADWEAR_SEMANTIC_KEY = (
    'interaction_preference:headwear:{"character":"hero"}'
)


def main() -> None:
    if not USER_TOKEN:
        raise SystemExit(
            "IGL_USER_TOKEN is not set. Issue a fresh demo "
            "token via the server admin API and export it."
        )

    with IglClient(BASE, USER_TOKEN) as client:
        # 1. author establishes canon
        eye = client.record(
            "explicit_preference",
            {
                "key": "eye_color",
                "value": "blue",
                "applicability": {"character": "hero"},
            },
        )
        r = client.compile([eye.id], use_llm=False)
        if not r.committed:
            raise RuntimeError(
                "Compilation produced zero committed beliefs "
                "for eye_color. Use a fresh demo account."
            )
        print("initial:", r.committed[0].value)

        # 2. author corrects the canon
        r = client.correct(
            r.committed[0].id,
            {"key": "eye_color", "value": "green"},
            reason={"why": "author revised canon"},
        )
        print("after correct:", r.new_belief.value)
        print("superseded:", r.superseded_ids)

        # 3. author adds a headwear belief, then rejects it
        hat = client.record(
            "explicit_preference",
            {
                "key": "headwear",
                "value": "dark hood",
                "applicability": {"character": "hero"},
            },
        )
        r = client.compile([hat.id], use_llm=False)
        if not r.committed:
            raise RuntimeError(
                "Compilation produced zero committed beliefs "
                "for headwear. The account may contain an "
                "active semantic block or another policy "
                "restriction. Cause is not asserted here. "
                "Use a fresh demo account and re-run."
            )
        r = client.reject(
            r.committed[0].id,
            reason={"why": "author banned headwear"},
        )
        print("blocked key:", r.semantic_block.semantic_key)

        # 4. gate returns only what is applicable now
        gate = client.gate(
            purpose="scene_generation",
            context={"character": "hero"},
        )

        print("gate accepted:")
        for a in gate.accepted:
            print("  accepted:", a.belief.value)

        print("gate withheld:")
        for w in gate.withheld:
            print("  withheld:", w.belief_id, "|", w.reason)

         # reject() in SDK v0.1 creates a MEMORY-scope block.
        # Verified 2026-10-15: a MEMORY-scope block removes
        # the belief from gate.accepted and adds it to
        # gate.withheld with reason "user_semantic_block",
        # but it does NOT produce a generation constraint.
        #
        # A BOTH-scope block produces both effects: the belief
        # is withheld AND a matching GateConstraint appears in
        # gate.constraints (verified on the same date with
        # POST /semantic-blocks).
        #
        # The SDK does not expose scope in reject() in v0.1.
        # Generation constraints require /semantic-blocks
        # directly.
        print("gate constraints:", len(gate.constraints))
        for c in gate.constraints:
            print("  constraint:", c.kind.value, c.scope.value, c.semantic_key)

        # invariant: the rejected trait must not appear in accepted
        for a in gate.accepted:
            if a.belief.semantic_key == HEADWEAR_SEMANTIC_KEY:
                raise AssertionError(
                    "rejected trait leaked into gate.accepted"
                )


if __name__ == "__main__":
    main()