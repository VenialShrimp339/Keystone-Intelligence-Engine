"""Deterministic PDF -> page/paragraph parsing for Lane E.

Two input shapes are accepted, aligned with how Lane H persists
artifacts:

1. ``content_text`` is present. Lane H (or some upstream backend) has
   already extracted text. Pages are separated by form-feed (``\\f``);
   if no form feeds are present, the whole payload is treated as a
   single page. This is the happy path for production use where a
   capable backend (e.g. docling) already handled extraction.

2. ``content_bytes_b64`` is present. A PDF binary blob was preserved.
   Lane E falls back to a stdlib-only best-effort extractor that
   handles simple, uncompressed or FlateDecode-compressed content
   streams for text-showing operators (Tj/TJ/'/"). Anything fancier
   (encryption, CID fonts with CMaps, image-only pages) degrades to
   LOW parse confidence plus explicit warnings -- the parser never
   fabricates text.

The text-backend boundary is a protocol so callers can inject a
production-grade backend without changing the parser.
"""

from __future__ import annotations

import base64
import re
import zlib
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from keystone.retrieval.parse_models import (
    FetchedArtifact,
    Locator,
    ParsedDocument,
    ParsedPassage,
    ParserIdentity,
    ParseWarning,
    PassageKind,
    SourceFamily,
    confidence,
)

PARSER_NAME = "keystone.pdf.v1"
PARSER_VERSION = "1.0.0"

_PDF_HEADER = re.compile(rb"^%PDF-\d+\.\d+")
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")
_WHITESPACE = re.compile(r"[ \t\u00A0]+")


@dataclass(frozen=True)
class PDFPageText:
    """Raw text extracted for a single PDF page.

    Page numbers are one-based. ``confidence_score`` is the extractor's
    self-assessment for this particular page -- an empty page can sit
    next to a high-quality one without pulling the document score down.
    """

    page_number: int
    text: str
    confidence_score: float = 1.0
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PDFExtractionResult:
    """Full extractor output handed to the PDF parser."""

    pages: list[PDFPageText]
    warnings: list[str] = field(default_factory=list)
    encrypted: bool = False


@runtime_checkable
class PDFTextBackend(Protocol):
    """Pluggable PDF -> text backend.

    Implementations must be deterministic and side-effect free. They
    should never raise for malformed input: degrade instead via empty
    pages, low per-page confidence, and warning codes.
    """

    def extract(self, data: bytes) -> PDFExtractionResult: ...


class BasicPDFTextBackend:
    """Stdlib-only PDF text extractor.

    Scope is intentionally narrow -- enough to lift text from PDFs that
    carry pure text content streams (the common case for reports, press
    releases, filings exported to PDF). Out of scope:

    - Encrypted PDFs (detected; marked encrypted + zero pages).
    - CID/Type 0 fonts with custom CMaps (text may be partially mojibake;
      ``MOJIBAKE_SUSPECTED`` warning emitted).
    - Scanned image-only pages (zero text returned with warning).

    For production-grade extraction on adversarial PDFs, inject a
    richer backend (e.g. wrapping docling).
    """

    def extract(self, data: bytes) -> PDFExtractionResult:
        if not data:
            return PDFExtractionResult(pages=[], warnings=["EMPTY_BYTES"])
        if not _PDF_HEADER.match(data[:16]):
            return PDFExtractionResult(pages=[], warnings=["NOT_A_PDF"])
        if b"/Encrypt" in data[:8192] or b"/Encrypt" in data[-8192:]:
            return PDFExtractionResult(pages=[], warnings=["ENCRYPTED"], encrypted=True)

        objects = _scan_indirect_objects(data)
        if not objects:
            return PDFExtractionResult(pages=[], warnings=["NO_OBJECTS_FOUND"])

        page_obj_nums = _find_page_objects(objects)
        if not page_obj_nums:
            return PDFExtractionResult(pages=[], warnings=["NO_PAGES_FOUND"])

        pages: list[PDFPageText] = []
        doc_warnings: list[str] = []

        for i, obj_num in enumerate(page_obj_nums, start=1):
            page_obj = objects.get(obj_num)
            if page_obj is None:
                pages.append(
                    PDFPageText(
                        page_number=i,
                        text="",
                        confidence_score=0.0,
                        warnings=["PAGE_OBJECT_MISSING"],
                    )
                )
                continue

            content_nums = _content_refs(page_obj.header)
            if not content_nums:
                pages.append(
                    PDFPageText(
                        page_number=i,
                        text="",
                        confidence_score=0.2,
                        warnings=["NO_CONTENT_STREAM"],
                    )
                )
                continue

            page_text_parts: list[str] = []
            page_warnings: list[str] = []
            for content_num in content_nums:
                content_obj = objects.get(content_num)
                if content_obj is None:
                    page_warnings.append("CONTENT_OBJECT_MISSING")
                    continue
                stream, stream_warnings = _decode_stream(content_obj)
                page_warnings.extend(stream_warnings)
                if stream is None:
                    continue
                text, op_warnings = _extract_text_from_stream(stream)
                page_warnings.extend(op_warnings)
                if text:
                    page_text_parts.append(text)

            joined = _clean_whitespace("\n".join(page_text_parts))
            page_score = _score_page(joined, page_warnings)
            pages.append(
                PDFPageText(
                    page_number=i,
                    text=joined,
                    confidence_score=page_score,
                    warnings=page_warnings,
                )
            )

        return PDFExtractionResult(pages=pages, warnings=doc_warnings)


