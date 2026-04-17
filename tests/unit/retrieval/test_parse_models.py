"""Model-level validation tests for Lane E parse output schemas."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from keystone.retrieval.parse_models import (
    Coverage,
    CoverageStatus,
    EvidencePrepRecord,
    FetchedArtifact,
    Locator,
    ParseConfidence,
    ParseConfidenceTier,
    ParsedDocument,
    ParsedPassage,
    ParserIdentity,
    ParseWarning,
    PassageKind,
    SourceFamily,
    confidence,
    tier_for_score,
)

HASH_ZERO = "0" * 64
HASH_DEADBEEF = "deadbeef" * 8


def _conf(score: float) -> ParseConfidence:
    return confidence(score, ["TEST"])


class TestTierMapping:
    @pytest.mark.parametrize(
        "score, tier",
        [
            (1.0, ParseConfidenceTier.HIGH),
            (0.85, ParseConfidenceTier.HIGH),
            (0.849, ParseConfidenceTier.MEDIUM),
            (0.55, ParseConfidenceTier.MEDIUM),
            (0.549, ParseConfidenceTier.LOW),
            (0.0, ParseConfidenceTier.LOW),
        ],
    )
    def test_tier_for_score(self, score: float, tier: ParseConfidenceTier) -> None:
        assert tier_for_score(score) is tier

    def test_confidence_helper_clamps_and_derives_tier(self) -> None:
        c = confidence(1.5, reasons=["OOB"])
        assert c.score == 1.0
        assert c.tier is ParseConfidenceTier.HIGH
        assert c.reasons == ["OOB"]
        assert confidence(-0.5).score == 0.0

    def test_mismatched_tier_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ParseConfidence(score=0.9, tier=ParseConfidenceTier.LOW)


class TestParserIdentity:
    def test_requires_non_empty_name_and_version(self) -> None:
        with pytest.raises(ValidationError):
            ParserIdentity(name="", version="1")
        with pytest.raises(ValidationError):
            ParserIdentity(name="x", version="")

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ParserIdentity.model_validate({"name": "x", "version": "1", "mystery": 1})


class TestCoverage:
    def test_bytes_fetched_cannot_exceed_expected(self) -> None:
        with pytest.raises(ValidationError):
            Coverage(
                status=CoverageStatus.PARTIAL,
                bytes_fetched=200,
                bytes_expected=100,
            )

    def test_matching_or_smaller_fetched_ok(self) -> None:
        Coverage(status=CoverageStatus.COMPLETE, bytes_fetched=50, bytes_expected=100)
        Coverage(status=CoverageStatus.COMPLETE, bytes_fetched=100, bytes_expected=100)


class TestLocator:
    def test_empty_section_segment_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Locator(section_path=["Foo", ""], paragraph_index=0)

    def test_untrimmed_segment_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Locator(section_path=[" Foo"], paragraph_index=0)

    def test_char_end_before_start_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Locator(paragraph_index=0, char_start=100, char_end=50)

    def test_page_number_must_be_one_based(self) -> None:
        with pytest.raises(ValidationError):
            Locator(paragraph_index=0, page_number=0)

    def test_valid_locator_roundtrips(self) -> None:
        loc = Locator(
            section_path=["Intro", "Detail"],
            paragraph_index=2,
            page_number=3,
            char_start=10,
            char_end=20,
        )
        assert loc.section_path == ["Intro", "Detail"]


class TestParseWarning:
    def test_code_must_be_upper_snake(self) -> None:
        with pytest.raises(ValidationError):
            ParseWarning(code="lowercase", message="x")
        with pytest.raises(ValidationError):
            ParseWarning(code="With-Dash", message="x")

    def test_valid_code_accepted(self) -> None:
        w = ParseWarning(code="EMPTY_PAGE", message="no text", locator=None)
        assert w.code == "EMPTY_PAGE"


class TestParsedPassage:
    def _passage(self, **overrides: object) -> ParsedPassage:
        defaults: dict[str, object] = {
            "passage_id": "art1-p0001",
            "artifact_id": "art1",
            "kind": PassageKind.PARAGRAPH,
            "text": "Hello world.",
            "locator": Locator(paragraph_index=0),
            "parse_confidence": _conf(0.9),
        }
        defaults.update(overrides)
        return ParsedPassage(**defaults)  # type: ignore[arg-type]

    def test_happy_path(self) -> None:
        p = self._passage()
        assert p.kind is PassageKind.PARAGRAPH
        assert p.parse_confidence.tier is ParseConfidenceTier.HIGH

    def test_whitespace_only_text_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._passage(text="   \n\t")

    def test_invalid_passage_id(self) -> None:
        with pytest.raises(ValidationError):
            self._passage(passage_id="bad id with space")

    def test_frozen(self) -> None:
        p = self._passage()
        with pytest.raises(ValidationError):
            p.text = "mutated"  # type: ignore[misc]


class TestParsedDocument:
    def _passage(self, artifact_id: str, passage_id: str) -> ParsedPassage:
        return ParsedPassage(
            passage_id=passage_id,
            artifact_id=artifact_id,
            kind=PassageKind.PARAGRAPH,
            text="Body.",
            locator=Locator(paragraph_index=0),
            parse_confidence=_conf(0.9),
        )

    def test_requires_passages_to_match_artifact_id(self) -> None:
        with pytest.raises(ValidationError):
            ParsedDocument(
                artifact_id="artA",
                source_family=SourceFamily.ARTICLE,
                parser=ParserIdentity(name="x", version="1"),
                passages=[self._passage("artB", "art-p1")],
                warnings=[],
                overall_confidence=_conf(0.9),
            )

    def test_duplicate_passage_ids_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ParsedDocument(
                artifact_id="art1",
                source_family=SourceFamily.ARTICLE,
                parser=ParserIdentity(name="x", version="1"),
                passages=[
                    self._passage("art1", "dup-1"),
                    self._passage("art1", "dup-1"),
                ],
                warnings=[],
                overall_confidence=_conf(0.9),
            )

    def test_happy_path(self) -> None:
        doc = ParsedDocument(
            artifact_id="art1",
            source_family=SourceFamily.ARTICLE,
            parser=ParserIdentity(name="x", version="1"),
            passages=[self._passage("art1", "a-1"), self._passage("art1", "a-2")],
            warnings=[],
            overall_confidence=_conf(0.9),
        )
        assert len(doc.passages) == 2


class TestFetchedArtifact:
    def _artifact(self, **overrides: object) -> FetchedArtifact:
        defaults: dict[str, object] = {
            "artifact_id": "art1",
            "url": "https://example.com/x",
            "content_hash": HASH_DEADBEEF,
            "fetched_at": datetime(2026, 4, 17, tzinfo=UTC),
            "coverage": Coverage(status=CoverageStatus.COMPLETE),
            "content_text": "<p>hi</p>",
        }
        defaults.update(overrides)
        return FetchedArtifact(**defaults)  # type: ignore[arg-type]

    def test_content_hash_must_be_sha256_hex(self) -> None:
        with pytest.raises(ValidationError):
            self._artifact(content_hash="short")
        with pytest.raises(ValidationError):
            self._artifact(content_hash="Z" * 64)

    def test_missing_content_payload_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._artifact(content_text=None, content_bytes_b64=None)

    def test_either_payload_field_ok(self) -> None:
        self._artifact(content_text=None, content_bytes_b64="abcd")

    def test_extra_fields_allowed(self) -> None:
        art = self._artifact(unknown_future_field={"shape": "tbd"})
        assert art.unknown_future_field == {"shape": "tbd"}

    def test_mime_type_default(self) -> None:
        art = self._artifact()
        assert art.mime_type == "application/octet-stream"


class TestEvidencePrepRecord:
    def test_requires_non_whitespace_text(self) -> None:
        with pytest.raises(ValidationError):
            EvidencePrepRecord(
                record_id="ev:1",
                artifact_id="art1",
                canonical_url="https://x",
                content_hash=HASH_ZERO,
                coverage=Coverage(status=CoverageStatus.COMPLETE),
                source_family=SourceFamily.ARTICLE,
                parser=ParserIdentity(name="x", version="1"),
                locator=Locator(paragraph_index=0),
                passage_kind=PassageKind.PARAGRAPH,
                text="   ",
                parse_confidence=_conf(0.9),
                fetched_at=datetime(2026, 4, 17, tzinfo=UTC),
            )

    def test_record_id_must_match_format(self) -> None:
        with pytest.raises(ValidationError):
            EvidencePrepRecord(
                record_id="not valid id",
                artifact_id="art1",
                canonical_url="https://x",
                content_hash=HASH_ZERO,
                coverage=Coverage(status=CoverageStatus.COMPLETE),
                source_family=SourceFamily.ARTICLE,
                parser=ParserIdentity(name="x", version="1"),
                locator=Locator(paragraph_index=0),
                passage_kind=PassageKind.PARAGRAPH,
                text="Body.",
                parse_confidence=_conf(0.9),
                fetched_at=datetime(2026, 4, 17, tzinfo=UTC),
            )
