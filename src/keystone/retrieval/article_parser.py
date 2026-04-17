"""Deterministic HTML -> section/paragraph parsing for Lane E.

Uses only the stdlib ``html.parser`` so parse behavior is reproducible
and requires no vendored HTML engine. The parser walks the document in
source order, maintaining a heading stack so each block-level passage
is emitted with a ``section_path`` that mirrors how a human reader would
summarise its location ("under <H1> / under <H2>").

What the parser does NOT do:

- It never infers or invents text: every emitted passage is derived from
  characters actually present in the input HTML.
- It does not execute scripts, apply styles, or follow links.
- It does not attempt semantic classification beyond the five structural
  kinds exposed on ``PassageKind``.

When the input degrades (empty body, no usable text, broken encoding
markers), the parser emits an explicit ``ParseWarning`` and lowers the
overall ParseConfidence score -- never a silent success.
"""

from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser

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

PARSER_NAME = "keystone.article.v1"
PARSER_VERSION = "1.0.0"

_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_BLOCK_TAGS = {
    "p",
    "li",
    "blockquote",
    "pre",
    "caption",
    "figcaption",
    "dt",
    "dd",
    "td",
    "th",
}
_SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}
_VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
_WHITESPACE = re.compile(r"[\s\u00A0]+")

_TAG_TO_KIND = {
    "p": PassageKind.PARAGRAPH,
    "li": PassageKind.LIST_ITEM,
    "dt": PassageKind.LIST_ITEM,
    "dd": PassageKind.LIST_ITEM,
    "blockquote": PassageKind.BLOCK_QUOTE,
    "pre": PassageKind.CODE,
    "caption": PassageKind.CAPTION,
    "figcaption": PassageKind.CAPTION,
    "td": PassageKind.TABLE,
    "th": PassageKind.TABLE,
}


class ArticleParser:
    """Turn a FetchedArtifact's HTML into a ParsedDocument."""

    parser_identity = ParserIdentity(name=PARSER_NAME, version=PARSER_VERSION)

    def parse(self, artifact: FetchedArtifact) -> ParsedDocument:
        """Parse ``artifact.content_text`` as HTML.

        If ``content_text`` is missing, the parser falls back to decoding
        ``content_bytes_b64`` as UTF-8 with a ``UTF8_DECODE_FALLBACK``
        warning. If no textual form is available at all, a document with
        zero passages and a LOW confidence is returned -- never an
        exception, so a single malformed artifact cannot fail a batch.
        """

        source_family = _family_for(artifact)
        warnings: list[ParseWarning] = []
        html_text = _extract_html(artifact, warnings)

        if not html_text.strip():
            warnings.append(
                ParseWarning(
                    code="EMPTY_HTML",
                    message="Article artifact carries no HTML body; no passages emitted",
                    locator=None,
                )
            )
            return ParsedDocument(
                artifact_id=artifact.artifact_id,
                source_family=source_family,
                parser=self.parser_identity,
                passages=[],
                warnings=warnings,
                overall_confidence=confidence(0.0, ["EMPTY_HTML"]),
            )

        collector = _ArticleCollector(artifact_id=artifact.artifact_id)
        try:
            collector.feed(html_text)
            collector.close()
        except (ValueError, AssertionError) as exc:  # html.parser strict-mode paths
            warnings.append(
                ParseWarning(
                    code="HTML_MALFORMED",
                    message=f"HTML parser raised {type(exc).__name__}: {exc}",
                    locator=None,
                )
            )

        warnings.extend(collector.warnings)
        passages = collector.passages
        score, reasons = _score_article(html_text, passages, warnings)

        return ParsedDocument(
            artifact_id=artifact.artifact_id,
            source_family=source_family,
            parser=self.parser_identity,
            passages=passages,
            warnings=warnings,
            overall_confidence=confidence(score, reasons),
        )


def _family_for(artifact: FetchedArtifact) -> SourceFamily:
    if artifact.source_family is not SourceFamily.UNKNOWN:
        return artifact.source_family
    return SourceFamily.ARTICLE


