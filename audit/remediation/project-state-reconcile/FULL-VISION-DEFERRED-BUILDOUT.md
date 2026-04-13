# Full Vision Deferred Buildout

## Rule

Everything in this file belongs to the intended fuller product beyond the current MVP spine.

- Most items below are `REQUIRED_FOR_FULL_VERSION`.
- Many are also `DEFERRED_BY_POLICY` right now because the control plane hard-stops post-Wave-4B capability expansion until a later setup artifact exists.

## Retrieval and full-document analysis

### Production retrieval stack

- Current base: Exa/Brave snippet search is real; tool registry entries exist for broader sources; the richer retrieval stack is not in committed runtime.
- Full-version buildout:
  `pgvector` or equivalent vector store,
  embeddings,
  keyword + vector hybrid retrieval,
  reranking,
  document parsing,
  source federation across public, internal, and historical corpora.
- Why this is full-version work:
  it is explicitly part of the long-term `#3a` design,
  but current runtime and policy do not support claiming it as finished now.

### Governed full-document / filing / article / PDF fetching

- Current base: deep research can read full pages through `WebFetch`, but that bypasses the gateway; the main gateway path remains snippet-heavy.
- Full-version buildout:
  real EDGAR/article/PDF fetchers under the gateway,
  parsing and normalization,
  provenance-carrying storage,
  unified fetch/reporting semantics.

### Internal document integration and federated search

- Current base: architecturally envisioned; not in committed runtime.
- Full-version buildout:
  secure internal-doc connectors,
  retrieval federation with public and historical sources,
  durable access-control handling.

## Semantic search and adaptive research depth

### Semantic retrieval over accumulated knowledge

- Current base: the round-to-round context loader currently loads all compiled entries for later rounds.
- Full-version buildout:
  relevance scoring,
  semantic retrieval over compiled entries,
  smarter context packing,
  duplicate/near-duplicate detection beyond simple heuristics.

### Adaptive replanning and semantic novelty search

- Current base: the minimum viable live iterative loop exists.
- Full-version buildout:
  semantic novelty signals,
  ADaPT-style branch deepening,
  richer replanning,
  divergence-aware decomposition,
  VOI-driven task updates.

## Knowledge accumulation and compounding memory

### Observation Library runtime

- Current base: data models, contracts, and an evaluator Pass 3 stub.
- Full-version buildout:
  recording failures and successes,
  query APIs,
  negative-space scans during evaluation,
  durable promotion/supersession logic.

### Cross-engagement knowledge and client calibration

- Current base: engagement-scoped wiki only.
- Full-version buildout:
  anonymized promotion across engagements,
  client or sector-specific calibration,
  trajectory storage,
  reusable institutional memory.

### Prompt evolution and skill promotion

- Current base: concept only.
- Full-version buildout:
  convert durable observations into constraints, skills, and improved defaults,
  manage promotion history and rollback.

## Output-system expansion

### Richer L2 content structuring

- Current base: thin provenance-bearing outline layer.
- Full-version buildout:
  deeper consulting-framework application,
  stronger section architecture,
  richer structure selection,
  better coherence handling across sections.

### L3 deliverable generation

- Current base: markdown only.
- Full-version buildout:
  PowerPoint,
  Excel,
  PDF,
  redrafting and export flows,
  presentation-quality deliverables rather than analysis-only markdown.

## Human review and product surface

### Reviewer UI and full HITL workflow

- Current base: backend/API state machine is real.
- Full-version buildout:
  consultant-facing reviewer interface,
  readable gate surfaces,
  modify/apply workflows,
  audit-friendly progress display,
  export and review ergonomics.

### Consultant-facing product UI

- Current base: no committed frontend product surface.
- Full-version buildout:
  project creation,
  run monitoring,
  artifact viewing,
  search,
  settings,
  multi-user interaction.

## Evaluator completion and calibration

### Wave 5 calibration and human alignment

- Current base: Layers 1-3 work; calibration is deferred.
- Full-version buildout:
  real-output review pack,
  human scoring,
  threshold tuning,
  profile tuning,
  empirical rather than intuitive evaluator settings.

### Layers 4-5 and richer judge stack

- Current base: Pass 3 observation scan is stubbed; higher evaluator layers are not active.
- Full-version buildout:
  process-trajectory evaluation,
  diverse-judge overlays,
  broader profile coverage,
  richer disagreement handling.

## Deployment and operations

### Production runtime shape

- Current base: there are seams for DB/API/config, but no clean committed product package.
- Full-version buildout:
  canonical release branch or packaging path,
  stable entrypoints,
  migrations,
  deploy manifests,
  runbooks,
  exemplar packs.

### Infrastructure

- Current base: config mentions PostgreSQL and Temporal; HITL backend is Temporal-ready in design only.
- Full-version buildout:
  PostgreSQL,
  Temporal,
  auth,
  multi-tenancy,
  caching,
  operational durability.

## Short read

The fuller version is still unmistakably larger than the current MVP spine. The missing full-version pieces are not cosmetic. They include the real retrieval moat, the compounding-memory moat, the richer deliverable stack, the consultant product surface, the human-calibrated evaluator, and the production runtime that would make the whole thing reliably usable outside a controlled demo.
