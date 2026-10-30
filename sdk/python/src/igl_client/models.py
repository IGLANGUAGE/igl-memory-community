"""Pydantic models for the IGL Memory SDK v0.1.

Every response model uses extra="allow" so that additive
server-side extensions do not silently drop data. Request
models use extra="forbid" and match the OpenAPI snapshot
exactly.

These models are OWNED by the SDK. They are NOT imported from
app.models. The SDK never depends on the server's internal
Python package.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# --- enums -------------------------------------------------------------


class AuthorityClass(str, Enum):
    DIRECT_USER = "DIRECT_USER"
    OBSERVATION = "OBSERVATION"
    INFERENCE = "INFERENCE"
    EXTERNAL = "EXTERNAL"
    LEGACY = "LEGACY"


class BeliefStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    SUSPECT = "SUSPECT"
    INVALID = "INVALID"
    USER_REJECTED = "USER_REJECTED"
    SUPERSEDED = "SUPERSEDED"


class ConstraintKind(str, Enum):
    EXCLUDE = "EXCLUDE"
    REQUIRE = "REQUIRE"
    PREFER = "PREFER"
    AVOID = "AVOID"


class ConstraintScope(str, Enum):
    MEMORY = "MEMORY"
    GENERATION = "GENERATION"
    BOTH = "BOTH"


class GenerationStatus(str, Enum):
    BUILDING = "BUILDING"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"
    FAILED = "FAILED"


# --- response base -----------------------------------------------------


class _ResponseModel(BaseModel):
    """Base class for all SDK response models.

    extra="allow" preserves unknown fields returned by the
    server so that additive schema extensions do not silently
    drop data on the client side.
    """

    model_config = ConfigDict(extra="allow")


# --- response models ---------------------------------------------------


class Event(_ResponseModel):
    id: str
    user_id: str
    created_at: str
    event_type: str
    content: dict[str, Any]
    sensitivity: str
    evidence_group: str | None = None
    deleted_at: str | None = None


class Belief(_ResponseModel):
    id: str
    user_id: str
    generation_id: str
    belief_type: str
    semantic_key: str
    authority: AuthorityClass
    value: dict[str, Any]
    status: BeliefStatus
    confidence: float
    uncertainty: float | None
    event_count: int
    evidence_count: int
    applicability: dict[str, Any]
    created_at: str
    last_validated_at: str | None


class BeliefProposal(_ResponseModel):
    user_id: str
    belief_type: str
    value: dict[str, Any]
    authority: AuthorityClass
    confidence: float = Field(ge=0.0, le=1.0)
    semantic_key: str
    applicability: dict[str, Any] = Field(default_factory=dict)
    source_event_ids: list[str] = Field(default_factory=list)


class EvidenceProposal(_ResponseModel):
    user_id: str
    belief_type: str
    semantic_key: str
    value: dict[str, Any]
    authority: AuthorityClass
    evidence_group: str
    applicability: dict[str, Any] = Field(default_factory=dict)
    source_event_ids: list[str] = Field(default_factory=list)


class CompileResult(_ResponseModel):
    proposals: list[dict[str, Any]]
    committed: list[Belief]
    superseded_ids: list[str]


class GateAccepted(_ResponseModel):
    belief: Belief
    trusted: bool
    applicable: bool
    reason: str


class GateWithheld(_ResponseModel):
    belief_id: str
    reason: str


class GateConstraint(_ResponseModel):
    semantic_key: str
    kind: ConstraintKind
    scope: ConstraintScope
    reason: str
    source: str
    target: str | None = None
    value: Any | None = None


class GateResult(_ResponseModel):
    accepted: list[GateAccepted]
    withheld: list[GateWithheld]
    constraints: list[GateConstraint] = Field(default_factory=list)


class CorrectResult(_ResponseModel):
    event: Event
    new_belief: Belief
    superseded_ids: list[str] = Field(default_factory=list)


class SemanticBlock(_ResponseModel):
    id: str
    user_id: str
    semantic_key: str
    created_at: str
    removed_at: str | None
    source_event_id: str | None
    reason: dict[str, Any]
    kind: ConstraintKind = ConstraintKind.EXCLUDE
    scope: ConstraintScope = ConstraintScope.MEMORY
    generation_target: str | None = None


class RejectResult(_ResponseModel):
    belief: Belief
    semantic_block: SemanticBlock


class ForgetResult(_ResponseModel):
    event_id: str
    status: str
    beliefs_affected: list[str] = Field(default_factory=list)
    beliefs_invalidated: list[str] = Field(default_factory=list)
    artifacts_deleted: list[str] = Field(default_factory=list)
    replay_safe: bool = False


class RestoreResult(_ResponseModel):
    removed_block_id: str
    old_generation_id: str
    new_generation_id: str
    restored_belief: Belief | None = None


class Generation(_ResponseModel):
    id: str
    user_id: str
    created_at: str
    parent_id: str | None
    reason: str
    status: GenerationStatus
    build_completed_at: str | None


class MemoryInspectItem(_ResponseModel):
    belief: Belief
    applicable_now: bool | None = None
    provenance_event_ids: list[str] = Field(default_factory=list)


class MemoryInspectResult(_ResponseModel):
    user_id: str
    active_generation: Generation | None
    active: list[MemoryInspectItem] = Field(default_factory=list)
    candidates: list[MemoryInspectItem] = Field(default_factory=list)
    suspect: list[MemoryInspectItem] = Field(default_factory=list)
    history: list[MemoryInspectItem] = Field(default_factory=list)
    semantic_blocks: list[SemanticBlock] = Field(default_factory=list)
    generations: list[Generation] = Field(default_factory=list)


# --- request models ----------------------------------------------------


class _RequestModel(BaseModel):
    """Base class for all SDK request models.

    extra="forbid" - a request the SDK sends must match the
    server's OpenAPI schema exactly. Unknown fields are an
    error, not silently accepted.
    """

    model_config = ConfigDict(extra="forbid")


class CreateEventRequest(_RequestModel):
    event_type: str
    content: dict[str, Any]
    sensitivity: str = "private"
    evidence_group: str | None = None


class CreateCompileRequest(_RequestModel):
    event_ids: list[str]
    use_llm: bool = False


class CreateGateRequest(_RequestModel):
    purpose: str
    context: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=20, ge=1, le=100)


class CorrectRequest(_RequestModel):
    value: dict[str, Any]
    reason: dict[str, Any] = Field(default_factory=dict)


class RejectRequest(_RequestModel):
    reason: dict[str, Any] = Field(default_factory=dict)


class SemanticForgetRequest(_RequestModel):
    semantic_key: str
    mode: str = "HARD_LOGICAL"
    reason: dict[str, Any] = Field(default_factory=dict)


class ForgetRequest(_RequestModel):
    mode: str = "HARD_LOGICAL"
    reason: dict[str, Any] = Field(default_factory=dict)
