# Gap Triage: 8 Remaining Gaps from Unified Synthesis
*Conducted: 2026-04-04*

Each gap is assessed on three dimensions:
- **Blocks Phase 1?** Can we start building core pipeline components without resolving this?
- **Time-sensitive?** External deadline or competitive pressure?
- **Resolvable now?** Can we answer with available information?

---

## Gap 1: Keystone-specific rubric calibration methodology
*Requires actual Keystone deliverables scored by experienced consultants*

- **Blocks Phase 1?** NO. We can build the full evaluator stack and 10-dimension rubric using synthetic calibration data and Jack's scoring of sample outputs. The 0.80+ Spearman calibration target is a Phase 1 acceptance criterion, but the methodology for getting there (score 100-200 samples) can begin with available deliverables.
- **Time-sensitive?** Yes -- evaluator calibration is on the critical path. Earlier calibration = earlier confidence in automated scoring.
- **Resolvable now?** PARTIALLY. We can define the scoring protocol, build the calibration infrastructure, and begin scoring with Jack's judgment. Full calibration against Keystone partner-level judgment requires access to past deliverables and partner feedback.
- **Action needed:** Jack provides 10+ past Keystone deliverables with his quality assessment. This is the minimum viable calibration set. Define a scoring rubric worksheet (10 dimensions, 1-5 scale each) for manual scoring.
- **From whom:** Jack (deliverables + scoring), potentially a Keystone partner (validation scoring)

---

## Gap 2: Multi-tenancy architecture for client isolation at scale
*Client data sandboxing described at principle level, not engineered*

- **Blocks Phase 1?** NO. Phase 1 operates on one engagement at a time. Multi-tenancy is a scale concern.
- **Time-sensitive?** No.
- **Resolvable now?** Yes, at the design level. pgvector supports row-level security. Filesystem isolation per engagement is straightforward. The retrieval layer's per-client sandboxing (Section 6.3) can be designed in Phase 1 and enforced by schema (client_id on every record).
- **Action needed:** Include client_id in all data schemas from Day 1. Design row-level security policies for pgvector tables. Defer full multi-tenancy implementation to Phase 2+.

---

## Gap 3: EU AI Act compliance (August 2026 deadline)
*Specification documentation requirements mentioned but not designed for*