class PDFParser:
    """Turn a FetchedArtifact's PDF payload into a ParsedDocument."""

    parser_identity = ParserIdentity(name=PARSER_NAME, version=PARSER_VERSION)

    def __init__(self, backend: PDFTextBackend | None = None) -> None:
        self._backend: PDFTextBackend = backend or BasicPDFTextBackend()

    def parse(self, artifact: FetchedArtifact) -> ParsedDocument:
        warnings: list[ParseWarning] = []

        if artifact.content_text is not None:
            pages = _split_pretext_into_pages(artifact.content_text)
            from_extraction = False
        else:
            pages, extraction_warnings, encrypted = self._from_bytes(artifact)
            for code in extraction_warnings:
                warnings.append(
                    ParseWarning(
                        code=code,
                        message=_warning_message(code),
                        locator=None,
                    )
                )
            if encrypted:
                return ParsedDocument(
                    artifact_id=artifact.artifact_id,
                    source_family=SourceFamily.PDF,
                    parser=self.parser_identity,
                    passages=[],
                    warnings=warnings,
                    overall_confidence=confidence(0.0, ["ENCRYPTED"]),
                )
            from_extraction = True

        if not pages:
            warnings.append(
                ParseWarning(
                    code="EMPTY_PDF",
                    message="PDF artifact produced no pages",
                    locator=None,
                )
            )
            return ParsedDocument(
                artifact_id=artifact.artifact_id,
                source_family=SourceFamily.PDF,
                parser=self.parser_identity,
                passages=[],
                warnings=warnings,
                overall_confidence=confidence(0.0, ["EMPTY_PDF"]),
            )

        passages: list[ParsedPassage] = []
        next_index = 0
        for page in pages:
            if not page.text.strip():
                warnings.append(
                    ParseWarning(
                        code="EMPTY_PAGE",
                        message=f"Page {page.page_number} produced no text",
                        locator=Locator(
                            section_path=[],
                            paragraph_index=0,
                            page_number=page.page_number,
                        ),
                    )
                )
                continue

            paragraphs = _paragraphs(page.text)
            for p_idx, para in enumerate(paragraphs):
                next_index += 1
                passages.append(
                    ParsedPassage(
                        passage_id=f"{artifact.artifact_id}-pg{page.page_number:04d}-p{p_idx:04d}",
                        artifact_id=artifact.artifact_id,
                        kind=PassageKind.PARAGRAPH,
                        text=para,
                        locator=Locator(
                            section_path=[],
                            paragraph_index=p_idx,
                            page_number=page.page_number,
                        ),
                        parse_confidence=confidence(
                            page.confidence_score,
                            list(page.warnings) or ["PDF_PAGE_TEXT"],
                        ),
                    )
                )

        overall_score, reasons = _score_document(pages, warnings, from_extraction)

        return ParsedDocument(
            artifact_id=artifact.artifact_id,
            source_family=SourceFamily.PDF,
            parser=self.parser_identity,
            passages=passages,
            warnings=warnings,
            overall_confidence=confidence(overall_score, reasons),
        )

    def _from_bytes(self, artifact: FetchedArtifact) -> tuple[list[PDFPageText], list[str], bool]:
        assert artifact.content_bytes_b64 is not None
        try:
            data = base64.b64decode(artifact.content_bytes_b64, validate=False)
        except (ValueError, TypeError):
            return [], ["BASE64_DECODE_FAILED"], False

        result = self._backend.extract(data)
        return list(result.pages), list(result.warnings), result.encrypted


