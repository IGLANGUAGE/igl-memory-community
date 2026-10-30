# IGL Memory — Public Contract

This document describes the four behavioral guarantees
that IGL Memory provides. These are guarantees of behavior,
not implementation details. They can be verified by
running `verify/smoke_sdk_live.py` against your own
instance.

## 1. Correction

When a belief is corrected, the previous value is no longer
used in the current context.

The old value remains in history (append-only). The new
value becomes the authoritative one. Gate returns only
the corrected value for the current context.

## 2. Forget

Forgotten information is not returned after a supported
replay.

When a semantic forget is performed, source events at or
before the cutoff are no longer replayable for that
semantic key. A subsequent replay cannot reconstruct the
forgotten information.

## 3. Reject

A rejected interpretation does not appear in Gate accepted
output.

When a belief is rejected, a semantic block is created for
its semantic key. Gate withholds the blocked belief. The
block survives recompilation and cross-generation
activation.

## 4. Ownership

A user cannot access another user's memory, even with known
IDs.

All user-facing endpoints are authenticated. Ownership is
established by the credential, not by request bodies. Cross-
user access returns the same failure as a nonexistent
resource.

## What this contract does not promise

- Cryptographic erasure of data from all storage media.
- Physical deletion from backups, WAL, or OS caches.
- Guarantees that an arbitrary LLM will follow the
  generation constraints it receives.
- Correctness of the LLM extractor when `use_llm=true`.

These are beyond the scope of the Community v0.1 edition.