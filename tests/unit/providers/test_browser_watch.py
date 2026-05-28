from __future__ import annotations

from keystone.providers import (
    BrowserResearchState,
    detect_chatgpt_deep_research_state,
    detect_claude_research_state,
)


def test_chatgpt_running_state_is_not_ingestable():
    signal = detect_chatgpt_deep_research_state(
        """
        - button "Deep research, click to remove"
        - button "Thinking"
        - tooltip "Stop answering, Enter"
        """
    )

    assert signal.state == BrowserResearchState.RUNNING
    assert signal.should_ingest is False


def test_claude_running_sources_and_counting_is_not_ingestable():
    signal = detect_claude_research_state(
        """
        - button "Collision repair industry consolidation report: 241 sources and counting."
        - button "Gathering 241 sources and counting..." [disabled]
        - button "Notify"
        - button "Stop response"
        """
    )

    assert signal.state == BrowserResearchState.RUNNING
    assert signal.source_count == 241
    assert signal.native_notify_available is True
    assert signal.should_ingest is False


def test_claude_completed_artifact_panel_is_ingestable():
    signal = detect_claude_research_state(
        """
        - text: Research complete
        - button "Collision repair industry consolidation report: 257 sources."
        - button "Boom! Research report is ready" [disabled]
        - region "Artifact panel: U.S. Collision Repair Consolidation"
        """
    )

    assert signal.state == BrowserResearchState.EXPORT_READY
    assert signal.source_count == 257
    assert signal.report_title == "U.S. Collision Repair Consolidation"
    assert signal.should_ingest is True


def test_blocked_state_takes_precedence():
    signal = detect_chatgpt_deep_research_state("Please verify you are human. Thinking.")

    assert signal.state == BrowserResearchState.BLOCKED
    assert signal.should_ingest is False
