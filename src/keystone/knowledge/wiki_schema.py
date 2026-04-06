"""Storage-agnostic wiki interface for knowledge accumulation.

Defines WikiEntry (compiled wiki entry model) and WikiStore (Protocol for
storage backends). Phase 1 = filesystem. Phase 2 = PostgreSQL. The interface
does not change between phases.

NOTE: WikiStore is a storage abstraction, NOT a pipeline contract.
It does NOT appear in contracts.py and does NOT yield PipelineEvents.
Wiki operations are event-silent. Observability is at the calling layer
(the research orchestrator yields ResearchComplete events after wiki writes).
"""

from __future__ import annotations

import re
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WikiEntry(BaseModel):
    """A compiled wiki entry in the engagement knowledge base.

    Each entry corresponds to a compiled/{topic}.md file containing
    synthesized findings from one or more research rounds. Content
    hashes and proposition hashes enable full provenance tracing
    back to raw/ artifacts.
    """

    model_config = ConfigDict(frozen=True)

    path: str = Field(description="Relative path: compiled/{topic}.md")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")
    content: str = Field(description="Compiled markdown content")
    content_hash: str = Field(description="SHA-256 of content")
    proposition_hashes: list[str] = Field(
        default_factory=list,
        description="Per-proposition content hashes for provenance tracking",
    )
    source_artifacts: list[str] = Field(
        default_factory=list,
        description="Paths to raw/ artifacts this was compiled from",
    )
    round_added: int = Field(ge=0, description="Research round number")
    indexed: bool = Field(default=False, description="Whether this appears in INDEX.md")

    @field_validator("content_hash")
    @classmethod
    def validate_content_hash(cls, v: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{64}", v):
            raise ValueError("content_hash must be a 64-character lowercase hex string (SHA-256)")
        return v

    @field_validator("proposition_hashes")
    @classmethod
    def validate_proposition_hashes(cls, v: list[str]) -> list[str]:
        for h in v:
            if not re.fullmatch(r"[0-9a-f]{64}", h):
                raise ValueError(
                    f"Each proposition hash must be a 64-character lowercase hex string, got: {h}"
                )
        return v


class WikiStore(Protocol):
    """Storage-agnostic wiki interface.

    Phase 1: FilesystemWikiStore (engagement_store.py)
    Phase 2: PostgresWikiStore (future)

    All methods are async to support both filesystem and database backends.
    """

    async def write_raw(
        self,
        engagement_id: str,
        round_number: int,
        agent_id: str,
        task_id: str,
        artifact: str,
    ) -> str:
        """Write a raw subagent artifact. Returns the path ({round}_{agent_id}_{task_id}.md).

        Raw artifacts are immutable after write.
        """
        ...

    async def write_compiled(self, entry: WikiEntry) -> None:
        """Write or overwrite a compiled wiki entry."""
        ...

    async def read_compiled(self, engagement_id: str, path: str) -> WikiEntry | None:
        """Read a compiled entry by path. Returns None if not found."""
        ...

    async def list_compiled(self, engagement_id: str) -> list[WikiEntry]:
        """List all compiled entries for an engagement."""
        ...

    async def read_index(self, engagement_id: str) -> str:
        """Read the INDEX.md content. Returns empty string if not found."""
        ...

    async def write_index(self, engagement_id: str, content: str) -> None:
        """Write the INDEX.md content."""
        ...
