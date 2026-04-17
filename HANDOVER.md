# Handover

Last updated: 2026-04-17
Session: Lane E build (article/PDF parse + evidence normalization)

## What Changed

- Built Lane E end-to-end under `src/keystone/retrieval/` (6 source files) and `tests/unit/retrieval/` (4 test files + fixtures).
- 82 new unit tests, all passing. No regressions: full suite 882/882 passes in ~7s.
- `ruff check` and `mypy strict` are clean for the retrieval module (pre-existing errors elsewhere untouched).

## Lane E Components

| File | Role |
|---|---|
| `parse_models.py` | All Pydantic v2 models: `SourceFamily`, `CoverageStatus`, `PassageKind`, `ParseConfidenceTier`, `ParserIdentity`, `Coverage`, `Locator`, `ParseConfidence`, `ParseWarning`, `ParsedPassage`, `ParsedDocument`, `FetchedArtifact`, `EvidencePrepRecord`. Helpers: `tier_for_score`, `confidence`. |
| `artifact_loader.py` | `ArtifactLoader(root)` loads `<root>/<artifact_id>.json` into `FetchedArtifact`. Raises `ArtifactNotFoundError` / `ArtifactLoadError`. `iter_all()` skips non-json, raises on malformed. |
| `article_parser.py` | `ArticleParser` → `ParsedDocument`. Stdlib `html.parser.HTMLParser`. Parser identity `keystone.article.v1`. Maintains `_section_stack` (heading chain), `_block_stack` (live blocks), `_tag_stack` (tag balance, emits `HTML_TAG_MISMATCH`). Skips script/style/noscript/template/svg. Scoring: `LOW_TEXT_VOLUME` (<40 chars → cap 0.5), `LOW_TEXT_TO_MARKUP_RATIO` (<2% → 0.6), `HTML_MALFORMED` (0.55), `UTF8_DECODE_LOSSY` (0.6), `UTF8_DECODE_FALLBACK` (0.85). |
| `pdf_parser.py` | `PDFParser` + pluggable `PDFTextBackend` Protocol + `BasicPDFTextBackend` fallback. Parser identity `keystone.pdf.v1`. Pre-extracted text path splits on `\f` (form feed). Binary path: `_scan_indirect_objects`, `_find_page_objects` (walks /Pages/Kids), `_decode_stream` (FlateDecode), `_extract_text_from_stream` (Tj/TJ/'/"/hex/octal). Emits `ENCRYPTED`, `NOT_A_PDF`, `EMPTY_BYTES`, `BASE64_DECODE_FAILED`, `EMPTY_PDF`, `EMPTY_PAGE`, `PARTIAL_PAGE_COVERAGE`, `UNKNOWN_FILTER`, `FLATE_DECOMPRESS_FAILED`, `SCANNED_IMAGE_PAGE`. |
| `evidence_normalizer.py` | `EvidenceNormalizer.normalize(artifact, parsed) → list[EvidencePrepRecord]`. `record_id = "ev:" + passage_id`. Falls back to `artifact.url` when `canonical_url` missing. Raises `ValueError` on artifact_id mismatch. |
| `__init__.py` | Re-exports all public symbols. |

## Design Choices

- **Stdlib-only parsing.** No bs4 / pypdf / pdfminer / docling installed in venv; keeps Lane E dependency-free. Pluggable `PDFTextBackend` Protocol lets production swap in a richer backend without changing the parser.
- **Never fabricate text.** Every passage's chars come from the input. Malformed input → explicit `ParseWarning` + degraded confidence, never silent success and never an exception that fails a batch.
- **Provenance preserved end-to-end.** `EvidencePrepRecord` carries `artifact_id`, `canonical_url`, `content_hash`, `coverage`, `source_family`, `parser identity`, `locator`, `parse_confidence`, and `fetched_at`.
- **Per-page + document-level confidence** on PDFs so one bad page doesn't poison the doc.
- **FetchedArtifact uses `extra="allow"`** to preserve any Lane H audit fields we haven't modeled.

## Key Commands

```bash
source .venv/bin/activate
pytest tests/unit/retrieval/ -q                  # 82 pass in 0.05s
pytest tests/unit/ -q                            # 882 pass in ~7s
ruff check src/keystone/retrieval/ tests/unit/retrieval/
mypy src/keystone/retrieval/                     # clean
```

## Gotchas Encountered

- Python 3.14.3 in `.venv` even though `pyproject.toml` pins 3.11+. Works fine but keep in mind.
- Lane H is **not** in this branch (merge-base predates commit `93a5ca8`). `FetchedArtifact` is Lane E's inferred contract for Lane H's output; any changes to Lane H's actual output schema must keep these fields valid.
- Pre-existing ruff errors (500+) and mypy errors (129) live in other modules. Not Lane E's scope.

## Next Steps

- Wire Lane E into the pipeline: load fetched artifacts, parse, normalize, hand off to research agents.
- Consider if the article parser should emit `data-` attribute extraction for structured data (currently ignored).
- If richer PDF extraction is needed, implement a `PDFTextBackend` wrapping `pdfminer.six` or `pypdf`.
- Stale integration test `test_evaluator_live.py` (pre-existing) still needs fixing.

## What Did Not Change

- No modifications to pipeline / research / deliberation / evaluator / renderer.
- No new dependencies added.
- Lane H code untouched (still not in this branch's history).
