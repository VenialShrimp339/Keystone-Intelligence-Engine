"""Shared fixtures for Lane E retrieval tests.

Builds FetchedArtifact instances and minimal PDF byte blobs programmatically
so the test suite has no dependency on binary fixture files beyond the
sample HTML/PDF in ``tests/fixtures/retrieval``.
"""

from __future__ import annotations

import base64
import hashlib
import io
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from keystone.retrieval.parse_models import (
    Coverage,
    CoverageStatus,
    FetchedArtifact,
    SourceFamily,
)

FIXTURES_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "retrieval"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_article_artifact(
    *,
    artifact_id: str = "art-simple",
    html: str | None = None,
    canonical_url: str | None = "https://example.com/story",
    source_family: SourceFamily = SourceFamily.ARTICLE,
    coverage: Coverage | None = None,
    title: str | None = "A simple article",
    snippet: str | None = None,
    audit: dict[str, Any] | None = None,
) -> FetchedArtifact:
    """Build a FetchedArtifact carrying inline HTML."""

    if html is None:
        html = (FIXTURES_ROOT / "sample_article.html").read_text(encoding="utf-8")
    return FetchedArtifact(
        artifact_id=artifact_id,
        url="https://example.com/story?ref=tw",
        canonical_url=canonical_url,
        redirect_chain=["https://example.com/short/1"],
        mime_type="text/html; charset=utf-8",
        content_hash=_sha256(html.encode("utf-8")),
        title=title,
        fetched_at=datetime(2026, 4, 17, 12, 0, tzinfo=UTC),
        coverage=coverage or Coverage(status=CoverageStatus.COMPLETE),
        content_text=html,
        snippet=snippet,
        source_family=source_family,
        audit=audit or {"fetcher": "lane-h/v1", "attempts": 1},
    )


def make_pdf_artifact(
    *,
    artifact_id: str = "pdf-simple",
    text: str | None = None,
    raw_bytes: bytes | None = None,
    canonical_url: str | None = "https://example.com/report.pdf",
    coverage: Coverage | None = None,
    title: str | None = "A simple PDF",
) -> FetchedArtifact:
    """Build a FetchedArtifact for a PDF; exactly one of text/raw_bytes must be set."""

    if text is None and raw_bytes is None:
        raise ValueError("make_pdf_artifact requires either text or raw_bytes")
    if text is not None and raw_bytes is not None:
        raise ValueError("make_pdf_artifact accepts only one of text/raw_bytes")

    hash_source = text.encode("utf-8") if text is not None else raw_bytes
    assert hash_source is not None
    return FetchedArtifact(
        artifact_id=artifact_id,
        url="https://example.com/report.pdf",
        canonical_url=canonical_url,
        redirect_chain=[],
        mime_type="application/pdf",
        content_hash=_sha256(hash_source),
        title=title,
        fetched_at=datetime(2026, 4, 17, 12, 0, tzinfo=UTC),
        coverage=coverage or Coverage(status=CoverageStatus.COMPLETE),
        content_text=text,
        content_bytes_b64=(
            base64.b64encode(raw_bytes).decode("ascii") if raw_bytes is not None else None
        ),
        source_family=SourceFamily.PDF,
        audit={"fetcher": "lane-h/v1"},
    )


