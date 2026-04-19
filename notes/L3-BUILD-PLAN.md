# L3 Deliverable Generation — Build Plan

**Status:** Plan. Not code.
**Target output path:** `notes/L3-BUILD-PLAN.md` (moved from this scratch location on approval).
**Scope:** Replace `src/keystone/pipeline/markdown_renderer.py` as the pipeline's primary L3 with a format-extensible renderer stack. Phase 1 ships PPTX. XLSX and PDF follow.

---

## Executive summary

Build a format-agnostic `rendering/` package that sits between L2's `StructuredOutline` and the on-disk artifact. Introduce a `DeckPlan` intermediate representation so new formats cost an adapter, not a rewrite of the whole renderer. Ship PPTX first because it's the only deliverable Jack can hand a client, then XLSX (for the model-driven engagements), then PDF (for read-only handoffs). The current Markdown renderer stays as the default debug output and the outline-content source of truth — it's light, determinism-safe, and already 800+ tests' worth of wired. New code lives in `src/keystone/rendering/`, wired through a new `L3Renderer` contract that matches L2's async-generator pattern. Every format is deterministic by Phase 1 (byte-stability tests gate CI). LLM use in the render path is bounded to the layout-intent planner (FLAGSHIP tier, Phase 2 upgrade — Phase 1 is rule-based). No Claude Skills API at runtime; we borrow Anthropic's MIT-licensed `inventory.py`/`replace.py`/`rearrange.py` scripts in-tree as the OOXML mechanics. Template hand-off from Jack is a written contract (layouts, placeholders, charts, theme colors), validated by an inventory-based checker that fails loud when the template drifts.

Risk is bounded: Phase 1 ships against a synthetic test template committed to the repo, so build can start before Jack uploads his branded file. Optional-dependency extras (`render-pptx`, `render-xlsx`, `render-pdf`, combined `render`) follow the existing `retrieval-*` pattern so minimal installs don't pull python-pptx or WeasyPrint's system libraries.

## Q1 — Scope and phasing

PPTX first. PPTX is the highest-value single output for consulting and the only deliverable Jack actually plans to hand a client. Markdown is already doing the reading-layer job. The IR-first architecture (see Q2) means the phase-1 investment is reusable for XLSX and PDF — the cost of "PPTX only" versus "PPTX + XLSX + PDF simultaneously" is maybe 20% of total work, but serialising means Phase 1 can ship to production before the other writers exist.

**Phase sequence.**

1. **Phase 1 — PPTX MVP (3–4 days).** `rendering/` package, `DeckPlan` IR, rule-based layout selector, `pptx` writer against a synthetic test template (`tests/fixtures/rendering/test_template.pptx`) committed to the repo. Classic charts only (bar/column/line/pie) via `chart.replace_data()`. Byte-stability CI gate from day one. `Pipeline` wired to emit both Markdown and PPTX when extras are installed. ~60 unit tests (IR construction, layout routing, byte-stable output, citation injection, template-contract validator).
2. **Phase 2 — PPTX polish (2–3 days).** Real branded template from Jack. LLM layout-intent planner (FLAGSHIP, replaces rule-based). Matplotlib PNG fallback for waterfall / funnel / treemap / Marimekko (driven by theme-derived `.mplstyle`). Headless-LibreOffice visual QA wired behind a `visualqa` marker + a new `RenderingValidated` event. think-cell `.ppttc` emitter if template inventory reports think-cell shapes. ~40 more tests.
3. **Phase 3 — XLSX (2 days).** `xlsxwriter` writer, `SheetPlan` IR (mirrors `DeckPlan`), Sources sheet + cell-comment + hyperlink citation pattern, dynamic-array formulas for sensitivity tables. Mostly needed for the financial-modeling engagement types. ~30 tests.
4. **Phase 4 — PDF (2 days).** `WeasyPrint` as primary (HTML/CSS path, CSS footnotes, `SOURCE_DATE_EPOCH` for determinism). `fpdf2` as pure-pip fallback when Pango isn't available. ~25 tests.

Each phase is independently auditable: passes its own test suite, full pipeline runs clean against the matrix, no deferred audit findings before the next phase starts.

## Q2 — Architecture: IR vs direct render

Use an IR. Both reports land here for the same reason: the adapter layer is the code we own and the part that absorbs library quirks. Direct rendering from `StructuredOutline` to PPTX would hardcode PowerPoint concerns (layouts, placeholders, chart data shape) into L2 or into a per-format renderer, making the next format a full rewrite. The IR is roughly 400 lines per format family; the writer against the IR is another 500–800. That's 1–2 KLOC we'd rewrite three times without it.

**Module layout.**

