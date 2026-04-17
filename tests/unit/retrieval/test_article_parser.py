"""Tests for the HTML article parser."""

from __future__ import annotations

import base64
from datetime import UTC, datetime

from keystone.retrieval import ArticleParser
from keystone.retrieval.parse_models import (
    Coverage,
    CoverageStatus,
    FetchedArtifact,
    ParseConfidenceTier,
    PassageKind,
    SourceFamily,
)
from tests.unit.retrieval.conftest import make_article_artifact

HASH_HEX = "c" * 64


def _text_artifact(html: str, *, artifact_id: str = "art-t") -> FetchedArtifact:
    return make_article_artifact(artifact_id=artifact_id, html=html)


class TestArticleParserHappyPath:
    def test_basic_fixture_produces_expected_structure(
        self, article_artifact: FetchedArtifact
    ) -> None:
        doc = ArticleParser().parse(article_artifact)
        assert doc.parser.name == "keystone.article.v1"
        assert doc.source_family is SourceFamily.ARTICLE
        assert doc.warnings == []
        assert doc.overall_confidence.tier is ParseConfidenceTier.HIGH
        kinds = [p.kind for p in doc.passages]
        assert PassageKind.SECTION_HEADING in kinds
        assert PassageKind.PARAGRAPH in kinds
        assert PassageKind.LIST_ITEM in kinds
        assert PassageKind.BLOCK_QUOTE in kinds

    def test_script_and_style_content_is_excluded(self, article_artifact: FetchedArtifact) -> None:
        doc = ArticleParser().parse(article_artifact)
        joined = " ".join(p.text for p in doc.passages)
        assert "window.analytics" not in joined
        assert "color: red" not in joined

    def test_entities_roundtrip(self, article_artifact: FetchedArtifact) -> None:
        doc = ArticleParser().parse(article_artifact)
        joined = " ".join(p.text for p in doc.passages)
        assert "&" in joined  # from "Entities like & and ©"
        assert "\u00a9" in joined  # ©
        assert "\u201c" in joined  # curly opening quote from &ldquo;

    def test_heading_chain_builds_section_path(self, article_artifact: FetchedArtifact) -> None:
        doc = ArticleParser().parse(article_artifact)
        body_paragraphs = [p for p in doc.passages if p.kind is PassageKind.PARAGRAPH]
        assert any(
            p.locator.section_path[:1] == ["How Lane E Parses HTML"] for p in body_paragraphs
        )
        assert any(
            p.locator.section_path[-1] == "Closing"
            for p in body_paragraphs
            if len(p.locator.section_path) >= 1
        )

    def test_passage_ids_are_unique_and_sequential(self, article_artifact: FetchedArtifact) -> None:
        doc = ArticleParser().parse(article_artifact)
        ids = [p.passage_id for p in doc.passages]
        assert len(ids) == len(set(ids))
        for i, pid in enumerate(ids, start=1):
            assert pid.endswith(f"p{i:04d}")

    def test_paragraph_index_increments_within_section(self) -> None:
        html = "<h1>A</h1><p>one</p><p>two</p><h1>B</h1><p>three</p>"
        doc = ArticleParser().parse(_text_artifact(html))
        paragraphs = [p for p in doc.passages if p.kind is PassageKind.PARAGRAPH]
        assert [p.locator.paragraph_index for p in paragraphs] == [0, 1, 0]


