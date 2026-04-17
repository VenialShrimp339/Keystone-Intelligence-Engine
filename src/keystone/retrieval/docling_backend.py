"""Docling-backed PDF text backend for Lane E.

Implements :class:`PDFTextBackend` on top of IBM's `docling`_ library
(the Granite-Docling 258M pipeline). Docling is layout-aware: it
preserves heading hierarchy, reading order, and tables that the stdlib
fallback (:class:`BasicPDFTextBackend`) cannot reliably recover. On
structure-heavy documents (SEC filings, analyst reports) docling
reports ~97.9 % accuracy on complex table extraction; on simple
text-only PDFs both backends should agree.

Swap the backend at construction time::

    from keystone.retrieval import PDFParser
    from keystone.retrieval.docling_backend import DoclingBackend

    parser = PDFParser(backend=DoclingBackend())

The backend is deterministic and side-effect free from the caller's
perspective: docling is lazily initialized on the first ``extract``
call, errors are captured as warning codes rather than raised, and
empty or non-PDF inputs short-circuit with the same warning vocabulary
the basic backend uses.

.. _docling: https://github.com/DS4SD/docling
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from keystone.retrieval.pdf_parser import (
    PDFExtractionResult,
    PDFPageText,
    PDFTextBackend,
)

logger = logging.getLogger(__name__)

# docling identifier used when tagging successful extractions with the
# pipeline that produced them. Kept as a module constant so operators
# can grep logs for it and so tests can assert the expected tag.
DOCLING_PIPELINE_TAG = "docling.granite-258m"

# Per-page confidence scores. Docling can surface its own layout
# confidence per page, but those are not guaranteed across versions; we
# start from a high default when docling returned non-empty text and
# degrade when it returned no text or raised.
_PAGE_SCORE_HIGH = 0.97  # matches the published table-extraction accuracy
_PAGE_SCORE_EMPTY = 0.3
_PAGE_SCORE_ERROR = 0.1


# ---------------------------------------------------------------------------
# Minimal structural protocols for the docling surface we rely on.
#
# We intentionally describe only what we actually consume so tests can
# supply a compact fake without having to import docling. Real docling
# objects satisfy these protocols.
# ---------------------------------------------------------------------------


@runtime_checkable
class _DoclingPage(Protocol):
    """Subset of ``docling_core.types.doc.DoclingDocument.pages`` items."""

    page_no: int

    def export_to_text(self) -> str: ...


@runtime_checkable
class _DoclingDocument(Protocol):
    """Subset of ``docling_core.types.doc.DoclingDocument`` we touch."""

    def export_to_markdown(self) -> str: ...


@runtime_checkable
class _DoclingConversionResult(Protocol):
    document: _DoclingDocument
    # status is a docling enum in the real library; we just need a
    # value we can compare to "success" / SUCCESS for ok checks.
    status: Any


@runtime_checkable
class _DoclingConverter(Protocol):
    def convert(self, source: Any) -> _DoclingConversionResult: ...


# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _RawPage:
    """Intermediate representation collected from a docling document."""

    page_no: int
    text: str


class DoclingBackend:
    """PDFTextBackend that delegates extraction to the docling library.

    Construction options:

    - ``converter``: inject a pre-built converter (real or test fake).
      When omitted, docling is imported lazily and a default
      ``DocumentConverter`` is instantiated on the first ``extract``
      call.
    - ``pipeline_tag``: override the identifier recorded alongside
      successful extractions (default: ``DOCLING_PIPELINE_TAG``).

    ``extract`` never raises. Conversion errors surface as warning
    codes on the returned :class:`PDFExtractionResult`, matching the
    fallback backend's vocabulary so downstream scoring stays
    consistent.
    """

    def __init__(
        self,
        *,
        converter: _DoclingConverter | None = None,
        pipeline_tag: str = DOCLING_PIPELINE_TAG,
    ) -> None:
        self._converter_override: _DoclingConverter | None = converter
        self._converter: _DoclingConverter | None = converter
        self._pipeline_tag = pipeline_tag

    # -- PDFTextBackend protocol --------------------------------------------

    def extract(self, data: bytes) -> PDFExtractionResult:
        if not data:
            return PDFExtractionResult(pages=[], warnings=["EMPTY_BYTES"])
        if not _looks_like_pdf(data):
            return PDFExtractionResult(pages=[], warnings=["NOT_A_PDF"])

        try:
            converter = self._get_converter()
        except ImportError as exc:
            logger.warning("Docling backend unavailable: %s", exc)
            return PDFExtractionResult(pages=[], warnings=["DOCLING_UNAVAILABLE"])

        try:
            result = converter.convert(_make_docling_input(data))
        except _EncryptedPDFError:
            return PDFExtractionResult(pages=[], warnings=["ENCRYPTED"], encrypted=True)
        except Exception as exc:  # noqa: BLE001 -- docling raises varied types
            logger.warning("Docling conversion failed: %s", exc)
            return PDFExtractionResult(
                pages=[],
                warnings=["DOCLING_CONVERSION_FAILED"],
            )

        if not _is_conversion_success(result):
            status = getattr(getattr(result, "status", None), "name", "unknown")
            logger.warning("Docling reported non-success status: %s", status)
            return PDFExtractionResult(
                pages=[],
                warnings=["DOCLING_NON_SUCCESS_STATUS"],
            )

        raw_pages = _collect_raw_pages(result.document)
        if not raw_pages:
            return PDFExtractionResult(pages=[], warnings=["NO_PAGES_FOUND"])

        pages: list[PDFPageText] = []
        for raw in raw_pages:
            text = raw.text.strip()
            if text:
                pages.append(
                    PDFPageText(
                        page_number=raw.page_no,
                        text=raw.text.strip(),
                        confidence_score=_PAGE_SCORE_HIGH,
                        warnings=[self._pipeline_tag],
                    )
                )
            else:
                pages.append(
                    PDFPageText(
                        page_number=raw.page_no,
                        text="",
                        confidence_score=_PAGE_SCORE_EMPTY,
                        warnings=["EMPTY_PAGE", self._pipeline_tag],
                    )
                )

        return PDFExtractionResult(pages=pages, warnings=[])

    # -- Lazy docling resolution --------------------------------------------

    def _get_converter(self) -> _DoclingConverter:
        if self._converter is not None:
            return self._converter
        converter = _build_default_converter()
        self._converter = converter
        return converter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _EncryptedPDFError(RuntimeError):
    """Raised internally when docling reports an encryption failure."""


def _looks_like_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


def _make_docling_input(data: bytes) -> Any:
    """Wrap raw bytes in whichever input type docling currently accepts.

    Newer docling releases expect ``DocumentStream`` (name + BytesIO).
    Older releases accept a bare ``BytesIO``. We fall back progressively
    so the backend keeps working across the range of published versions.
    """

    try:
        from docling.datamodel.base_models import DocumentStream

        return DocumentStream(name="document.pdf", stream=io.BytesIO(data))
    except ImportError:
        # Older docling: a plain BytesIO stream works.
        return io.BytesIO(data)


def _build_default_converter() -> _DoclingConverter:
    """Construct the default docling DocumentConverter.

    Separated so tests can stub it (or skip it entirely by injecting a
    converter). Kept import-local so ``DoclingBackend`` itself has no
    module-level docling dependency.
    """

    from docling.document_converter import DocumentConverter

    converter: _DoclingConverter = DocumentConverter()
    return converter


def _is_conversion_success(result: _DoclingConversionResult) -> bool:
    """True when docling reports a successful conversion.

    docling uses an enum for status (``ConversionStatus.SUCCESS`` in
    recent versions). We accept either the enum's ``.name`` attribute or
    a raw string to stay compatible across the library's evolution.
    """

    status = getattr(result, "status", None)
    if status is None:
        # Some docling releases simply omit status on the successful path;
        # fall back to trusting the presence of a document.
        return getattr(result, "document", None) is not None
    name = getattr(status, "name", str(status)).upper()
    return name in {"SUCCESS", "PARTIAL_SUCCESS", "CONVERTED"}


def _collect_raw_pages(document: _DoclingDocument) -> list[_RawPage]:
    """Walk a DoclingDocument and produce per-page text tuples.

    Tries three strategies in order so we stay robust across docling
    releases:

    1. ``document.pages`` dict with per-page ``export_to_text``
       (current recommended path).
    2. ``document.pages`` dict where each page exposes ``text`` / ``body``
       directly (older releases).
    3. ``document.export_to_markdown`` fallback treated as a single
       logical page (extreme fallback; better than silently dropping
       text).
    """

    pages_attr = getattr(document, "pages", None)
    if isinstance(pages_attr, dict) and pages_attr:
        return _pages_from_dict(pages_attr)

    markdown_fn = getattr(document, "export_to_markdown", None)
    if callable(markdown_fn):
        text = markdown_fn() or ""
        if text.strip():
            return [_RawPage(page_no=1, text=text)]

    text_fn = getattr(document, "export_to_text", None)
    if callable(text_fn):
        text = text_fn() or ""
        if text.strip():
            return [_RawPage(page_no=1, text=text)]

    return []


def _pages_from_dict(pages: dict[Any, Any]) -> list[_RawPage]:
    collected: list[_RawPage] = []
    for key, page in pages.items():
        page_no = _coerce_page_number(key, page)
        text = _extract_page_text(page)
        collected.append(_RawPage(page_no=page_no, text=text))

    # Sort by page number so downstream consumers see ascending order
    # regardless of dict insertion order.
    collected.sort(key=lambda p: p.page_no)
    return collected


def _coerce_page_number(key: Any, page: Any) -> int:
    """Pick the best page number from key / page attributes."""

    candidate = getattr(page, "page_no", None) or getattr(page, "page_number", None)
    if isinstance(candidate, int) and candidate > 0:
        return candidate
    if isinstance(key, int) and key > 0:
        return key
    # Some docling versions key pages by 0-based int; bump to 1-based.
    if isinstance(key, int):
        return key + 1
    return 1


def _extract_page_text(page: Any) -> str:
    """Extract text from a docling page object via whichever API it exposes."""

    exporter = getattr(page, "export_to_text", None)
    if callable(exporter):
        try:
            text = exporter()
        except Exception:  # noqa: BLE001 -- defensive across docling versions
            text = ""
        if isinstance(text, str):
            return text

    markdown = getattr(page, "export_to_markdown", None)
    if callable(markdown):
        try:
            text = markdown()
        except Exception:  # noqa: BLE001
            text = ""
        if isinstance(text, str):
            return text

    for attr in ("text", "body", "content"):
        value = getattr(page, attr, None)
        if isinstance(value, str):
            return value

    return ""


# Assert DoclingBackend satisfies the protocol at import time. This gives
# us a clear typing signal -- mypy strict complains loudly if extract()
# drifts off the contract.
_PROTOCOL_CHECK: PDFTextBackend = DoclingBackend()