# ---------------------------------------------------------------------------
# Pre-extracted text path
# ---------------------------------------------------------------------------


def _split_pretext_into_pages(text: str) -> list[PDFPageText]:
    """Split a pre-extracted PDF text payload into per-page records."""

    if not text:
        return []
    # Standard PDF-to-text tools separate pages with form feed.
    chunks = text.split("\f")
    pages: list[PDFPageText] = []
    for i, chunk in enumerate(chunks, start=1):
        cleaned = _clean_whitespace(chunk)
        pages.append(
            PDFPageText(
                page_number=i,
                text=cleaned,
                confidence_score=0.95 if cleaned else 0.3,
                warnings=[] if cleaned else ["EMPTY_PAGE"],
            )
        )
    return pages


def _paragraphs(page_text: str) -> list[str]:
    """Split a page's text into paragraph-level passages."""

    paragraphs: list[str] = []
    for chunk in _PARAGRAPH_SPLIT.split(page_text):
        cleaned = chunk.strip()
        if cleaned:
            paragraphs.append(cleaned)
    if not paragraphs and page_text.strip():
        paragraphs.append(page_text.strip())
    return paragraphs


def _clean_whitespace(text: str) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        collapsed = _WHITESPACE.sub(" ", raw).strip()
        lines.append(collapsed)
    collapsed = "\n".join(lines)
    # Collapse runs of blank lines to a single blank line so _paragraphs works.
    return re.sub(r"\n{3,}", "\n\n", collapsed).strip()


# ---------------------------------------------------------------------------
# PDF binary helpers (stdlib-only, best effort)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _IndirectObject:
    obj_num: int
    header: bytes
    stream: bytes | None


_OBJ_PATTERN = re.compile(rb"(\d+)\s+\d+\s+obj\b(.*?)\bendobj\b", re.DOTALL)
_STREAM_PATTERN = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)


def _scan_indirect_objects(data: bytes) -> dict[int, _IndirectObject]:
    objects: dict[int, _IndirectObject] = {}
    for match in _OBJ_PATTERN.finditer(data):
        obj_num = int(match.group(1))
        body = match.group(2)
        stream_match = _STREAM_PATTERN.search(body)
        if stream_match is not None:
            header = body[: stream_match.start()]
            stream = stream_match.group(1)
        else:
            header = body
            stream = None
        objects[obj_num] = _IndirectObject(obj_num=obj_num, header=header, stream=stream)
    return objects


def _find_page_objects(objects: dict[int, _IndirectObject]) -> list[int]:
    """Return page-object numbers in document order.

    Order is recovered from the first ``/Kids`` array encountered in a
    ``/Type /Pages`` object. If no /Pages object is present, fall back
    to any object tagged ``/Type /Page`` in numeric order.
    """

    pages_obj: _IndirectObject | None = None
    for obj in objects.values():
        if b"/Type /Pages" in obj.header or b"/Type/Pages" in obj.header:
            pages_obj = obj
            break

    if pages_obj is not None:
        kids = _parse_ref_array(pages_obj.header, b"/Kids")
        if kids:
            ordered: list[int] = []
            for kid in kids:
                _visit_page_node(kid, objects, ordered)
            if ordered:
                return ordered

    fallback = [
        obj_num
        for obj_num, obj in sorted(objects.items())
        if b"/Type /Page" in obj.header or b"/Type/Page" in obj.header
        if b"/Type /Pages" not in obj.header
        if b"/Type/Pages" not in obj.header
    ]
    return fallback


def _visit_page_node(obj_num: int, objects: dict[int, _IndirectObject], ordered: list[int]) -> None:
    obj = objects.get(obj_num)
    if obj is None:
        return
    if b"/Type /Pages" in obj.header or b"/Type/Pages" in obj.header:
        for kid in _parse_ref_array(obj.header, b"/Kids"):
            _visit_page_node(kid, objects, ordered)
        return
    if b"/Type /Page" in obj.header or b"/Type/Page" in obj.header:
        ordered.append(obj_num)


_REF_ARRAY = re.compile(rb"\[\s*((?:\d+\s+\d+\s+R\s*)+)\]")


def _parse_ref_array(header: bytes, key: bytes) -> list[int]:
    idx = header.find(key)
    if idx == -1:
        return []
    tail = header[idx + len(key) :]
    match = _REF_ARRAY.search(tail)
    if match is None:
        return []
    refs = re.findall(rb"(\d+)\s+\d+\s+R", match.group(1))
    return [int(r) for r in refs]