class TestArticleParserEdgeCases:
    def test_empty_body_returns_zero_passages_with_warning(self) -> None:
        doc = ArticleParser().parse(_text_artifact("<html><body></body></html>"))
        assert doc.passages == []
        assert any(w.code == "EMPTY_HTML" for w in doc.warnings) or any(
            "NO_PASSAGES_EMITTED" in r for r in doc.overall_confidence.reasons
        )
        assert doc.overall_confidence.tier is ParseConfidenceTier.LOW

    def test_missing_content_entirely_returns_empty_doc(self) -> None:
        art = FetchedArtifact(
            artifact_id="blank",
            url="https://example.com",
            content_hash=HASH_HEX,
            fetched_at=datetime(2026, 4, 17, tzinfo=UTC),
            coverage=Coverage(status=CoverageStatus.COMPLETE),
            content_text="",
        )
        doc = ArticleParser().parse(art)
        assert doc.passages == []
        assert any(w.code == "EMPTY_HTML" for w in doc.warnings)
        assert doc.overall_confidence.score == 0.0

    def test_b64_fallback_emits_fallback_warning(self) -> None:
        html = (
            "<p>Fallback content decoded from bytes when content_text is absent "
            "but the artifact carries a base64-encoded payload instead.</p>"
        )
        art = FetchedArtifact(
            artifact_id="b64",
            url="https://example.com",
            content_hash=HASH_HEX,
            fetched_at=datetime(2026, 4, 17, tzinfo=UTC),
            coverage=Coverage(status=CoverageStatus.COMPLETE),
            content_text=None,
            content_bytes_b64=base64.b64encode(html.encode("utf-8")).decode("ascii"),
        )
        doc = ArticleParser().parse(art)
        assert doc.passages
        assert "Fallback content" in doc.passages[0].text
        assert any(w.code == "UTF8_DECODE_FALLBACK" for w in doc.warnings)
        assert doc.overall_confidence.tier in {
            ParseConfidenceTier.HIGH,
            ParseConfidenceTier.MEDIUM,
        }

    def test_b64_non_utf8_decode_is_lossy_with_warning(self) -> None:
        # Latin-1 "é" byte is invalid UTF-8 start byte.
        payload = b"<p>caf\xe9</p>"
        art = FetchedArtifact(
            artifact_id="lossy",
            url="https://example.com",
            content_hash=HASH_HEX,
            fetched_at=datetime(2026, 4, 17, tzinfo=UTC),
            coverage=Coverage(status=CoverageStatus.COMPLETE),
            content_text=None,
            content_bytes_b64=base64.b64encode(payload).decode("ascii"),
        )
        doc = ArticleParser().parse(art)
        assert any(w.code == "UTF8_DECODE_LOSSY" for w in doc.warnings)
        # Passage text should still be present (possibly containing the replacement char)
        assert doc.passages
        assert doc.overall_confidence.tier is not ParseConfidenceTier.HIGH

    def test_malformed_html_does_not_raise(self) -> None:
        html = "<p>unclosed <p>second<strong>never"
        doc = ArticleParser().parse(_text_artifact(html))
        # Lenient parser should still emit at least one non-empty passage.
        assert doc.passages
        joined = " ".join(p.text for p in doc.passages)
        assert "unclosed" in joined and "second" in joined

    def test_base64_decode_failure_emits_warning_and_empty_doc(self) -> None:
        art = FetchedArtifact(
            artifact_id="badb64",
            url="https://example.com",
            content_hash=HASH_HEX,
            fetched_at=datetime(2026, 4, 17, tzinfo=UTC),
            coverage=Coverage(status=CoverageStatus.COMPLETE),
            content_text=None,
            content_bytes_b64="not base64 !!!",
        )
        doc = ArticleParser().parse(art)
        # Either base64 decode warning or empty html warning will fire.
        codes = {w.code for w in doc.warnings}
        assert codes & {"BASE64_DECODE_FAILED", "EMPTY_HTML"}
        assert doc.passages == []

    def test_respects_pre_set_source_family(self) -> None:
        art = make_article_artifact(
            artifact_id="reportish",
            html="<h1>Q1 Report</h1><p>Financial highlights.</p>",
            source_family=SourceFamily.REPORT,
        )
        doc = ArticleParser().parse(art)
        assert doc.source_family is SourceFamily.REPORT

    def test_tag_mismatch_emits_warning(self) -> None:
        html = "<p>Hi</div>"
        doc = ArticleParser().parse(_text_artifact(html))
        assert doc.passages  # still extracted text
        assert any(w.code == "HTML_TAG_MISMATCH" for w in doc.warnings)

    def test_br_inserts_space(self) -> None:
        html = "<p>line one<br>line two</p>"
        doc = ArticleParser().parse(_text_artifact(html))
        [passage] = doc.passages
        assert "line one" in passage.text and "line two" in passage.text

    def test_inline_whitespace_is_collapsed(self) -> None:
        html = "<p>lots   of\n\nspace\there</p>"
        doc = ArticleParser().parse(_text_artifact(html))
        [p] = doc.passages
        assert p.text == "lots of space here"

    def test_table_cells_become_table_passages(self) -> None:
        html = "<table><tr><th>A</th><td>1</td></tr></table>"
        doc = ArticleParser().parse(_text_artifact(html))
        assert all(p.kind is PassageKind.TABLE for p in doc.passages)
        assert {p.text for p in doc.passages} == {"A", "1"}
