"""Unit tests for the docling PDF text backend.

These tests never import docling. They drive ``DoclingBackend`` with
injected fake converter objects that mirror the subset of docling's
API we depend on. Fake documents implement ``pages``, ``export_to_text``,
and status enums exactly as docling does.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from keystone.retrieval import (
    DOCLING_PIPELINE_TAG,
    DoclingBackend,
    PDFParser,
    PDFTextBackend,
)
from keystone.retrieval.parse_models import (
    ParseConfidenceTier,
    SourceFamily,
)
from tests.unit.retrieval.conftest import build_minimal_pdf, make_pdf_artifact

# ---------------------------------------------------------------------------
# Docling fakes
# ---------------------------------------------------------------------------


class _FakeStatus:
    """Minimal stand-in for docling.ConversionStatus."""

    def __init__(self, name: str) -> None:
        self.name = name


class _FakePage:
    def __init__(
        self,
        page_no: int,
        text: str = "",
        markdown: str | None = None,
        raises: BaseException | None = None,
    ) -> None:
        self.page_no = page_no
        self._text = text
        self._markdown = markdown
        self._raises = raises

    def export_to_text(self) -> str:
        if self._raises is not None:
            raise self._raises
        return self._text

    def export_to_markdown(self) -> str:
        return self._markdown or self._text


class _FakeDocument:
    def __init__(
        self,
        pages: dict[int, _FakePage] | None = None,
        markdown: str = "",
    ) -> None:
        self.pages = pages or {}
        self._markdown = markdown

    def export_to_markdown(self) -> str:
        return self._markdown

    def export_to_text(self) -> str:
        return self._markdown


@dataclass
class _FakeResult:
    document: _FakeDocument
    status: _FakeStatus


class _FakeConverter:
    """Captures the last source passed to .convert()."""

    def __init__(
        self,
        pages: dict[int, _FakePage] | None = None,
        status_name: str = "SUCCESS",
        markdown: str = "",
        raises: BaseException | None = None,
    ) -> None:
        self._pages = pages or {}
        self._status = _FakeStatus(status_name)
        self._markdown = markdown
        self._raises = raises
        self.calls: list[Any] = []

    def convert(self, source: Any) -> _FakeResult:
        self.calls.append(source)
        if self._raises is not None:
            raise self._raises
        doc = _FakeDocument(pages=self._pages, markdown=self._markdown)
        return _FakeResult(document=doc, status=self._status)


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_docling_backend_is_a_pdf_text_backend(self) -> None:
        backend = DoclingBackend(converter=_FakeConverter())
        assert isinstance(backend, PDFTextBackend)


# ---------------------------------------------------------------------------
# Empty / malformed input short-circuits
# ---------------------------------------------------------------------------


class TestInputGuards:
    def test_empty_bytes_returns_empty_pages_with_warning(self) -> None:
        backend = DoclingBackend(converter=_FakeConverter())
        result = backend.extract(b"")

        assert result.pages == []
        assert result.warnings == ["EMPTY_BYTES"]
        assert result.encrypted is False

    def test_non_pdf_bytes_returns_empty_pages_with_warning(self) -> None:
        backend = DoclingBackend(converter=_FakeConverter())
        result = backend.extract(b"<html>not a pdf</html>")

        assert result.pages == []
        assert result.warnings == ["NOT_A_PDF"]

    def test_non_pdf_skips_converter(self) -> None:
        converter = _FakeConverter()
        backend = DoclingBackend(converter=converter)
        backend.extract(b"plain text")

        assert converter.calls == []


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestSuccessfulExtraction:
    def test_returns_one_page_per_docling_page(self) -> None:
        converter = _FakeConverter(
            pages={
                1: _FakePage(1, text="First page body"),
                2: _FakePage(2, text="Second page body"),
            }
        )
        backend = DoclingBackend(converter=converter)
        pdf_bytes = build_minimal_pdf(pages=["hello"])
        result = backend.extract(pdf_bytes)

        assert [p.page_number for p in result.pages] == [1, 2]
        assert "First page body" in result.pages[0].text
        assert "Second page body" in result.pages[1].text

    def test_page_confidence_high_for_nonempty_pages(self) -> None:
        converter = _FakeConverter(
            pages={1: _FakePage(1, text="Body text")},
        )
        backend = DoclingBackend(converter=converter)
        result = backend.extract(build_minimal_pdf(pages=["hi"]))

        assert result.pages[0].confidence_score == pytest.approx(0.97)
        assert DOCLING_PIPELINE_TAG in result.pages[0].warnings

    def test_empty_page_degrades_confidence_but_keeps_ordering(self) -> None:
        converter = _FakeConverter(
            pages={
                1: _FakePage(1, text="populated"),
                2: _FakePage(2, text=""),
            }
        )
        backend = DoclingBackend(converter=converter)
        result = backend.extract(build_minimal_pdf(pages=["hi"]))

        assert [p.page_number for p in result.pages] == [1, 2]
        assert result.pages[0].confidence_score == pytest.approx(0.97)
        assert result.pages[1].confidence_score == pytest.approx(0.3)
        assert "EMPTY_PAGE" in result.pages[1].warnings

    def test_pages_sorted_ascending_even_when_dict_unordered(self) -> None:
        converter = _FakeConverter(
            pages={
                5: _FakePage(5, text="fifth"),
                1: _FakePage(1, text="first"),
                3: _FakePage(3, text="third"),
            }
        )
        backend = DoclingBackend(converter=converter)
        result = backend.extract(build_minimal_pdf(pages=["hi"]))

        assert [p.page_number for p in result.pages] == [1, 3, 5]

    def test_strips_surrounding_whitespace(self) -> None:
        converter = _FakeConverter(pages={1: _FakePage(1, text="\n\n  padded body  \n\n")})
        backend = DoclingBackend(converter=converter)
        result = backend.extract(build_minimal_pdf(pages=["hi"]))

        assert result.pages[0].text == "padded body"


# ---------------------------------------------------------------------------
# Docling-specific failure modes
# ---------------------------------------------------------------------------


class TestDoclingFailureModes:
    def test_non_success_status_yields_warning_and_no_pages(self) -> None:
        converter = _FakeConverter(
            pages={1: _FakePage(1, text="never returned")},
            status_name="FAILURE",
        )
        backend = DoclingBackend(converter=converter)
        result = backend.extract(build_minimal_pdf(pages=["hi"]))

        assert result.pages == []
        assert result.warnings == ["DOCLING_NON_SUCCESS_STATUS"]

    def test_converter_raises_is_captured_as_warning(self) -> None:
        converter = _FakeConverter(raises=RuntimeError("docling exploded"))
        backend = DoclingBackend(converter=converter)
        result = backend.extract(build_minimal_pdf(pages=["hi"]))

        assert result.pages == []
        assert result.warnings == ["DOCLING_CONVERSION_FAILED"]
        assert result.encrypted is False

    def test_empty_document_yields_no_pages_warning(self) -> None:
        converter = _FakeConverter(pages={}, markdown="")
        backend = DoclingBackend(converter=converter)
        result = backend.extract(build_minimal_pdf(pages=["hi"]))

        assert result.pages == []
        assert result.warnings == ["NO_PAGES_FOUND"]

    def test_markdown_only_document_falls_back_to_single_page(self) -> None:
        # Some docling outputs only expose a document-level markdown
        # export (no .pages). We must still surface that content as one
        # logical page instead of silently dropping the conversion.
        converter = _FakeConverter(
            pages={},
            markdown="# Title\n\nBody text extracted from the PDF.",
        )
        backend = DoclingBackend(converter=converter)
        result = backend.extract(build_minimal_pdf(pages=["hi"]))

        assert [p.page_number for p in result.pages] == [1]
        assert "Body text extracted from the PDF." in result.pages[0].text


# ---------------------------------------------------------------------------
# Integration with PDFParser
# ---------------------------------------------------------------------------


class TestParserIntegration:
    def test_pdfparser_dispatches_to_docling_backend(self) -> None:
        converter = _FakeConverter(
            pages={
                1: _FakePage(1, text="Hello from docling."),
                2: _FakePage(2, text="Second docling page."),
            }
        )
        backend = DoclingBackend(converter=converter)
        parser = PDFParser(backend=backend)

        artifact = make_pdf_artifact(
            artifact_id="pdf-docling",
            raw_bytes=build_minimal_pdf(pages=["ignored"]),
        )
        doc = parser.parse(artifact)

        assert doc.source_family is SourceFamily.PDF
        joined = " ".join(p.text for p in doc.passages)
        assert "Hello from docling." in joined
        assert "Second docling page." in joined
        # Pages come through ranked by docling page_no, 1-based.
        pages_seen = sorted({p.locator.page_number for p in doc.passages})
        assert pages_seen == [1, 2]
        assert doc.overall_confidence.tier is ParseConfidenceTier.HIGH

    def test_pdfparser_preserves_docling_pipeline_tag_in_warnings(self) -> None:
        converter = _FakeConverter(
            pages={1: _FakePage(1, text="Only page")},
        )
        parser = PDFParser(backend=DoclingBackend(converter=converter))

        artifact = make_pdf_artifact(
            artifact_id="pdf-tag",
            raw_bytes=build_minimal_pdf(pages=["ignored"]),
        )
        doc = parser.parse(artifact)

        assert any(
            DOCLING_PIPELINE_TAG in passage.parse_confidence.reasons for passage in doc.passages
        )

    def test_encrypted_warning_flagged_when_converter_declares_encryption(self) -> None:
        from keystone.retrieval.docling_backend import _EncryptedPDFError

        converter = _FakeConverter(raises=_EncryptedPDFError("encrypted"))
        backend = DoclingBackend(converter=converter)
        result = backend.extract(build_minimal_pdf(pages=["hi"]))

        assert result.encrypted is True
        assert result.warnings == ["ENCRYPTED"]


# ---------------------------------------------------------------------------
# Lazy-loading default converter
# ---------------------------------------------------------------------------


class TestLazyDefault:
    def test_missing_docling_installation_returns_warning(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from keystone.retrieval import docling_backend as mod

        def fake_build() -> Any:
            raise ImportError("docling is not installed")

        monkeypatch.setattr(mod, "_build_default_converter", fake_build)
        backend = DoclingBackend()

        result = backend.extract(build_minimal_pdf(pages=["hi"]))
        assert result.pages == []
        assert result.warnings == ["DOCLING_UNAVAILABLE"]

    def test_default_converter_is_cached_after_first_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from keystone.retrieval import docling_backend as mod

        call_count = 0

        def fake_build() -> _FakeConverter:
            nonlocal call_count
            call_count += 1
            return _FakeConverter(pages={1: _FakePage(1, text="ok")})

        monkeypatch.setattr(mod, "_build_default_converter", fake_build)
        backend = DoclingBackend()

        pdf_bytes = build_minimal_pdf(pages=["hi"])
        backend.extract(pdf_bytes)
        backend.extract(pdf_bytes)
        backend.extract(pdf_bytes)

        assert call_count == 1


# ---------------------------------------------------------------------------
# Input wrapper: passes PDF bytes into docling without buffer mutations
# ---------------------------------------------------------------------------


class TestDoclingInputWrapping:
    def test_converter_receives_wrapped_source(self) -> None:
        converter = _FakeConverter(pages={1: _FakePage(1, text="body")})
        backend = DoclingBackend(converter=converter)
        pdf_bytes = build_minimal_pdf(pages=["hi"])

        backend.extract(pdf_bytes)

        assert len(converter.calls) == 1
        source = converter.calls[0]
        # Either DocumentStream (newer docling) or BytesIO (older). Both
        # expose a `read` method, which is what docling actually consumes.
        assert hasattr(source, "read") or hasattr(source, "stream")