_CONTENTS_SINGLE = re.compile(rb"/Contents\s+(\d+)\s+\d+\s+R")
_CONTENTS_ARRAY = re.compile(rb"/Contents\s*\[\s*((?:\d+\s+\d+\s+R\s*)+)\]")


def _content_refs(header: bytes) -> list[int]:
    arr_match = _CONTENTS_ARRAY.search(header)
    if arr_match is not None:
        return [int(n) for n in re.findall(rb"(\d+)\s+\d+\s+R", arr_match.group(1))]
    single = _CONTENTS_SINGLE.search(header)
    if single is not None:
        return [int(single.group(1))]
    return []


def _decode_stream(obj: _IndirectObject) -> tuple[bytes | None, list[str]]:
    if obj.stream is None:
        return None, ["NO_STREAM_FOR_OBJECT"]
    warnings: list[str] = []
    data = obj.stream
    filter_match = re.search(rb"/Filter\s*(\S+)", obj.header)
    if filter_match is None:
        return data, warnings
    filt = filter_match.group(1)
    if b"FlateDecode" in filt:
        try:
            data = zlib.decompress(data)
        except zlib.error:
            warnings.append("FLATE_DECOMPRESS_FAILED")
            return None, warnings
    elif b"ASCIIHexDecode" in filt or b"ASCII85Decode" in filt:
        warnings.append("ASCII_FILTER_UNSUPPORTED")
        return None, warnings
    elif b"DCTDecode" in filt or b"CCITTFaxDecode" in filt or b"JBIG2Decode" in filt:
        warnings.append("IMAGE_ONLY_STREAM")
        return None, warnings
    else:
        warnings.append("UNKNOWN_FILTER")
        return None, warnings
    return data, warnings


# ---------------------------------------------------------------------------
# Content-stream text extraction
# ---------------------------------------------------------------------------

_OCTAL_ESCAPE = re.compile(rb"\\([0-7]{1,3})")


_LINE_MOVE_OPS = (b"Td", b"TD", b"Tm", b"T*")


def _extract_text_from_stream(stream: bytes) -> tuple[str, list[str]]:
    """Walk a decoded content stream and pull text from showing operators.

    Newlines are inserted at line-moving operators (Td/TD/Tm/T*) and at
    ET boundaries so downstream paragraph-splitting has a chance to
    recover document structure. All glyph bytes flow through the
    CP1252/Latin-1 decode path; genuinely custom CID fonts are flagged
    via the MOJIBAKE_SUSPECTED heuristic.
    """

    warnings: list[str] = []
    pieces: list[str] = []
    pending_newline = False
    i = 0
    length = len(stream)
    saw_op = False

    def emit(chunk: str) -> None:
        nonlocal pending_newline
        if pending_newline and pieces and not pieces[-1].endswith("\n"):
            pieces.append("\n")
        pending_newline = False
        if chunk:
            pieces.append(chunk)

    while i < length:
        ch = stream[i : i + 1]
        if ch == b"(":
            literal, consumed = _read_literal_string(stream, i)
            if literal is None:
                warnings.append("UNBALANCED_LITERAL")
                break
            i += consumed
            op, op_bytes = _peek_next_op(stream, i)
            if op in {b"Tj", b"'", b'"'}:
                saw_op = True
                emit(_decode_bytes(literal))
                i += op_bytes
                if op in {b"'", b'"'}:
                    pending_newline = True
            elif op == b"TJ":
                saw_op = True
                emit(_decode_bytes(literal))
                i += op_bytes
            continue
        if ch == b"<" and stream[i : i + 2] != b"<<":
            hex_literal, consumed = _read_hex_string(stream, i)
            if hex_literal is None:
                i += 1
                continue
            i += consumed
            op, op_bytes = _peek_next_op(stream, i)
            if op in {b"Tj", b"'", b'"'}:
                saw_op = True
                emit(_decode_bytes(hex_literal))
                i += op_bytes
                if op in {b"'", b'"'}:
                    pending_newline = True
            continue
        if ch == b"[":
            array_text, consumed, had_op = _read_tj_array(stream, i)
            if consumed > 0:
                if had_op:
                    saw_op = True
                    emit(array_text)
                i += consumed
                continue
        if stream[i : i + 2] == b"ET":
            # ET ends a text block; treat as a paragraph boundary by
            # emitting a blank line (downstream splits on \n\s*\n).
            emit("")
            pieces.append("\n\n")
            pending_newline = False
            i += 2
            continue
        if _is_op_here(stream, i, _LINE_MOVE_OPS):
            pending_newline = True
            # advance past the op chars and let the next iteration skip whitespace
            i += 2 if stream[i : i + 2] in (b"Td", b"TD", b"Tm", b"T*") else 1
            continue
        i += 1

    if not saw_op:
        warnings.append("NO_TEXT_OPERATORS")
    text = "".join(pieces)
    if text and _looks_like_mojibake(text):
        warnings.append("MOJIBAKE_SUSPECTED")
    return text, warnings


