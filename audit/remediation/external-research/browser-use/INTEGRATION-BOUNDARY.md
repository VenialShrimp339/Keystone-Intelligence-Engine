# Browser Use Integration Boundary

## Classification Boundary

Recommended placement: `FALLBACK_ONLY`

Browser Use should not sit on Keystone's canonical governed retrieval path as the default fetch mechanism.

If adopted, it should sit behind Keystone's system-owned fetch control plane as a narrowly scoped browser-native acquisition backend for cases where ordinary governed fetch is insufficient.

The deeper second pass sharpened one important point:

- the lowest-risk seam is below the full autonomous agent loop
- the highest-value reusable surfaces are `BrowserSession`, `Tools`, DOM/download/state watchdogs, and their sidecar artifacts
- MCP and CLI are thinner wrappers, useful later if protocol isolation matters, but not the preferred first integration

## Exact Placement

Browser Use belongs here:

`SourceCandidate -> promotion decision -> system-owned fetch backend -> Browser Use fallback only when needed -> persisted artifact -> Keystone deterministic parse -> EvidenceBundle -> anchored citation`

It does not belong here:

- `ResearchTask.assigned_tools`
- LLM task-generation tool lists
- direct synthesis over Browser Use agent output
- direct citation generation from Browser Use extraction output

## Invocation Rule

Browser Use should be callable only by Keystone retrieval control-plane logic after discovery normalization.

Reasonable triggers:

- standard governed HTTP/article fetch fails
- page renders materially incomplete without a browser
- source requires authenticated browser state
- source requires interaction to reach the real artifact or download
- fallback policy explicitly allows browser escalation for that source family

It should not be used merely because a browser "might be nice."

The key bar should be necessity, not convenience.

## Allowed Source Families

If adopted now, keep the boundary tight:

- `article`
- `pdf`

Do not widen the first integration to:

- SEC/EDGAR venue work
- paper/full academic retrieval policy
- general open-ended browsing for research synthesis

## Allowed Outputs

The Browser Use adapter should return acquisition artifacts and telemetry only.

Minimum safe output:

- final URL after browser navigation
- redirect/navigation chain if available
- MIME/content-type judgment
- persisted raw artifact or rendered capture
- content hash of the persisted artifact
- access timestamp
- explicit coverage outcome
- optional sidecar telemetry such as HAR, screenshot, download metadata, and browser-state notes

Those outputs then need to be normalized into Keystone's own fetch DTOs and artifact store.

Preferred returned material:

- raw downloaded artifact when available
- rendered capture only when raw artifact is not available
- sidecar telemetry kept clearly separate from canonical evidence artifacts

## Forbidden Outputs

Do not allow Browser Use to define or short-circuit:

- evidence-bundle structure
- claim support logic
- citation locators
- final excerpts used as canonical evidence
- task-assigned retrieval authority
- acceptance proof for Retrieval MVP by itself

Most importantly:

- do not treat Browser Use's `extract` action as Keystone's evidence extractor
- do not treat Browser Use's `done` output as canonical retrieval evidence
- do not cite Browser Use agent summaries directly

Also:

- do not let Browser Use's rerun/judge stack become claim validation
- do not let Browser Use Cloud search/session APIs become canonical discovery or evidence sources
- do not let Browser Use MCP/CLI shape Keystone's retrieval contract

## Why The Boundary Must Be This Tight

Keystone's architecture memo defines the critical seam as:

`discovery -> governed fetch -> deterministic parse -> evidence bundle -> synthesis -> anchored citation`

Browser Use can help the `governed fetch` stage acquire hard content.

It does not safely subsume:

- deterministic parse
- evidence selection
- anchored citation

If it is allowed to bleed into those stages, Keystone will recreate the same architecture blur it is currently trying to remove from the retrieval path.

## Open-Source Versus Cloud Boundary

The open-source/local Browser Use path is the safer architectural fit for an initial evaluation because it keeps Keystone closer to self-owned execution.

Browser Use Cloud adds real value for:

- stealth
- proxy rotation
- captcha handling
- geo-routed browsers

But it also adds separate risk:

- vendor dependency
- hosted-browser governance questions
- product/legal review for stealth workflows
- more ambiguous provenance posture

So if Keystone ever uses Browser Use Cloud, that should be a second decision after the base fallback boundary is accepted.

The second pass makes the cloud decision look more important than first pass suggested, because much of the hard-site value lives there:

- managed stealth/proxy browsers
- persistent remote sessions and profiles
- live takeover
- vendor-hosted search/task/session APIs

That makes Browser Use Cloud worth a separate vendor evaluation, but not a reason to widen the canonical retrieval seam.

## Preferred Technical Seam

If Keystone ever integrates Browser Use, the preferred order is:

1. `BrowserSession + Tools` in-process, behind a Keystone-owned adapter.
2. Local MCP sidecar only if protocol isolation is worth the thinner surface.
3. CLI/daemon only for operator workflows, ad hoc debugging, or disposable experiments.

Reason:

- the in-process surface is richer and more faithful
- MCP narrows extraction and session semantics
- CLI is more operator-facing and relies on thinner or more private plumbing

Keystone should not start by integrating the full `Agent` loop, the legacy TUI, or the fast CLI as its main retrieval contract.

## Safe First Integration Shape

If Keystone revisits this later, the safest first integration is:

1. Keep building Keystone's own governed `document_fetch` or equivalent system-owned fetch contract.
2. Add a Browser Use-backed fallback backend behind that contract.
3. Persist artifacts and telemetry into Keystone-owned storage.
4. Run Keystone's own deterministic parser on those artifacts.
5. Require Keystone's own citation and evidence contracts downstream.

That preserves the governed architecture while still buying Browser Use's browser-native acquisition ability.

If Keystone wants to exploit the replay/eval value, keep that as a separate shadow lane:

1. save Browser Use history and sidecar artifacts
2. use rerun/judge only for benchmark/control-arm evaluation
3. never let those outputs short-circuit canonical retrieval acceptance

## Current Program Impact

This boundary does not change the current blocker-remediation order.

Browser Use does not resolve:

- the current `document_fetch` authority decision
- parser lane work
- evidence-bundle work
- citation-locator work

So the evaluation should remain sidecar research unless and until Keystone's own canonical fetch contract is already settled.