- **Blocks Phase 1?** NO. The Intelligence Engine is a tool used by consultants, not a standalone decision-making system. It likely falls under limited-risk or minimal-risk categories. The key requirement is transparency (users must know they're interacting with AI output).
- **Time-sensitive?** YES -- August 2026 is 4 months away. But the compliance burden is low for this use case.
- **Resolvable now?** PARTIALLY. The basic transparency and documentation requirements are clear. Whether the system qualifies as "high-risk AI" under the Act depends on how it's deployed (internal tool vs. client-facing product).
- **Action needed:** Classify the system under EU AI Act risk categories. At minimum: (1) document that outputs are AI-generated, (2) maintain audit logs of all agent decisions (already planned via trajectory storage), (3) ensure human oversight capability (already designed via human-in-the-loop gates). Full legal review if Keystone plans to sell the system as a product (vs. use internally).
- **From whom:** Legal counsel or compliance advisor for formal classification.

---

## Gap 4: Expert network integration design
*GLG/AlphaSights recommended as data sources, no integration architecture*

- **Blocks Phase 1?** NO. Expert networks are a data source enhancement, not a pipeline dependency. Phase 1 operates on public data sources.
- **Time-sensitive?** No.
- **Resolvable now?** No. Requires API access negotiations with GLG/AlphaSights and understanding their data formats.
- **Action needed:** Defer to Phase 2+. Design the L1 agent interface to accept expert network data as a source type (the search API stack in Section 6.2 already accommodates this pattern).

---

## Gap 5: Temporal knowledge graph implementation
*Recommended for living competitive landscapes, no production architecture evaluated*

- **Blocks Phase 1?** NO. Phase 1 produces point-in-time research, not living landscapes. Knowledge graphs are a Phase 3 capability.
- **Time-sensitive?** No.
- **Resolvable now?** Partially. Graphiti (Zep) and Neo4j are evaluated in the research reports. But production architecture design requires understanding the actual data volumes and query patterns from Phase 1 operation.
- **Action needed:** Defer to Phase 3. Ensure trajectory storage (Phase 2) captures the temporal metadata that a knowledge graph would later ingest.

---

## Gap 6: Evaluator calibration drift detection
*How to detect when evaluator agreement with human judgment deteriorates*

- **Blocks Phase 1?** NO for building. YES for production trust. The plan already specifies continuous re-calibration every 5-10 engagements (Section 5.4), but doesn't specify the drift detection mechanism.
- **Time-sensitive?** Not for Phase 1 build, but needed before declaring the evaluator production-ready.
- **Resolvable now?** YES. Standard approach: maintain a held-out "canary set" of 20-30 pre-scored samples. Run the evaluator against the canary set periodically. If Spearman correlation drops below 0.75 (below the 0.80 production threshold with margin), trigger re-calibration. Promptfoo (already in the tool stack) supports canary evaluation.
- **Action resolved:** Add to implementation spec: build a canary evaluation set as part of Evaluator calibration (Phase 1, item #9). Run canary check after every 5 engagements. Alert if correlation drops below 0.75.

---

## Gap 7: Cost model for the full 5-layer evaluation stack
*A5 estimates $7-$85/engagement but predates the 5-layer recommendation*

- **Blocks Phase 1?** NO. The validated cost model ($7-$85) covers the base pipeline. The 5-layer stack adds cost from: Prometheus 2 (runs locally, no API cost), cross-model ensemble (2-3 API calls per evaluation), FActScore (pip install, minimal cost). The dominant cost driver remains the same (verification = ~72% of tokens).
- **Time-sensitive?** No.
- **Resolvable now?** YES. Rough estimate: Layers 1-2 (deterministic, local) add ~$0. Layer 3 (Prometheus 2, local) adds ~$0 API cost but requires Mac Mini compute. Layers 4-5 (cross-model ensemble, 2-3 models) add ~$5-15/engagement for the API calls. Revised range: **$12-$100/engagement** fully loaded. Still 0.3-3% of engagement revenue.
- **Action resolved:** Update cost model in implementation spec with 5-layer estimate. Monitor actual costs during Phase 1 testing.

---

## Gap 8: Rate limit management at 15-50 parallel agents
*Tier 4+ API access or custom invoicing required*

- **Blocks Phase 1?** YES for full-scale testing, NO for development. Development and testing can run with 3-5 parallel agents. Full 15-50 agent parallelism requires higher rate limits.
- **Time-sensitive?** Yes -- rate limit upgrades require account history and sometimes negotiation.
- **Resolvable now?** PARTIALLY. Anthropic's rate limits scale with usage tier. Development starts at lower tiers. The MCP gateway architecture (Section 12.0) with rate limiting and circuit breakers is designed to handle this gracefully -- agents queue rather than fail when rate-limited.
- **Action needed:** (1) Begin building with 3-5 agent parallelism. (2) Monitor usage to organically tier up. (3) If full-scale testing is needed before natural tier progression, contact Anthropic for tier upgrade or custom invoicing. (4) Implement exponential backoff in the MCP gateway from Day 1.
- **From whom:** Anthropic (tier upgrade request when needed)

---

## Summary

| Gap | Blocks Phase 1? | Resolved? | Action |
|-----|-----------------|-----------|--------|
| 1. Rubric calibration methodology | No (build) / Yes (validate) | Partially | Jack provides 10+ deliverables + scores |
| 2. Multi-tenancy | No | Design only | Include client_id in schemas from Day 1 |
| 3. EU AI Act | No | Partially | Classify risk category; build transparency features |
| 4. Expert network integration | No | No | Defer to Phase 2+ |
| 5. Temporal knowledge graph | No | No | Defer to Phase 3 |
| 6. Calibration drift detection | No (build) / Yes (production) | **YES -- resolved** | Canary set of 20-30 pre-scored samples |
| 7. Cost model for 5-layer stack | No | **YES -- resolved** | Est. $12-$100/engagement |
| 8. Rate limit management | No (dev) / Yes (full-scale) | Partially | Build with 3-5 agents; tier up organically |

**No gap blocks Phase 1 development.** Gaps 6 and 7 are resolved above. Gaps 1 and 8 require external action before production deployment but not before building.
