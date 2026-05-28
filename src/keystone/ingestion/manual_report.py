"""Manual Deep Research report ingestion for the first Keystone slice."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from keystone.artifacts.models import (
    ArtifactStatus,
    EvidenceBundleArtifact,
    ResearchReportArtifact,
    SourceBundleArtifact,
    SourceFormat,
    make_artifact_id,
)

if TYPE_CHECKING:
    from keystone.artifacts.store import LocalArtifactStore

_URL_RE = re.compile(r"https?://[^\s\]\)<>'\"]+")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_REF_RE = re.compile(r"^\[([A-Za-z0-9_-]+)\]:\s*(https?://\S+)", re.MULTILINE)
_INLINE_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
_REF_MARKER_RE = re.compile(r"\[([A-Za-z0-9_-]+)\]")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


@dataclass(frozen=True)
class ReportIngestionResult:
    """Artifacts produced by one manual report ingestion."""

    report: ResearchReportArtifact
    source_bundle: SourceBundleArtifact
    evidence_bundle: EvidenceBundleArtifact


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"h1", "h2", "h3", "p", "li", "br"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self._parts.append(stripped)

    def text(self) -> str:
        return "\n".join(part for part in self._parts if part.strip())


class ManualUploadAdapter:
    """Convert saved markdown/text/HTML reports into Keystone evidence artifacts."""

    def __init__(self, store: LocalArtifactStore | None = None) -> None:
        self._store = store

    def ingest_file(
        self,
        path: str | Path,
        *,
        run_id: str,
        provider_job_id: str | None = None,
        issue_node_ids: list[str] | None = None,
        source_format: SourceFormat | None = None,
    ) -> ReportIngestionResult:
        source_path = Path(path)
        raw_text = source_path.read_text(encoding="utf-8")
        resolved_format = source_format or _infer_source_format(source_path)
        normalized_text = _normalize_text(raw_text, resolved_format)

        title = _extract_title(normalized_text, fallback=source_path.stem)
        sections = _extract_sections(normalized_text)
        source_records, reference_map = _extract_sources(normalized_text, sections)
        claim_records = _extract_claims(normalized_text, sections, reference_map)
        quality_flags = _quality_flags(source_records, claim_records)

        report_id = make_artifact_id("report", run_id, source_path.name, title)
        source_bundle_id = make_artifact_id("sources", report_id)
        evidence_bundle_id = make_artifact_id("evidence", report_id)

        raw_path: str | None = None
        normalized_path: str | None = None
        if self._store is not None:
            raw_path = str(self._store.copy_file(run_id, source_path, f"raw/{source_path.name}"))
            normalized_path = str(
                self._store.write_text_file(
                    run_id,
                    f"normalized/{report_id}.txt",
                    normalized_text,
                )
            )

        report = ResearchReportArtifact(
            artifact_id=report_id,
            run_id=run_id,
            status=ArtifactStatus.READY if source_records else ArtifactStatus.PARTIAL,
            provider_job_id=provider_job_id,
            parent_artifact_ids=[provider_job_id] if provider_job_id else [],
            title=title,
            source_format=resolved_format,
            issue_node_ids=issue_node_ids or [],
            raw_path=raw_path,
            normalized_path=normalized_path,
            section_records=sections,
            source_records=source_records,
            candidate_claim_records=claim_records,
            quality_flags=quality_flags,
        )
        source_bundle = SourceBundleArtifact(
            artifact_id=source_bundle_id,
            run_id=run_id,
            status=ArtifactStatus.READY if source_records else ArtifactStatus.PARTIAL,
            parent_artifact_ids=[report.artifact_id],
            report_artifact_ids=[report.artifact_id],
            source_records=source_records,
        )
        evidence_bundle = EvidenceBundleArtifact(
            artifact_id=evidence_bundle_id,
            run_id=run_id,
            status=ArtifactStatus.READY if claim_records else ArtifactStatus.PARTIAL,
            parent_artifact_ids=[report.artifact_id, source_bundle.artifact_id],
            report_artifact_ids=[report.artifact_id],
            source_bundle_artifact_id=source_bundle.artifact_id,
            claim_records=claim_records,
            source_records=source_records,
            quality_flags=quality_flags,
        )

        if self._store is not None:
            self._store.write_artifact(report)
            self._store.write_artifact(source_bundle)
            self._store.write_artifact(evidence_bundle)

        return ReportIngestionResult(
            report=report,
            source_bundle=source_bundle,
            evidence_bundle=evidence_bundle,
        )


def _infer_source_format(path: Path) -> SourceFormat:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return SourceFormat.MARKDOWN
    if suffix in {".html", ".htm"}:
        return SourceFormat.HTML
    if suffix == ".txt":
        return SourceFormat.TEXT
    return SourceFormat.UNKNOWN


def _normalize_text(raw_text: str, source_format: SourceFormat) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    if source_format == SourceFormat.HTML:
        parser = _TextExtractor()
        parser.feed(text)
        text = parser.text()
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip() + "\n"


def _extract_title(text: str, *, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        heading = _HEADING_RE.match(stripped)
        return heading.group(2).strip() if heading else stripped[:160]
    return fallback


def _extract_sections(text: str) -> list[dict]:
    sections: list[dict] = []
    current: dict | None = None
    buffer: list[str] = []
    start_line = 1

    def flush(end_line: int) -> None:
        nonlocal buffer, current
        if current is None:
            return
        section_text = "\n".join(buffer).strip()
        current["text"] = section_text
        current["end_line"] = end_line
        sections.append(current)
        buffer = []

    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        heading = _HEADING_RE.match(line.strip())
        if heading:
            flush(idx - 1)
            start_line = idx
            current = {
                "section_id": f"section_{len(sections) + 1:03d}",
                "title": heading.group(2).strip(),
                "level": len(heading.group(1)),
                "start_line": start_line,
                "end_line": start_line,
                "text": "",
            }
            continue

        if current is None:
            current = {
                "section_id": "section_001",
                "title": "Report",
                "level": 1,
                "start_line": start_line,
                "end_line": start_line,
                "text": "",
            }
        buffer.append(line)

    flush(len(lines))
    return [section for section in sections if section["text"] or section["title"]]


def _extract_sources(text: str, sections: list[dict]) -> tuple[list[dict], dict[str, str]]:
    ordered_urls: list[tuple[str, str | None, str | None]] = []
    reference_map: dict[str, str] = {}

    for match in _REF_RE.finditer(text):
        key = match.group(1)
        url = _clean_url(match.group(2))
        reference_map[key] = url
        ordered_urls.append((url, key, None))

    for label, url in _INLINE_LINK_RE.findall(text):
        ordered_urls.append((_clean_url(url), None, label.strip()))

    for url in _URL_RE.findall(text):
        ordered_urls.append((_clean_url(url), None, None))

    seen: dict[str, str] = {}
    records: list[dict] = []
    for url, reference_key, label in ordered_urls:
        if url in seen:
            if reference_key:
                reference_map[reference_key] = seen[url]
            continue

        source_id = f"SRC-{len(records) + 1:03d}"
        seen[url] = source_id
        reference_map[url] = source_id
        if reference_key:
            reference_map[reference_key] = source_id
        first_section = _section_for_text(url, sections)
        parsed = urlparse(url)
        records.append(
            {
                "source_id": source_id,
                "url": url,
                "domain": parsed.netloc,
                "label": label or reference_key or parsed.netloc,
                "reference_key": reference_key,
                "first_seen_section_id": first_section,
            }
        )
        for alias in _source_aliases(url, label, reference_key):
            reference_map.setdefault(alias, source_id)

    for key, value in list(reference_map.items()):
        if value.startswith("http"):
            reference_map[key] = seen[value]

    return records, reference_map


def _extract_claims(
    text: str,
    sections: list[dict],
    reference_map: dict[str, str],
    *,
    limit: int = 24,
) -> list[dict]:
    claims: list[dict] = []
    for section in sections:
        for candidate in _candidate_units(section["text"]):
            citation_ids = _citation_ids(candidate, reference_map)
            flags = [] if citation_ids else ["missing_citation"]
            claims.append(
                {
                    "claim_id": f"CLM-{len(claims) + 1:03d}",
                    "text": _strip_markdown(candidate),
                    "section_id": section["section_id"],
                    "citation_ids": citation_ids,
                    "quality_flags": flags,
                    "confidence": 0.55 if citation_ids else 0.35,
                }
            )
            if len(claims) >= limit:
                return claims
    return claims


def _candidate_units(section_text: str) -> list[str]:
    units: list[str] = []
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if not line or _REF_RE.match(line) or _HEADING_RE.match(line):
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        if len(line) < 35:
            continue
        for sentence in _SENTENCE_SPLIT_RE.split(line):
            cleaned = sentence.strip()
            if len(cleaned) >= 35 and _looks_like_claim(cleaned):
                units.append(cleaned)
    return units


def _citation_ids(text: str, reference_map: dict[str, str]) -> list[str]:
    citation_ids: list[str] = []
    lower_text = text.lower()
    for marker in _REF_MARKER_RE.findall(text):
        if marker in reference_map and reference_map[marker] not in citation_ids:
            citation_ids.append(reference_map[marker])
    for url in _URL_RE.findall(text):
        clean = _clean_url(url)
        source_id = reference_map.get(clean)
        if source_id and source_id not in citation_ids:
            citation_ids.append(source_id)
    for marker, source_id in reference_map.items():
        if not marker or marker.startswith("http") or not source_id.startswith("SRC-"):
            continue
        if marker.isdigit() or len(marker) < 4:
            continue
        if marker.lower() in lower_text and source_id not in citation_ids:
            citation_ids.append(source_id)
    return citation_ids


def _quality_flags(source_records: list[dict], claim_records: list[dict]) -> list[str]:
    flags: list[str] = []
    if not source_records:
        flags.append("no_sources_found")
    if not claim_records:
        flags.append("no_candidate_claims_found")
    uncited = [claim for claim in claim_records if not claim["citation_ids"]]
    if uncited:
        flags.append(f"{len(uncited)}_claims_missing_citations")
    if len(source_records) < 5:
        flags.append("fewer_than_5_sources")
    return flags


def _section_for_text(value: str, sections: list[dict]) -> str | None:
    for section in sections:
        if value in section.get("text", ""):
            return section["section_id"]
    return None


def _clean_url(url: str) -> str:
    return url.rstrip(".,;:)]}")


def _source_aliases(url: str, label: str | None, reference_key: str | None) -> list[str]:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    aliases = [domain]
    if domain.startswith("www."):
        aliases.append(domain[4:])
    if label:
        aliases.append(label.strip())
    if reference_key:
        aliases.append(reference_key)
    return [alias for alias in aliases if alias]


def _looks_like_claim(text: str) -> bool:
    if text.endswith((".", "!", "?", ")", '"')):
        return True
    return len(text.split()) >= 8 and any(char.isdigit() for char in text)


def _strip_markdown(text: str) -> str:
    without_links = _INLINE_LINK_RE.sub(r"\1", text)
    without_refs = _REF_MARKER_RE.sub("", without_links)
    collapsed = re.sub(r"\s+", " ", without_refs).strip()
    return re.sub(r"\s+([.,;:!?])", r"\1", collapsed)
