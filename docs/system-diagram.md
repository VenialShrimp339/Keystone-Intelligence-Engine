# System Diagram

> Status: support architecture diagram. Not current-state truth.
> Read `AUTHORITY-INDEX.md`, `SESSION-STANDARD.md`, and the control-plane pair first.
> Labels such as `Built`, `Pressure-tested`, `Current repo reality`, and `Implemented and evidenced now` below are derived support labels for architecture orientation only; they do not certify the checked-out worktree, live lane authorization, or present runtime truth.

## Legend

- `Built`: implemented in code and represented in the repo
- `Pressure-tested`: exercised with real-model or real-tool component tests documented in the repo
- `Planned`: part of the intended architecture, not the current meeting claim
- `In validation`: code path exists and the MVP is built, but human-reviewed exemplar output is still pending

## 1. High-Level Architecture

```mermaid
flowchart LR
    U[User / Client Question]
    L0[L0 Specification Engine<br/>Built + Pressure-tested]
    G1[HITL Gate 1<br/>Built]
    L1[L1 Research Agents<br/>Built + Pressure-tested]
    CP[CitationProcessor<br/>Built + Pressure-tested]
    L15[L1.5 Deliberation<br/>Built + Pressure-tested]
    G2[HITL Gate 2<br/>Built]
    L4[L4 Evaluator<br/>Built + Pressure-tested]
    MR[Markdown Renderer<br/>Built]
    OUT[Phase 1 Markdown Output<br/>Built path, now under validation]
    L2[L2 Content Structuring<br/>Planned / Phase 2]
    L3[L3 Deliverable Generation<br/>Planned / Phase 2]
    OBS[Observation Library / Meta-layer<br/>Planned / partial foundation]

    U --> L0 --> G1 --> L1 --> CP --> L15 --> G2 --> L4 --> MR --> OUT
    OBS -. informs improvement over time .-> L0
    OBS -. informs improvement over time .-> L4
    L15 -. future richer handoff .-> L2 --> L3

    classDef built fill:#d9f2d9,stroke:#2d6a2d,color:#111;
    classDef partial fill:#fff0c2,stroke:#8a6d1d,color:#111;
    classDef planned fill:#e7e7e7,stroke:#6b6b6b,color:#111;

    class L0,G1,L1,CP,L15,G2,L4,MR built;
    class OUT partial;
    class L2,L3,OBS planned;
```

## 2. Actual Phase 1 MVP Workflow For This Meeting

The `output/first_real_run/` path shown below refers to archived demo evidence, not to current live truth or active output canon.

```mermaid
flowchart TD
    A[Consulting-style research question]
    B[Specification Engine classifies question,<br/>builds issue tree, hypothesis, and task DAG]
    C[Research agents execute scoped tasks<br/>with assigned tools]
    D[CitationProcessor deduplicates and verifies sources]
    E[Deliberation compares claims,<br/>maps confidence, and flags gaps]
    F[Evaluator scores output quality]
    G[Markdown renderer assembles Phase 1 output path]
    H[Expected artifact location:<br/>output/first_real_run/]
    I[Current repo reality:<br/>first real run interrupted before exemplar review]

    A --> B --> C --> D --> E --> F --> G --> H --> I

    classDef normal fill:#d9f2d9,stroke:#2d6a2d,color:#111;
    classDef warn fill:#fff0c2,stroke:#8a6d1d,color:#111;

    class A,B,C,D,E,F,G,H normal;
    class I warn;
```

## 3. Implementation Status Map

```mermaid
flowchart TB
    subgraph Implemented_Now[Implemented and evidenced now]
        S1[Specification Engine]
        S2[Research Agents]
        S3[CitationProcessor]
        S4[Deliberation]
        S5[Evaluator]
        S6[Pipeline Orchestrator]
        S7[Markdown Renderer]
        S8[HITL State Machine]
    end

    subgraph Current_Gaps[Current validation gaps]
        G1[Human-reviewed full-pipeline exemplar pending]
        G2[Citation metadata gap depresses evaluator scores]
        G3[Codex OAuth latency / stability]
    end

    subgraph Deferred_Future[Deferred or future-facing architecture]
        F1[L2 Content Structuring]
        F2[L3 Deliverable Generation]
        F3[Observation Library at full operating depth]
        F4[Evaluator calibration against human scores]
    end

    S1 --> G1
    S2 --> G2
    S5 --> G2
    S6 --> G1
    G3 --> G1

    classDef implemented fill:#d9f2d9,stroke:#2d6a2d,color:#111;
    classDef gap fill:#fff0c2,stroke:#8a6d1d,color:#111;
    classDef future fill:#e7e7e7,stroke:#6b6b6b,color:#111;

    class S1,S2,S3,S4,S5,S6,S7,S8 implemented;
    class G1,G2,G3 gap;
    class F1,F2,F3,F4 future;
```