def _is_op_here(stream: bytes, i: int, ops: tuple[bytes, ...]) -> bool:
    for op in ops:
        if stream[i : i + len(op)] == op:
            end = i + len(op)
            before_ok = i == 0 or stream[i - 1 : i] in (b" ", b"\n", b"\r", b"\t", b"]", b")")
            after_ok = end == len(stream) or stream[end : end + 1] in (
                b" ",
                b"\n",
                b"\r",
                b"\t",
            )
            if before_ok and after_ok:
                return True
    return False


def _peek_next_op(stream: bytes, start: int) -> tuple[bytes, int]:
    i = start
    length = len(stream)
    while i < length and stream[i : i + 1] in (b" ", b"\n", b"\r", b"\t"):
        i += 1
    for op in (b"TJ", b"Tj", b"'", b'"'):
        if stream[i : i + len(op)] == op:
            end = i + len(op)
            if end == length or stream[end : end + 1] in (b" ", b"\n", b"\r", b"\t", b"/"):
                return op, (end - start)
    return b"", 0


def _read_literal_string(stream: bytes, start: int) -> tuple[bytes | None, int]:
    assert stream[start : start + 1] == b"("
    i = start + 1
    depth = 1
    buf = bytearray()
    length = len(stream)
    while i < length:
        ch = stream[i : i + 1]
        if ch == b"\\":
            if i + 1 >= length:
                return None, 0
            nxt = stream[i + 1 : i + 2]
            if nxt in (b"n", b"r", b"t", b"b", b"f"):
                buf.append({b"n": 10, b"r": 13, b"t": 9, b"b": 8, b"f": 12}[nxt])
                i += 2
                continue
            if nxt in (b"(", b")", b"\\"):
                buf.append(nxt[0])
                i += 2
                continue
            if nxt.isdigit():
                # up to 3 octal digits
                j = i + 1
                digits = bytearray()
                while j < length and stream[j : j + 1].isdigit() and len(digits) < 3:
                    digits.append(stream[j])
                    j += 1
                buf.append(int(digits.decode("ascii"), 8) & 0xFF)
                i = j
                continue
            # unknown escape -- drop the backslash per PDF spec
            i += 1
            continue
        if ch == b"(":
            depth += 1
            buf.append(ch[0])
            i += 1
            continue
        if ch == b")":
            depth -= 1
            if depth == 0:
                return bytes(buf), (i + 1 - start)
            buf.append(ch[0])
            i += 1
            continue
        buf.append(ch[0])
        i += 1
    return None, 0


def _read_hex_string(stream: bytes, start: int) -> tuple[bytes | None, int]:
    assert stream[start : start + 1] == b"<"
    end = stream.find(b">", start + 1)
    if end == -1:
        return None, 0
    hex_part = stream[start + 1 : end]
    hex_clean = re.sub(rb"\s+", b"", hex_part)
    if len(hex_clean) % 2 == 1:
        hex_clean += b"0"
    try:
        return bytes.fromhex(hex_clean.decode("ascii")), (end + 1 - start)
    except ValueError:
        return None, (end + 1 - start)


def _read_tj_array(stream: bytes, start: int) -> tuple[str, int, bool]:
    """Parse a ``[ (chunk) num (chunk) ... ] TJ`` sequence."""

    assert stream[start : start + 1] == b"["
    i = start + 1
    length = len(stream)
    pieces: list[str] = []
    while i < length:
        ch = stream[i : i + 1]
        if ch == b"]":
            i += 1
            op, op_bytes = _peek_next_op(stream, i)
            if op == b"TJ":
                return "".join(pieces), (i + op_bytes - start), True
            return "".join(pieces), (i - start), False
        if ch == b"(":
            literal, consumed = _read_literal_string(stream, i)
            if literal is None:
                return "", 0, False
            pieces.append(_decode_bytes(literal))
            i += consumed
            continue
        if ch == b"<":
            hex_literal, consumed = _read_hex_string(stream, i)
            if hex_literal is None:
                i += 1
                continue
            pieces.append(_decode_bytes(hex_literal))
            i += consumed
            continue
        i += 1
    return "", 0, False