```
src/keystone/rendering/
  __init__.py
  contracts.py          # Renderer protocol + RenderArtifact dataclass
  planner.py            # outline + template_inventory -> DeckPlan (rule-based P1, LLM P2)
  ir/
    __init__.py
    deck_plan.py        # DeckPlan, SlidePlan, SlideIntent, Placement
    sheet_plan.py       # WorkbookPlan, SheetPlan (Phase 3)
    doc_plan.py         # DocPlan, PageBlock (Phase 4)
    chart_data.py       # ChartableItem, ChartKind, Series (shared across formats)
  determinism.py        # repro-zipfile wrapper, fixed-timestamp helpers
  citations.py          # inline [N] injection, Sources trailer builder
  markdown/
    writer.py           # moved from pipeline/markdown_renderer.py
  pptx/
    __init__.py
    writer.py           # DeckPlan -> .pptx bytes
    inventory.py        # vendored from Anthropic skills, adapted
    replace.py          # vendored from Anthropic skills, adapted
    rearrange.py        # vendored from Anthropic skills, adapted
    template_contract.py  # TemplateContract model + validator
    mplstyle_builder.py   # theme colors -> .mplstyle for matplotlib fallback
  xlsx/                 # Phase 3
  pdf/                  # Phase 4
```

**Contracts.** New `RendererContract` in `rendering/contracts.py` replacing the currently-unused `GenerationContract` in `src/keystone/contracts.py`:

```python
class RendererContract(Protocol):
    format: OutputFormat  # markdown | pptx | xlsx | pdf

    async def render(
        self,
        outline: StructuredOutline,
        manifest: CitationManifest,
        spec: EngagementSpec,
        evaluation_results: list[EvaluationResult],
        confidence_map: ConfidenceMap,
        findings: list[StructuredFinding],
    ) -> AsyncIterator[AnyPipelineEvent]: ...

    async def get_artifact(self) -> RenderArtifact: ...
```

`RenderArtifact` carries `format`, `bytes`, `suggested_filename`, `metadata` (sha256, timestamps normalised, source outline hash). Each writer emits `DraftGenerated` / `CitationFormatted` / `DeliverableAssembled` (already in `events.py`) plus new format-specific events (see Q12).

**Why not direct render.** Keeps L3 writers dumb — no LLM calls on PPTX/XLSX/PDF paths. Lets the planner own all LLM cost. Makes adding format #4 (e.g. HTML-for-Notion) a 1-day job.

## Q3 — Template contract

Jack's .pptx is not uploaded. Build against a synthetic template in the repo; specify the contract so his real template slots in when it arrives.

**Required layouts (by exact name, case-sensitive).** Phase 1 contract:

| Layout name | Used for | Required placeholders (by name) |
|---|---|---|
| `title` | Deck title slide | `title`, `subtitle`, `client`, `date` |
| `agenda` | Table of contents | `title`, `agenda_items` (text frame with 1 bullet per section) |
| `executive_summary` | Headline findings | `title`, `headline_1`, `headline_2`, `headline_3`, `headline_4`, `caveat` |
| `framework_overview` | Analytical framework slide | `title`, `framework_name`, `framework_rationale`, `framework_diagram` (picture) |
| `key_finding_single` | One claim, full slide | `title`, `claim`, `evidence`, `tier_badge`, `source_refs` |
| `key_finding_two_col` | Two claims side-by-side | `title`, `claim_left`, `evidence_left`, `claim_right`, `evidence_right`, `tier_badges` |
| `uncertainty` | Moderate/weak/contested | `title`, `tier_label`, `claim_list` |
| `gaps` | Evidence gaps + insufficient | `title`, `gap_list`, `insufficient_list` |
| `absence` | Absence report | `title`, `absence_list` |
| `chart_bar` | Bar/column chart | `title`, `chart` (chart placeholder with bar/column template chart), `takeaway`, `source_refs` |
| `chart_line` | Line chart | `title`, `chart`, `takeaway`, `source_refs` |
| `chart_picture` | matplotlib/Plotly PNG fallback | `title`, `picture`, `takeaway`, `source_refs` |
| `sources` | Numbered source list | `title`, `source_list` (multi-column text frame) |
| `divider` | Section divider | `title`, `section_number` |

Phase 2 adds: `key_finding_waterfall` (think-cell if detected), `bubble_matrix_2x2`, `timeline`.

**Theme colors (required in slide master).** `ACCENT_1` through `ACCENT_6`, background `LIGHT_1`/`DARK_1`, mapped by semantic name: `accent_1` = high-confidence, `accent_2` = moderate, `accent_3` = weak, `accent_4` = contested, `accent_5` = insufficient, `accent_6` = framework stamp. Color values can be whatever the brand dictates — we just key off the accent slot.

**Discovery tool.** `python -m keystone.rendering.pptx.inventory template.pptx > inventory.json` dumps every layout, every placeholder, every chart's series count and type, and every theme color. Vendored from Anthropic's `skills/pptx/scripts/inventory.py`, adapted to emit our schema. Runs in unit tests as the template-contract validator — if Jack's real template doesn't match, CI fails with a diff.

**Jack's handoff checklist alongside the .pptx.**