def build_minimal_pdf(
    *,
    pages: list[str] | None = None,
    flate: bool = False,
    encrypt: bool = False,
) -> bytes:
    """Construct a minimal, valid (ish) PDF byte blob for tests.

    Each entry in ``pages`` becomes a single BT...ET block with one Tj per
    physical line (split on ``\\n``). ``flate=True`` wraps the content
    stream in a FlateDecode filter so the basic backend exercises zlib.
    ``encrypt=True`` inserts ``/Encrypt 0 0 R`` into the trailer so the
    backend flags the PDF as encrypted.
    """

    import zlib

    if pages is None:
        pages = ["Hello world.\nSecond line."]

    def escape_pdf(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    # Build page objects: [catalog=1, pages=2, page_3, contents_3, page_4, contents_4, ...]
    # Then a single font object at the end.
    page_obj_nums: list[int] = []
    content_obj_nums: list[int] = []
    bodies: list[bytes] = []

    # placeholder indexes: we will assign them after we know the font obj number
    # We'll interleave: for N pages, objs 1..2 + 2*N page/content + 1 font
    font_num = 2 + 2 * len(pages) + 1

    bodies.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids_refs = " ".join(f"{3 + 2 * i} 0 R" for i in range(len(pages)))
    bodies.append(f"<< /Type /Pages /Kids [{kids_refs}] /Count {len(pages)} >>".encode())

    for i, page_text in enumerate(pages):
        page_num = 3 + 2 * i
        content_num = page_num + 1
        page_obj_nums.append(page_num)
        content_obj_nums.append(content_num)

        page_obj = (
            f"<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 612 792] "
            f"/Contents {content_num} 0 R "
            f"/Resources << /Font << /F1 {font_num} 0 R >> >> >>"
        ).encode()
        bodies.append(page_obj)

        lines = page_text.split("\n")
        parts = ["BT", "/F1 12 Tf", "50 700 Td"]
        for j, line in enumerate(lines):
            if j > 0:
                parts.append("0 -20 Td")
            parts.append(f"({escape_pdf(line)}) Tj")
        parts.append("ET")
        stream = (" ".join(parts)).encode("latin-1")

        if flate:
            compressed = zlib.compress(stream)
            header = f"<< /Length {len(compressed)} /Filter /FlateDecode >>".encode()
            bodies.append(header + b"\nstream\n" + compressed + b"\nendstream")
        else:
            header = f"<< /Length {len(stream)} >>".encode()
            bodies.append(header + b"\nstream\n" + stream + b"\nendstream")

    bodies.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    buf = io.BytesIO()
    buf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")  # binary comment = standard
    offsets: list[int] = []
    for idx, body in enumerate(bodies, start=1):
        offsets.append(buf.tell())
        buf.write(f"{idx} 0 obj\n".encode())
        buf.write(body)
        buf.write(b"\nendobj\n")

    xref_pos = buf.tell()
    buf.write(f"xref\n0 {len(bodies) + 1}\n".encode())
    buf.write(b"0000000000 65535 f \n")
    for offset in offsets:
        buf.write(f"{offset:010d} 00000 n \n".encode())
    trailer_bits = [f"/Size {len(bodies) + 1}", "/Root 1 0 R"]
    if encrypt:
        trailer_bits.append("/Encrypt 99 0 R")
    buf.write(f"trailer\n<< {' '.join(trailer_bits)} >>\nstartxref\n{xref_pos}\n%%EOF".encode())
    return buf.getvalue()


@pytest.fixture
def fixtures_root() -> Path:
    return FIXTURES_ROOT


@pytest.fixture
def article_html() -> str:
    return (FIXTURES_ROOT / "sample_article.html").read_text(encoding="utf-8")


@pytest.fixture
def article_artifact() -> FetchedArtifact:
    return make_article_artifact()


@pytest.fixture
def simple_pdf_bytes() -> bytes:
    return build_minimal_pdf(pages=["Hello world.\nSecond line.", "Page two body."])


@pytest.fixture
def flate_pdf_bytes() -> bytes:
    return build_minimal_pdf(
        pages=["Deflated page one.\nHas two lines."],
        flate=True,
    )


@pytest.fixture
def encrypted_pdf_bytes() -> bytes:
    return build_minimal_pdf(
        pages=["Should not be readable."],
        encrypt=True,
    )


@pytest.fixture
def pdf_artifact(simple_pdf_bytes: bytes) -> FetchedArtifact:
    return make_pdf_artifact(raw_bytes=simple_pdf_bytes)