def _decode_bytes(data: bytes) -> str:
    """Best-effort decode of string bytes from a content stream.

    Tries UTF-16 BE (BOM-marked) first, then WinAnsi (cp1252), then
    Latin-1 as a last-resort. Non-decodable bytes are replaced with
    U+FFFD; this causes ``_looks_like_mojibake`` to flag the page.
    """

    if data.startswith(b"\xfe\xff"):
        try:
            return data[2:].decode("utf-16-be")
        except UnicodeDecodeError:
            return data[2:].decode("utf-16-be", errors="replace")
    try:
        return data.decode("cp1252")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


_MOJIBAKE_THRESHOLD = 0.3


def _looks_like_mojibake(text: str) -> bool:
    if not text:
        return False
    replacements = text.count("\ufffd")
    # High-bit non-ASCII that fall outside Latin-1 printable.
    suspicious = sum(1 for c in text if ord(c) < 0x20 and c not in "\n\r\t")
    total = len(text)
    return (replacements + suspicious) / max(1, total) > _MOJIBAKE_THRESHOLD


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _score_page(text: str, warnings: list[str]) -> float:
    if not text.strip():
        return 0.2
    score = 0.95
    if "MOJIBAKE_SUSPECTED" in warnings:
        score = min(score, 0.5)
    if "UNKNOWN_FILTER" in warnings:
        score = min(score, 0.4)
    if "FLATE_DECOMPRESS_FAILED" in warnings:
        score = min(score, 0.3)
    if "NO_TEXT_OPERATORS" in warnings:
        score = min(score, 0.3)
    if "IMAGE_ONLY_STREAM" in warnings:
        score = min(score, 0.2)
    return score


def _score_document(
    pages: list[PDFPageText], warnings: list[ParseWarning], from_extraction: bool
) -> tuple[float, list[str]]:
    if not pages:
        return 0.0, ["NO_PAGES"]
    reasons: list[str] = []
    avg = sum(p.confidence_score for p in pages) / len(pages)
    score = avg
    non_empty = sum(1 for p in pages if p.text.strip())
    if non_empty == 0:
        return 0.0, ["ALL_PAGES_EMPTY"]
    if non_empty < len(pages):
        score = min(score, 0.7)
        reasons.append("PARTIAL_PAGE_COVERAGE")
    if from_extraction:
        reasons.append("BINARY_EXTRACTION")
    else:
        reasons.append("PREEXTRACTED_TEXT")
    warning_codes = {w.code for w in warnings}
    for code in warning_codes:
        if code not in reasons:
            reasons.append(code)
    return score, reasons


# ---------------------------------------------------------------------------
# Warning code -> human message
# ---------------------------------------------------------------------------

_WARNING_MESSAGES = {
    "EMPTY_BYTES": "PDF payload was empty",
    "NOT_A_PDF": "Content did not start with a %PDF- header",
    "ENCRYPTED": "PDF is encrypted; cannot extract text with the basic backend",
    "NO_OBJECTS_FOUND": "PDF structure contained no parseable indirect objects",
    "NO_PAGES_FOUND": "PDF structure contained no /Type /Page objects",
    "BASE64_DECODE_FAILED": "content_bytes_b64 was not valid base64",
    "PAGE_OBJECT_MISSING": "A /Kids reference pointed to a missing page object",
    "NO_CONTENT_STREAM": "Page object had no /Contents reference",
    "CONTENT_OBJECT_MISSING": "A /Contents reference pointed to a missing object",
    "NO_STREAM_FOR_OBJECT": "Object referenced as content had no stream body",
    "FLATE_DECOMPRESS_FAILED": "zlib could not decompress a FlateDecode stream",
    "ASCII_FILTER_UNSUPPORTED": "ASCII filter pipelines are not handled by the basic backend",
    "IMAGE_ONLY_STREAM": "Content stream used image filters; no text available",
    "UNKNOWN_FILTER": "Content stream used an unsupported filter",
    "NO_TEXT_OPERATORS": "Content stream contained no Tj/TJ/'/\" operators",
    "MOJIBAKE_SUSPECTED": "Extracted text contains replacement chars; font encoding likely custom",
    "UNBALANCED_LITERAL": "Hit end of stream inside an unbalanced literal string",
}


def _warning_message(code: str) -> str:
    return _WARNING_MESSAGES.get(code, f"PDF parse warning: {code}")
