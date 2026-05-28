"""Completion detection for browser-backed Deep Research jobs.

This module is deliberately pure string parsing. Browser adapters can feed it
DOM snapshots from Chrome, Playwright, Browser Use, or another controller while
keeping provider-specific UI rules testable without live browser sessions.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class BrowserResearchState(StrEnum):
    """Normalized lifecycle state for long-running browser research jobs."""

    UNKNOWN = "unknown"
    RUNNING = "running"
    COMPLETED = "completed"
    EXPORT_READY = "export_ready"
    BLOCKED = "blocked"
    FAILED = "failed"


class ProviderCompletionSignal(BaseModel):
    """A browser-observed state signal for one provider research job."""

    model_config = ConfigDict(frozen=True)

    provider: str
    state: BrowserResearchState
    evidence: list[str] = Field(default_factory=list)
    report_title: str | None = None
    source_count: int | None = None
    native_notify_available: bool = False
    native_notify_enabled: bool = False
    export_available: bool = False

    @property
    def should_ingest(self) -> bool:
        """Only completed, exportable reports may enter the ingestion path."""
        return self.state == BrowserResearchState.EXPORT_READY and self.export_available


def detect_chatgpt_deep_research_state(dom_text: str) -> ProviderCompletionSignal:
    """Classify ChatGPT Deep Research DOM text into Keystone lifecycle state."""
    text = _normalize(dom_text)
    evidence: list[str] = []

    if _contains_any(text, "captcha", "verify you are human", "payment required", "log in"):
        return ProviderCompletionSignal(
            provider="chatgpt",
            state=BrowserResearchState.BLOCKED,
            evidence=_hits(text, "captcha", "verify you are human", "payment required", "log in"),
        )

    if _contains_any(text, "error generating", "something went wrong", "failed"):
        return ProviderCompletionSignal(
            provider="chatgpt",
            state=BrowserResearchState.FAILED,
            evidence=_hits(text, "error generating", "something went wrong", "failed"),
        )

    if _contains_any(text, "stop answering", "thinking", "researching", "searching"):
        evidence.extend(_hits(text, "stop answering", "thinking", "researching", "searching"))
        return ProviderCompletionSignal(
            provider="chatgpt",
            state=BrowserResearchState.RUNNING,
            evidence=evidence,
            native_notify_available=_contains_any(text, "notify"),
        )

    export_available = _contains_any(
        text,
        "download",
        "markdown",
        "pdf",
        "word",
        "fullscreen report",
        "sources used",
    )
    if export_available:
        evidence.extend(_hits(text, "download", "markdown", "pdf", "word", "sources used"))
        return ProviderCompletionSignal(
            provider="chatgpt",
            state=BrowserResearchState.EXPORT_READY,
            evidence=evidence,
            export_available=True,
            native_notify_available=_contains_any(text, "notify"),
        )

    if _contains_any(text, "copy message", "share"):
        return ProviderCompletionSignal(
            provider="chatgpt",
            state=BrowserResearchState.COMPLETED,
            evidence=_hits(text, "copy message", "share"),
            native_notify_available=_contains_any(text, "notify"),
        )

    return ProviderCompletionSignal(provider="chatgpt", state=BrowserResearchState.UNKNOWN)


def detect_claude_research_state(dom_text: str) -> ProviderCompletionSignal:
    """Classify Claude Research DOM text into Keystone lifecycle state."""
    text = _normalize(dom_text)
    evidence: list[str] = []
    source_count = _source_count(text)
    report_title = _claude_report_title(dom_text)
    notify_available = "notify" in text

    if _contains_any(text, "captcha", "verify you are human", "payment required", "log in"):
        return ProviderCompletionSignal(
            provider="claude",
            state=BrowserResearchState.BLOCKED,
            evidence=_hits(text, "captcha", "verify you are human", "payment required", "log in"),
            source_count=source_count,
            native_notify_available=notify_available,
        )

    if _contains_any(text, "failed", "error", "try again"):
        return ProviderCompletionSignal(
            provider="claude",
            state=BrowserResearchState.FAILED,
            evidence=_hits(text, "failed", "error", "try again"),
            source_count=source_count,
            native_notify_available=notify_available,
        )

    export_available = _contains_any(
        text,
        "artifact panel:",
        "view u.s.",
        "research report is ready",
        "research complete",
    )
    if export_available:
        evidence.extend(
            _hits(
                text,
                "artifact panel:",
                "research report is ready",
                "research complete",
                "gathered",
            )
        )
        return ProviderCompletionSignal(
            provider="claude",
            state=BrowserResearchState.EXPORT_READY,
            evidence=evidence,
            report_title=report_title,
            source_count=source_count,
            native_notify_available=notify_available,
            native_notify_enabled=_contains_any(text, "notifications (f8)"),
            export_available=True,
        )

    if _contains_any(
        text,
        "claude is responding",
        "preparing to dive in",
        "sources and counting",
        "writing and citing report",
        "stop response",
    ):
        evidence.extend(
            _hits(
                text,
                "claude is responding",
                "preparing to dive in",
                "sources and counting",
                "writing and citing report",
                "stop response",
            )
        )
        return ProviderCompletionSignal(
            provider="claude",
            state=BrowserResearchState.RUNNING,
            evidence=evidence,
            source_count=source_count,
            native_notify_available=notify_available,
        )

    return ProviderCompletionSignal(
        provider="claude",
        state=BrowserResearchState.UNKNOWN,
        source_count=source_count,
        native_notify_available=notify_available,
    )


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _contains_any(text: str, *needles: str) -> bool:
    return any(needle in text for needle in needles)


def _hits(text: str, *needles: str) -> list[str]:
    return [needle for needle in needles if needle in text]


def _source_count(text: str) -> int | None:
    matches = re.findall(r"(?:gathered\s+)?(\d{1,4})\s+sources", text)
    if not matches:
        return None
    return max(int(match) for match in matches)


def _claude_report_title(dom_text: str) -> str | None:
    match = re.search(r"Artifact panel:\s*([^\n\"]+)", dom_text)
    if match:
        return match.group(1).strip()
    match = re.search(r'View\s+([^"\n]+)', dom_text)
    if match:
        return match.group(1).strip()
    return None