def _extract_html(artifact: FetchedArtifact, warnings: list[ParseWarning]) -> str:
    if artifact.content_text is not None:
        return artifact.content_text
    if artifact.content_bytes_b64 is not None:
        import base64

        try:
            decoded = base64.b64decode(artifact.content_bytes_b64, validate=False)
        except (ValueError, TypeError) as exc:
            warnings.append(
                ParseWarning(
                    code="BASE64_DECODE_FAILED",
                    message=f"Could not base64-decode content_bytes_b64: {exc}",
                    locator=None,
                )
            )
            return ""
        try:
            text = decoded.decode("utf-8")
            warnings.append(
                ParseWarning(
                    code="UTF8_DECODE_FALLBACK",
                    message="content_text missing; decoded content_bytes_b64 as UTF-8",
                    locator=None,
                )
            )
            return text
        except UnicodeDecodeError as exc:
            text = decoded.decode("utf-8", errors="replace")
            warnings.append(
                ParseWarning(
                    code="UTF8_DECODE_LOSSY",
                    message=(
                        "content_bytes_b64 was not valid UTF-8; "
                        f"decoded with replacement chars (error at byte {exc.start})"
                    ),
                    locator=None,
                )
            )
            return text
    return ""


def _score_article(
    html_text: str, passages: list[ParsedPassage], warnings: list[ParseWarning]
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 1.0
    if not passages:
        return 0.0, ["NO_PASSAGES_EMITTED"]

    text_chars = sum(len(p.text) for p in passages)
    if text_chars < 40:
        score = min(score, 0.5)
        reasons.append("LOW_TEXT_VOLUME")

    html_chars = max(1, len(html_text))
    ratio = text_chars / html_chars
    if ratio < 0.02:
        score = min(score, 0.6)
        reasons.append("LOW_TEXT_TO_MARKUP_RATIO")

    warning_codes = {w.code for w in warnings}
    if "HTML_MALFORMED" in warning_codes:
        score = min(score, 0.55)
        reasons.append("HTML_MALFORMED")
    if "UTF8_DECODE_LOSSY" in warning_codes:
        score = min(score, 0.6)
        reasons.append("UTF8_DECODE_LOSSY")
    if "UTF8_DECODE_FALLBACK" in warning_codes:
        score = min(score, 0.85)
        reasons.append("UTF8_DECODE_FALLBACK")
    if any(p.kind is PassageKind.SECTION_HEADING for p in passages):
        reasons.append("STRUCTURED_HEADINGS_DETECTED")

    return score, reasons


class _ArticleCollector(HTMLParser):
    """Stateful HTML walker that emits ParsedPassage records.

    State machine:

    - ``_skip_depth`` > 0 while inside a <script>, <style>, etc.
    - ``_section_stack`` is the live heading chain.
    - ``_block_stack`` holds the currently-open block-level container
      along with its accumulating text buffer.
    """

    def __init__(self, artifact_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self._artifact_id = artifact_id
        self._section_stack: list[tuple[int, str]] = []
        self._block_stack: list[_Block] = []
        self._tag_stack: list[str] = []
        self._passages: list[ParsedPassage] = []
        self._warnings: list[ParseWarning] = []
        self._skip_depth = 0
        self._paragraph_counts: dict[tuple[str, ...], int] = {}
        self._next_index = 0
        self._in_title = False

    @property
    def passages(self) -> list[ParsedPassage]:
        return list(self._passages)

    @property
    def warnings(self) -> list[ParseWarning]:
        return list(self._warnings)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        lname = tag.lower()
        if lname in _SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return
        if lname == "br":
            if self._block_stack:
                self._block_stack[-1].append_text(" ")
            return
        if lname in _VOID_TAGS:
            return
        self._tag_stack.append(lname)
        if lname == "title":
            self._in_title = True
            return
        if lname in _HEADING_TAGS:
            self._open_block(lname, PassageKind.SECTION_HEADING)
            return
        if lname in _BLOCK_TAGS:
            self._open_block(lname, _TAG_TO_KIND.get(lname, PassageKind.PARAGRAPH))
            return
        # inline tags: their text just accumulates in the current block

    def handle_endtag(self, tag: str) -> None:
        lname = tag.lower()
        if lname in _SKIP_TAGS:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if self._skip_depth > 0:
            return
        if lname in _VOID_TAGS:
            return
        self._check_tag_balance(lname)
        if lname == "title":
            self._in_title = False
            return
        if lname in _HEADING_TAGS:
            self._close_block(lname, is_heading=True)
            return
        if lname in _BLOCK_TAGS:
            self._close_block(lname, is_heading=False)
            return

    def _check_tag_balance(self, lname: str) -> None:
        if self._tag_stack and self._tag_stack[-1] == lname:
            self._tag_stack.pop()
            return
        if lname in self._tag_stack:
            self._warnings.append(
                ParseWarning(
                    code="HTML_TAG_MISMATCH",
                    message=f"</{lname}> closes at unexpected nesting depth",
                    locator=None,
                )
            )
            while self._tag_stack and self._tag_stack[-1] != lname:
                self._tag_stack.pop()
            if self._tag_stack:
                self._tag_stack.pop()
            return
        self._warnings.append(
            ParseWarning(
                code="HTML_TAG_MISMATCH",
                message=f"</{lname}> closed with no matching open tag",
                locator=None,
            )
        )

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        # Treat self-closing variants the same as the opening tag.
        lname = tag.lower()
        if lname == "br" and self._block_stack:
            self._block_stack[-1].append_text(" ")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if self._in_title:
            return
        if not self._block_stack:
            return
        self._block_stack[-1].append_text(data)

    def handle_entityref(self, name: str) -> None:
        if self._skip_depth > 0 or not self._block_stack:
            return
        # html.parser with convert_charrefs=True normally handles this,
        # but keep a fallback for unusual entities.
        self._block_stack[-1].append_text(unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        if self._skip_depth > 0 or not self._block_stack:
            return
        self._block_stack[-1].append_text(unescape(f"&#{name};"))

    def _open_block(self, tag: str, kind: PassageKind) -> None:
        # Close any dangling inline/block of the same type to match
        # the lenient behavior of real-world HTML.
        self._block_stack.append(_Block(tag=tag, kind=kind))

    def _close_block(self, tag: str, is_heading: bool) -> None:
        if not self._block_stack:
            return
        # Find the nearest matching block; if not found, close the innermost
        # open block instead to avoid leaking state on malformed markup.
        match_index: int | None = None
        for i in range(len(self._block_stack) - 1, -1, -1):
            if self._block_stack[i].tag == tag:
                match_index = i
                break
        if match_index is None:
            match_index = len(self._block_stack) - 1
            self._warnings.append(
                ParseWarning(
                    code="HTML_TAG_MISMATCH",
                    message=(
                        f"Closing </{tag}> with no matching open tag; "
                        f"closing {self._block_stack[match_index].tag!r} instead"
                    ),
                    locator=None,
                )
            )

        # Closing a block may flush any blocks opened inside it that never saw
        # their own end tag (e.g. an unclosed <p> inside an <li>).
        while len(self._block_stack) - 1 > match_index:
            self._flush(self._block_stack.pop(), is_heading=False)
        self._flush(self._block_stack.pop(), is_heading=is_heading)

    def _flush(self, block: _Block, is_heading: bool) -> None:
        text = block.text()
        if not text:
            return
        if is_heading:
            heading_level = int(block.tag[1:]) if block.tag[1:].isdigit() else 6
            while self._section_stack and self._section_stack[-1][0] >= heading_level:
                self._section_stack.pop()
            self._section_stack.append((heading_level, text))
            # Heading passages live at the parent path -- downstream can tell
            # "this text IS a heading" from "this text is UNDER that heading".
            section_path = [segment for _, segment in self._section_stack[:-1]]
        else:
            section_path = [segment for _, segment in self._section_stack]

        key = tuple(section_path)
        pindex = self._paragraph_counts.get(key, 0)
        self._paragraph_counts[key] = pindex + 1

        self._next_index += 1
        passage = ParsedPassage(
            passage_id=f"{self._artifact_id}-p{self._next_index:04d}",
            artifact_id=self._artifact_id,
            kind=block.kind,
            text=text,
            locator=Locator(
                section_path=list(section_path),
                paragraph_index=pindex,
            ),
            parse_confidence=confidence(
                0.95 if block.kind is not PassageKind.SECTION_HEADING else 0.9,
                ["STRUCTURED_BLOCK"],
            ),
        )
        self._passages.append(passage)

    def close(self) -> None:
        super().close()
        # Flush blocks still open at EOF (common in real HTML).
        while self._block_stack:
            block = self._block_stack.pop()
            self._flush(block, is_heading=block.tag in _HEADING_TAGS)


class _Block:
    """Mutable accumulator for the text of a single block-level element."""

    __slots__ = ("tag", "kind", "_buffer")

    def __init__(self, tag: str, kind: PassageKind) -> None:
        self.tag = tag
        self.kind = kind
        self._buffer: list[str] = []

    def append_text(self, chunk: str) -> None:
        if chunk:
            self._buffer.append(chunk)

    def text(self) -> str:
        raw = "".join(self._buffer)
        return _WHITESPACE.sub(" ", raw).strip()