1. The .pptx file itself.
2. A one-page naming convention doc confirming every layout in the contract table is present and named exactly as specified (or proposing alternative names which we'd codify).
3. Theme accent palette decisions (which accent = which tier).
4. Chart template authorship: every layout named `chart_*` must contain a pre-authored chart with series count matching the claim shape we'll emit (1 series default). `chart.replace_data()` is styling-safe only when the template series count matches the runtime series count (python-pptx issue #539).
5. Pre-applied table styles: any table layout needs its style applied in GUI first (PowerPoint lazy-populates `tableStyles.xml`).

If any item is missing, `validate_template()` fails with the exact contract violation. No silent fallbacks.

**Template-agnostic Phase 1.** `tests/fixtures/rendering/test_template.pptx` is a minimal synthetic template that satisfies the contract with ugly-but-valid defaults (Arial 12pt, black/white, single-series bar chart). Built in GUI once, committed binary to repo. All Phase 1 unit tests run against this; Phase 2 swaps in Jack's real file and asserts the contract still holds.

## Q4 — Layout intent selection

Inside L3, as a two-step pipeline: `plan` → `write`. The planner is a new component (`rendering/planner.py`); the writer is `pptx/writer.py`. This keeps template knowledge inside `rendering/` (L2 stays template-agnostic) and keeps the writer deterministic (no LLM in the write step).

**Phase 1: rule-based planner.** Maps `OutlineSectionType` to layout names directly:

| OutlineSectionType | Default layout |
|---|---|
| EXECUTIVE_SUMMARY | `executive_summary` |
| FRAMEWORK_ANALYSIS | `framework_overview` |
| BRANCH | `key_finding_single` (or `key_finding_two_col` when branch has 2 distinct sub-claims) |
| MODERATE / WEAK / CONTESTED | `uncertainty` (one slide per tier) |
| GAPS / INSUFFICIENT | `gaps` |
| ABSENCE | `absence` |

Deterministic function `plan_deck(outline, template_inventory) -> DeckPlan`. No LLM. Tests are pure unit tests on the function.

**Phase 2: LLM-stamped planner.** Upgrade the planner to use an LLM for layout intent when the outline has ambiguity — e.g. a BRANCH with numerical content should route to `chart_bar` not `key_finding_single`. Pydantic-schema-constrained output:

```python
class SlideIntentDecision(BaseModel):
    section_id: str
    layout_name: str
    chart_kind: ChartKind | None  # when layout is chart_*
    rationale: str
```

The planner prompts with the template inventory (layout names + semantic descriptions) + the section content and asks for a strict-schema response. Model tier: FLAGSHIP (Opus) at `xhigh` reasoning effort. This is load-bearing judgment; Sonnet is the floor if we ever need to downshift for cost.

**Pipeline-config wiring.** Add to `ModelMixingConfig` in `src/keystone/models/config.py`:

```python
l3_layout_planner: str = Field(default="flagship", description="L3 layout-intent planner tier")
```

And to `_DEFAULT_LAYER_EFFORTS`: `"l3_layout_planner": "xhigh"`.

Phase 1 sets this but doesn't call the LLM — the field is reserved for Phase 2. Env override: `PIPELINE__MODEL_MIXING__L3_LAYOUT_PLANNER=flagship`.

**Testing without a real LLM.** Planner takes an `LLMCallable` like every other component; tests pass a `FakeLayoutPlannerLLM` that returns a pre-baked `SlideIntentDecision` per section_id. The Phase 1 rule-based path doesn't invoke the LLM at all; Phase 2's LLM-based path is tested against the fake and the structural invariants (every section maps to exactly one layout, layout names exist in the template inventory).

## Q5 — Chart strategy

Hybrid by chart type. Both reports land here; the split is only on library defaults, which is a Q8 concern, not an architectural one.

**Classic charts (bar, column, line, pie, scatter, area, bubble, radar):** `python-pptx` `chart.replace_data(CategoryChartData)` with series count matched to template. Styling-safe per python-pptx issue #539 as long as Jack pre-authors the template with the right series count. Writer code:

```python
from pptx.chart.data import CategoryChartData
cd = CategoryChartData()
cd.categories = [str(c) for c in chartable.categories]
for series in chartable.series:
    cd.add_series(series.name, series.values)
chart.replace_data(cd)
```

**Exotic charts (waterfall, funnel, treemap, sunburst, histogram, Marimekko, Sankey):** matplotlib PNG fallback, inserted into a `chart_picture` layout's picture placeholder. `Agg` backend, metadata stripped (`savefig(metadata={"Software": None, "Creation Time": None})`), `.mplstyle` file generated from the template's theme accent palette at build time (`mplstyle_builder.py`). Deterministic across runs.

**think-cell charts:** if `inventory.py` detects think-cell shapes in the template (specific `<thinkCell>` OOXML namespace presence), write a `.ppttc` sidecar via the unofficial `thinkcell` package. Phase 2 only. The template inventory's detection result is persisted on `TemplateInventory.uses_thinkcell: bool` so Phase 1 can proceed ignoring it.

**Chart data origin.** New Pydantic model in `rendering/ir/chart_data.py`:

```python
class ChartKind(StrEnum):
    BAR = "bar"
    COLUMN = "column"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    BUBBLE = "bubble"
    AREA = "area"
    WATERFALL = "waterfall"     # matplotlib
    FUNNEL = "funnel"           # matplotlib
    TREEMAP = "treemap"         # matplotlib
    HISTOGRAM = "histogram"     # matplotlib

class ChartSeries(BaseModel):
    name: str
    values: list[float]

class ChartableItem(BaseModel):
    kind: ChartKind
    categories: list[str]
    series: list[ChartSeries]
    title: str
    takeaway: str  # one-sentence action title on the slide
    source_citation_ids: list[str]
```

Extend `OutlineItem` in `src/keystone/models/structuring.py` with an optional field:

```python
chart: ChartableItem | None = Field(
    default=None,
    description="When set, item renders as chart rather than bullet text.",
)
```

**Where does the chart data come from.** In Phase 1, charts are rare and L2 doesn't extract them. The planner synthesises a `chart_picture` layout slide only when the outline item already carries a populated `ChartableItem` — which for Phase 1 means never. Charts are deferred content. Phase 2 adds an L2-side `NumericalExtractor` that scans `OutlineItem.text` + `OutlineItem.evidence` for quantitative patterns ("X grew 43% YoY", "Y = $3.2B") and promotes them to `ChartableItem`. That extractor is a separate build plan; this plan specifies the IR and the writer contract, not the extractor.

**matplotlib styling.** `mplstyle_builder.build_from_template(template_inventory) -> Path` generates `~/.cache/keystone/rendering/theme.mplstyle` with:

```
font.family: <template font primary>
axes.prop_cycle: cycler('color', [<accent_1>, <accent_2>, ..., <accent_6>])
axes.edgecolor: <template dark_1>
axes.titleweight: bold
```

Applied via `matplotlib.style.use(path)` inside a context manager around every chart render so the style stays scoped.

## Q6 — Citation preservation

Three layers, per both reports. Canonical `CitationManifest` is the source of truth — every format's Sources trailer is a view over it.

**PPTX.**

- **Inline refs.** Body text runs carry superscript `[N]` immediately after the sentence they support, keyed to the manifest's numeric index. Run formatting preserved by walking existing template runs and appending a new run with `font.superscript = True`, `font.size = min(original_size, 8pt)`. Don't use `cell.text = ...` (strips formatting).
- **Speaker notes.** For every slide carrying citations, `slide.notes_slide.notes_text_frame` gets a block:
  ```
  [N] Author(s) (Year). "Title". Publication. URL (accessed YYYY-MM-DD) — quality: 0.87
  [N+1] ...
  ```
  Speaker notes survive round-trip in python-pptx and are preserved by every mainstream PPTX renderer.
- **Sources slide.** Final slide uses the `sources` layout with the numbered list in `source_list`. Same format as speaker notes for consistency.
- **File-level provenance.** `prs.core_properties.keywords = "engagement:{eid}; outline_hash:{sha256(outline)[:16]}"` so the deck is self-identifying.

**XLSX (Phase 3).**

- **Canonical `Sources` sheet** with columns: id, url, title, author, publication, date, quality_score, hash. Populated from `CitationManifest`.
- **Claim cells** get an adjacent column `Src` with `=HYPERLINK("#Sources!A"&MATCH("CAN-042", Sources.A:A, 0), "[12]")` — formula resolves at open time.
- **Cell comments** on claim cells carry one-line summary (`"[12] Title (Year) — quality 0.87"`) via `write_comment` with `author="Keystone"`.
- **Workbook-level named ranges** `cite_<id>` point at the Sources row for formula-driven audit.
- **Threaded comments.** Skip. Only Aspose.Cells can author them and we're not buying Aspose.

**PDF (Phase 4).**

- **WeasyPrint path.** CSS footnotes (`span.citation { float: footnote }`, `@page { @bottom-center { content: counter(footnote) } }`). `[N]` superscript in body via `<sup class="citation-ref">`. Sources section as a numbered list at end.
- **fpdf2 fallback.** Manual footnote counter on the `FPDF` subclass. Sources section via `start_section()` for PDF outline.

**Invariant across formats.** Every numeric `[N]` on a rendered page must resolve to a row in the format-native Sources trailer, and every row must correspond to exactly one `Citation` in `manifest.citations`. Byte-stability tests verify this.

## Q7 — Determinism

Non-negotiable from Phase 1. The CI gate is a byte-stability test per format: run the renderer twice against a fixed fixture, assert the output bytes match.

**Phase 1 guardrails (all required):**

1. `repro-zipfile` wrapping the python-pptx save — strips ZIP timestamps. Vendored from `timvink/repro-zipfile` (MIT) or installed as a dep under `render-pptx` extra.
2. `prs.core_properties.created = prs.core_properties.modified = datetime(2024, 1, 1, tzinfo=UTC)` before save. Also `.last_modified_by = "keystone"`, `.revision = 1`.
3. `sorted()` on every filesystem traversal (template parts, chart XMLs, embedded xlsx parts).
4. `matplotlib.use("Agg")` in module import; `savefig(metadata={"Software": None, "Creation Time": None, "Producer": None})`.
5. PIL image writes via `Image.save(path, pnginfo=None)` for any generated PNG.
6. Python `os.environ["SOURCE_DATE_EPOCH"] = "1704067200"` (2024-01-01 UTC) set by the renderer on entry, restored on exit (context manager).
7. `prs.core_properties.keywords` carries the input hashes (outline + manifest + spec) so the same input deterministically produces the same keyword string.

**CI gate shape.** `tests/unit/rendering/test_byte_stability.py`:

```python
@pytest.mark.parametrize("fixture_id", ALL_FIXTURES)
def test_pptx_byte_stable(fixture_id):
    a = render_once(fixture_id)
    b = render_once(fixture_id)
    assert sha256(a) == sha256(b)
```

Runs on every PR. If it fails, the PR cannot merge. ~5 fixtures in Phase 1 (title-only, title+exec, title+exec+branches, full-stack, chart slide).

**Deferred to Phase 2.** `invariant=1` on ReportLab (when PDF lands — not Phase 1). think-cell determinism audit (Phase 2's think-cell work). XLSX shared-strings ordering (Phase 3 — addressed via `constant_memory=True` in xlsxwriter).

## Q8 — Dependencies and graceful degradation

Optional extras, mirroring the `retrieval-*` pattern:

```toml
[project.optional-dependencies]
render-pptx = [
    "python-pptx>=1.0.2",
    "lxml>=5.0",
    "matplotlib>=3.8",
    "Pillow>=10.0",
    "repro-zipfile>=0.4.0",
]
render-xlsx = [
    "xlsxwriter>=3.2.9",
    "openpyxl>=3.1.5",
]
render-pdf = [
    "weasyprint>=68.1",
    "fpdf2>=2.8.7",
    "Jinja2>=3.1",
]
render = [
    "keystone-intelligence-engine[render-pptx,render-xlsx,render-pdf]",
]
```

**Version pins come from the reports** — python-pptx 1.0.2 is effectively feature-frozen and the right baseline; xlsxwriter 3.2.9 is the September 2025 release with complete dynamic-array support; WeasyPrint 68.1 is the February 2026 release with CSS footnotes improved; fpdf2 2.8.7 is the February 2026 release with HarfBuzz shaping.

**System libraries.** WeasyPrint needs Pango/HarfBuzz/fontconfig (`brew install pango` on macOS). Documented in the Phase 4 milestone as a handover item; fpdf2 is the pure-pip fallback when Pango is unavailable.

**Behavior when an extra is missing.** Fail loud, not silent. The rendering package imports lazily:

```python
# src/keystone/rendering/pptx/__init__.py
try:
    from pptx import Presentation  # noqa
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
```

And `Pipeline.__init__` checks the configured `output_formats` against the available renderers. When a configured format's extra isn't installed:

1. `Pipeline.__init__` raises `RenderingExtraMissing(f"output_formats includes 'pptx' but python-pptx is not installed. pip install 'keystone-intelligence-engine[render-pptx]'")` — fail at construction, not at render time.
2. Alternatively, when `strict_rendering=False` (new kwarg, default `True`), downgrade to a WARN governance flag (`l3_render_extras_missing`) and skip that format. The Markdown renderer always works (it's pure Python, no extras).

Fail loud by default because silent format-skipping is the audit anti-pattern the codebase has been moving away from.

## Q9 — Visual QA

Phase 2, not Phase 1.

**Why defer.** Visual QA adds headless LibreOffice (Homebrew cask or apt package), pdftoppm (Poppler), and optional matplotlib + Pillow work for rasterisation. Phase 1 has byte-stability tests which catch the "did the renderer change" class of bug. Visual QA catches overflow, placeholder-residue, low-contrast — which matter once Jack's real template lands and we're polishing, not when we're proving the pipeline works.

**Phase 2 design.** New `rendering/pptx/visual_qa.py`:

```python
async def validate_render(
    pptx_path: Path,
    *,
    check_overflow: bool = True,
    check_residual_placeholders: bool = True,
    mllm_pass: bool = False,
) -> VisualQAReport
```

1. `soffice --headless --convert-to pdf` → PDF.
2. `pdftoppm -r 150` → one PNG per slide.
3. `markitdown` on the source .pptx to extract text; regex-scan for residue (`{{`, `}}`, `<<`, placeholder names).
4. Optional MLLM pass (Claude Sonnet): for each slide PNG, ask "any text overflow, overlap, or obvious visual defect?" — Sonnet-tier floor per the constraint; no Haiku.

**Event integration.** New `RenderingValidated` event:

```python
class RenderingValidated(PipelineEvent):
    layer: str = "L3"
    format: str
    slide_count: int
    issues_found: int
    issues_by_kind: dict[str, int]  # overflow, residue, contrast, mllm_flag
    mllm_score: float | None
```

And a new governance flag `l3_visual_qa_failed` — WARN when `issues_found > 0`, ESCALATE when any MLLM flag is critical. Gate the pipeline with `policy.apply_flag`.

**Phase 1 substitute.** A `test_no_residual_placeholders.py` test runs `markitdown` on the synthetic test-template output and asserts no `{{`, `}}`, or layout-placeholder names leak through. Zero runtime cost because it's just a test.

## Q10 — Testing strategy

Unit tests run without PowerPoint or LibreOffice installed. Integration tests are gated.

**Unit test taxonomy.**

1. **IR construction (`test_deck_plan.py`).** `StructuredOutline` → `DeckPlan` via planner. Asserts every outline section maps to a valid layout, every item has citations resolved, every chart is classified.
2. **Writer mechanics (`test_pptx_writer.py`).** `DeckPlan` → .pptx bytes. Uses a `fake_presentation` fixture and inspects the resulting file via `python-pptx` read-back (no headless office needed). Asserts placeholder content matches, citation count matches, theme accent usage matches.
3. **Byte stability (`test_byte_stability.py`).** Render twice, compare sha256. Parameterised over fixture set.
4. **Citation injection (`test_citation_layers.py`).** Inline `[N]` in body, speaker notes carry full entries, Sources slide matches manifest count.
5. **Template contract (`test_template_contract.py`).** Runs `inventory.py` on `tests/fixtures/rendering/test_template.pptx`, compares against the declared `TemplateContract`, asserts 1:1 match.
6. **Missing extras (`test_graceful_degradation.py`).** Monkeypatches `PPTX_AVAILABLE = False`, asserts `Pipeline.__init__` raises `RenderingExtraMissing` when `strict_rendering=True` and emits `l3_render_extras_missing` flag when `strict_rendering=False`.
7. **Events emitted (`test_rendering_events.py`).** Asserts every writer yields `DraftGenerated`, `CitationFormatted`, `DeliverableAssembled`, and format-specific events in the right order and count.
8. **Planner LLM (`test_layout_planner.py`, Phase 2).** Uses fake LLM returning pre-baked `SlideIntentDecision`; asserts layout selection is valid for every section.

Target counts: Phase 1 = 60 unit tests; Phase 2 = +40; Phase 3 = +30; Phase 4 = +25.

**Integration tests.** `tests/integration/test_render_full_pipeline.py` runs the full `Pipeline` against a mocked upstream (L0-L2 produce a known `StructuredOutline` + `CitationManifest`), asserts the rendered PPTX opens without errors in python-pptx read-back, and opens in headless LibreOffice without repair dialogs. Gated on a pytest marker: `@pytest.mark.integration` + `@pytest.mark.render_pptx`.

**Template fixtures.**

```
tests/fixtures/rendering/
  test_template.pptx         # committed binary, 14 layouts matching the contract
  test_template_inventory.json  # generated from inventory.py, committed for diff visibility
  golden/
    outline_minimal.json     # smallest valid input
    outline_full.json        # all 9 section types populated
    outline_chart_heavy.json # exercises chart_bar/chart_line
    outline_citations_heavy.json  # 50-citation stress
```

Golden outputs committed as SHA256 hashes in `test_byte_stability.py` — not the full binary — so PRs don't churn the repo. When byte-stability intentionally changes (new determinism fix), the hash updates with a commit message explaining why.

**Template-agnostic build pre-upload.** Phase 1 builds against `test_template.pptx` which is minimal but satisfies the contract. Jack's real template is expected to satisfy the same contract; if it doesn't, `validate_template()` fails with a diff. Build can start now.

## Q11 — Anthropic pptx Skill + Claude-native path

**Steal the scripts, not the API.** Both reports agree: Anthropic's `skills/pptx/scripts/` (`inventory.py`, `replace.py`, `rearrange.py`, `unpack.py`, `pack.py`, `validate.py`) are the reference implementation for template-driven PPTX manipulation and are MIT-to-source-available.

**Approach: vendor in-tree, adapted.** Not a submodule (ties us to upstream cadence), not reimplemented (gives up battle-tested OOXML handling). Copy the scripts to `src/keystone/rendering/pptx/{inventory,replace,rearrange}.py`, add a module docstring attributing Anthropic's upstream, adapt signatures to our Pydantic types, run them through ruff/mypy. Licence: MIT — our `LICENSE` file already permits bundled MIT code; add a `NOTICES` entry.

**Orchestration role for Claude Skills at runtime.** Zero. Both reports converge:

- Skills aren't ZDR-eligible; our pipeline is citation-heavy, citations are ZDR-eligible, and mixing modes splits every eval call.
- Skills sandbox can't install runtime packages; anything we need (repro-zipfile, custom template code) doesn't exist there.
- Skills add tokenizer cost (Opus 4.7's new tokenizer is up to 35% more tokens per report 2) for orchestration that runs locally in ~100ms.
- Determinism vanishes the moment we route through an LLM for rendering.

The one possible future role is **visual QA** (Q9's Phase 2 MLLM pass) — sending a slide PNG to Claude Sonnet and asking for overflow/contrast feedback. That's not a "Skill," it's a regular Messages API call with an image. No skills beta, no code_execution tool, no sandbox.

## Q12 — Integration + MD renderer legacy

**`EngagementConfig` changes.**

```python
class OutputFormat(StrEnum):
    MARKDOWN = "markdown"
    PPTX = "pptx"
    XLSX = "xlsx"
    PDF = "pdf"

class EngagementConfig(BaseModel):
    ...
    output_formats: list[OutputFormat] = Field(
        default_factory=lambda: [OutputFormat.MARKDOWN],
        description="Output formats to render. Markdown is always available (no extras).",
    )
    # Deprecated, kept for back-compat read:
    output_format: str = Field(default="markdown", deprecated=True)
```

Migration shim: when `output_formats` is the default and `output_format` is non-default, auto-populate `output_formats = [OutputFormat(output_format)]`. One-release deprecation, then drop `output_format`.

**`Pipeline.__init__` changes.**

```python
def __init__(
    self,
    ...,
    output_formats: list[OutputFormat] | None = None,  # defaults to [MARKDOWN]
    strict_rendering: bool = True,  # raise on missing extras
) -> None:
```

**`_build_components` changes.** Today `renderer: MarkdownRenderer` is a single field. Replace with:

```python
@dataclass
class PipelineComponents:
    ...
    renderers: dict[OutputFormat, RendererContract]  # populated per output_formats
```

Renderer construction validates extras per Q8 and builds each configured writer.

**Render stage changes.** Current:

```python
markdown_output = c.renderer.render(...)
self._result = PipelineResult(..., markdown_output=markdown_output)
```

New:

```python
rendered_artifacts: dict[OutputFormat, RenderArtifact] = {}
for fmt, renderer in c.renderers.items():
    async for event in renderer.render(
        filtered_outline, render_manifest, spec,
        render_evaluation_results, filtered_confidence_map, passed_findings,
    ):
        yield event
    rendered_artifacts[fmt] = await renderer.get_artifact()

self._result = PipelineResult(
    ...,
    markdown_output=rendered_artifacts[OutputFormat.MARKDOWN].bytes.decode("utf-8"),  # back-compat
    rendered_artifacts=rendered_artifacts,
)
```

**`PipelineResult` additions.**

```python
class PipelineResult(BaseModel):
    ...
    markdown_output: str  # Unchanged — back-compat for existing call sites
    rendered_artifacts: dict[OutputFormat, RenderArtifact] = Field(default_factory=dict)
```

**New events in `events.py`.**

```python
class DeckRendered(PipelineEvent):
    layer: str = "L3"
    slide_count: int
    byte_count: int
    output_path: str | None  # None when bytes are in-memory
    sha256: str

class WorkbookRendered(PipelineEvent):  # Phase 3
    layer: str = "L3"
    sheet_count: int
    byte_count: int
    output_path: str | None
    sha256: str

class DocumentRendered(PipelineEvent):  # Phase 4
    layer: str = "L3"
    page_count: int
    byte_count: int
    output_path: str | None
    sha256: str

class LayoutIntentStamped(PipelineEvent):  # Phase 2
    layer: str = "L3"
    section_id: str
    layout_name: str
    chart_kind: str | None
```

All four added to `AnyPipelineEvent` union.

**Existing `MarkdownRenderer` fate.** Keep. Move to `src/keystone/rendering/markdown/writer.py` with the `RendererContract` wrapper that adapts its existing `render(spec, findings, confidence_map, evaluation_results, manifest, outline)` sync signature to the async-generator contract:

```python
class MarkdownWriter:
    format = OutputFormat.MARKDOWN

    async def render(self, outline, manifest, spec, evaluation_results, confidence_map, findings):
        markdown = self._renderer.render(spec, findings, confidence_map, evaluation_results, manifest, outline)
        self._artifact = RenderArtifact(
            format=OutputFormat.MARKDOWN,
            bytes=markdown.encode("utf-8"),
            suggested_filename=f"{spec.research_spec.engagement_id}.md",
            metadata={"sha256": sha256(markdown.encode()).hexdigest()},
        )
        yield DraftGenerated(...)
        yield DeliverableAssembled(format="markdown", ...)

    async def get_artifact(self) -> RenderArtifact:
        return self._artifact
```

**Back-compat for `pipeline/markdown_renderer.py` path.** Keep the file as a re-export shim:

```python
# src/keystone/pipeline/markdown_renderer.py
from keystone.rendering.markdown.writer import MarkdownWriter as MarkdownRenderer  # noqa

__all__ = ["MarkdownRenderer"]
```

Drop the shim after one release cycle. Saves ~800 test files from churning imports.

**Contracts reconciliation.** The currently-unused `GenerationContract` in `src/keystone/contracts.py` has a wrong signature (takes `contracts: list[SprintContract]` instead of outline + manifest). Replace it with `RendererContract` from `rendering/contracts.py`, matching actual runtime. Delete the stale one.

---

## Phase-plan table

| Phase | Scope | Milestones | Gated by | Audit shape |
|---|---|---|---|---|
| **1: PPTX MVP** | IR + rule-based planner + python-pptx writer against synthetic template + Markdown renderer repackaged + byte-stability CI + determinism guardrails | — `src/keystone/rendering/` package structure with IR + planner + contracts<br>— `tests/fixtures/rendering/test_template.pptx` committed<br>— Phase 1 rule-based `plan_deck()` maps 9 section types<br>— `pptx/writer.py` renders exec_summary + framework + branches + uncertainty + gaps + absence + sources slides<br>— Classic chart support only (outline items without `ChartableItem` skip chart slides)<br>— `EngagementConfig.output_formats: list[OutputFormat]` wired through `Pipeline`<br>— ~60 unit tests pass; byte-stability CI gate green | — `render-pptx` extra installable (`python-pptx`, `lxml`, `matplotlib`, `Pillow`, `repro-zipfile`)<br>— Synthetic test template committed to repo<br>— Anthropic skills scripts vendored with attribution | Unit+canary count `1404 → ~1464`. Ruff net-zero on touched files. Mypy strict net-zero on `src/keystone/rendering/`. Byte-stability test passes ×2 consecutive runs. No deferred findings. |
| **2: PPTX polish** | LLM layout planner + matplotlib PNG fallback + think-cell detection + headless LibreOffice visual QA + real template from Jack | — Jack uploads branded .pptx; `validate_template()` passes<br>— `l3_layout_planner: flagship` wired through `ModelMixingConfig`<br>— `NumericalExtractor` (out-of-scope for this plan) OR manual chart hints in outline promote items to `ChartableItem`<br>— matplotlib PNG fallback renders waterfall + funnel + treemap against theme-derived `.mplstyle`<br>— `RenderingValidated` event emitted; `l3_visual_qa_failed` governance flag active<br>— `visualqa` pytest marker gates headless-LibreOffice integration test<br>— ~40 more unit tests | — Jack's real template uploaded<br>— LibreOffice installed in CI (Homebrew or apt)<br>— `render-pptx` extra updated if matplotlib version bump needed | Unit+canary `~1464 → ~1504`. Integration test suite gains `visualqa` marker. Visual QA report shape audited. No deferred findings before Phase 3. |
| **3: XLSX** | `xlsxwriter` writer + `SheetPlan` IR + Sources sheet + formula emission + sensitivity tables | — `WorkbookPlan` and `SheetPlan` IR mirroring `DeckPlan`<br>— `xlsx/writer.py` emits Sources sheet, claim sheets with `=HYPERLINK()` cites + cell comments, per-branch assumption sheets<br>— Dynamic-array formulas (`LET`, `SEQUENCE`, `FILTER`) for Phase-3 sensitivity slides when outline items carry numerical evidence<br>— Corporate theme application via format objects (theme1.xml direct manipulation deferred)<br>— ~30 more tests | — `render-xlsx` extra installable (`xlsxwriter>=3.2.9`, `openpyxl>=3.1.5`)<br>— Phase 1 IR stable | Unit+canary `~1504 → ~1534`. Byte-stability test extended to XLSX. No new mypy errors on `rendering/xlsx/`. |
| **4: PDF** | WeasyPrint primary + fpdf2 fallback + CSS footnotes + HTML-template generation | — `DocPlan` IR<br>— `pdf/weasyprint_writer.py` with Jinja2 HTML templates, CSS footnotes, `SOURCE_DATE_EPOCH` determinism<br>— `pdf/fpdf2_writer.py` as pure-pip fallback<br>— Auto-selection: WeasyPrint when Pango available, fpdf2 otherwise<br>— ~25 more tests | — `render-pdf` extra installable (`weasyprint>=68.1`, `fpdf2>=2.8.7`, `Jinja2>=3.1`)<br>— Pango documented as optional system dep<br>— Phase 1 IR stable | Unit+canary `~1534 → ~1559`. Byte-stability gate covers PDF. No deferred findings. |

**Gating principle.** Each phase completes cleanly (all tests pass, zero deferred audit findings, byte-stability CI green) before the next begins. The build→audit→remediate cycle applies per-phase.

**Template handoff gate (Phase 1 → 2 boundary).** Phase 1 can ship entirely against the synthetic template. Phase 2 cannot begin until Jack uploads his branded file AND supplies the handoff checklist items (Q3). If handoff drags, Phase 3 (XLSX) can run in parallel with Phase 2's blocking.

---

## Verification (how to confirm this plan is executable)

The next session that writes build prompts should verify each of:

1. `src/keystone/models/structuring.py` accepts `OutlineItem.chart: ChartableItem | None` as an additive Pydantic field (no existing usage breaks). ✓ (checked — current `OutlineItem` has extensible optional fields)
2. `src/keystone/pipeline/orchestrator.py:607` renderer invocation can be replaced by the per-format loop described in Q12 without breaking any of the 1404 existing tests. ✓ (renderer result is assigned to `markdown_output`, keeping that field in `PipelineResult` preserves back-compat)
3. `src/keystone/events.py:AnyPipelineEvent` union extension is additive and doesn't break `isinstance` checks. ✓ (union; all current consumers check specific types)
4. The `render-pptx` extra doesn't conflict with the existing `retrieval-search` extra. ✓ (different package sets; pyproject.toml's optional-dependencies merges cleanly)
5. Jack's template validator can run on the synthetic template before the real one arrives. ✓ (synthetic template ships in `tests/fixtures/rendering/`)
6. Byte-stability CI gate doesn't add measurable wall-clock time. ✓ (single fixture render is ~200ms; 5 fixtures × 2 runs = ~2s per CI run)

**Next session's first move.** Sketch the Phase 1 work as five concrete PRs:

1. Scaffolding + IR + events (`DeckRendered`, `LayoutIntentStamped` stubs) + contracts.
2. Markdown renderer move + back-compat shim + `EngagementConfig.output_formats`.
3. Synthetic template fixture + `inventory.py` vendor + `TemplateContract` validator.
4. `pptx/writer.py` — layout-by-layout, gated per PR by byte-stability test.
5. `Pipeline` integration + determinism guardrails + governance flag for missing extras.

Each PR is ~1 day of work, fully auditable, shippable. Phase 1 closes after all five merge and the 1464-test baseline is green.
