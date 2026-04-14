# Browser Use Fit Against Keystone Retrieval

## Executive Judgment

The deeper second pass increased Browser Use's value score for Keystone, but not in the way that would change architecture.

What changed:

- Browser Use has a more serious low-level browser/runtime substrate than the first pass captured.
- Its auth/session, download/PDF, replay/eval, and operational provenance layers are materially better than a shallow skim suggests.
- The cloud product boundary is broader and more strategically relevant than the OSS package alone.

What did not change:

- Browser Use still does not solve governed fetch authority.
- It still does not give Keystone deterministic parse artifacts.
- It still does not produce evidence bundles or anchored citation objects.
- It still does not retire the current retrieval MVP critical path.

That leaves Browser Use as a strong browser-native supplement and a stronger-than-expected benchmark/control arm, not a replacement for Retrieval MVP architecture.

## What The Second Pass Added

The first pass was directionally right but underweighted five value clusters.

### 1. Reusable browser substrate

`BrowserSession`, `DomService`, `Page`, `Element`, `Tools`, and the watchdog layer make Browser Use more interesting as a bounded runtime seam below the full agent loop.

### 2. Auth and state

Chrome profile reuse, storage-state load/save/merge, domain-scoped secrets, TOTP generation, and Gmail-based OTP support make it meaningfully better on login-gated acquisition than ordinary fetch.

### 3. Hard-page acquisition

JS-heavy pages, shadow DOM, some cross-origin iframe handling, PDF-viewer handling, and download flows are all stronger than first pass emphasized.

### 4. Replay and control-arm value

Saved histories, rerun, variable substitution, element rematching, judge/eval infrastructure, and rich operator sidecars make it more valuable for benchmark/control-arm work than first pass reflected.

### 5. Browser Use Cloud as separate strategic surface

Managed browsers, profiles, live takeover, skills, and search/session APIs make the cloud product more strategically relevant than the OSS package alone, especially for vendor-backed fallback acquisition evaluation.

## Gap-By-Gap Fit

| Keystone gap | Fit | Judgment |
|---|---|---|
| Article fetch | partial | Overkill for ordinary article fetch, but genuinely helpful for browser-gated, dynamic, or interaction-heavy articles. |
| PDF acquisition | partial to strong | Stronger than first pass implied on "get the file" problems because PDF-viewer/download handling is real. Still weak on canonical PDF parsing and locator fidelity. |
| JS-heavy pages | strong | One of Browser Use's clearest strengths because it uses a real browser, rendered DOM, shadow DOM handling, and broader session/runtime state. |
| Authenticated / dynamic sites | strong | One of the most meaningful hidden value areas because of storage state, Chrome profile reuse, secrets, TOTP, and session persistence. |
| Provenance / auditability | partial | Better than first pass implied because HAR, screenshots, downloads, histories, and rerun traces are substantial. Still not Keystone-grade evidence provenance. |
| Deterministic evidence extraction | weak | The extract path remains markdown plus LLM plus schema-shaping. It is useful operationally and still not deterministic evidence extraction. |
| Canonical citation support | weak | No anchored citation contract, no stable evidence-bundle locators, no claim-support object model. |

## What It Helps With

Browser Use can materially help Keystone in bounded ways:

- acquire rendered content when direct article fetch is incomplete
- obtain content behind browser session state
- interact to reach the real artifact or download
- recover PDFs/files from browser-viewer or click-gated flows
- produce useful operational sidecars during acquisition failure analysis
- act as a shadow benchmark/control arm for browser-native retrieval experiments

In other words, it improves the odds that Keystone gets the artifact and can compare browser escalation against non-browser retrieval paths.

It does not improve the governed meaning of that artifact unless Keystone wraps and normalizes the output itself.

## What It Does Not Solve For Keystone

Browser Use still does not solve these Keystone requirements:

- governed evidence model
- deterministic parse and evidence bundles
- anchored citation contract
- claim-level citation support
- control-plane or tool-surface authority rules
- the separate SEC venue/access blocker

Those remain Keystone responsibilities even if Browser Use is adopted as a fallback acquisition backend.

## Browser Use Versus Continue Building Keystone's Governed Fetch Layer

| Dimension | Browser Use | Keystone governed fetch layer |
|---|---|---|
| Quality on ordinary articles/PDFs | Often worse or less direct because the browser path is heavier | Better when direct fetch/parsers work |
| Quality on dynamic/auth/browser-native pages | Better | Weaker unless Keystone builds or buys browser fallback |
| Retrieval depth | Strong for interactive acquisition and session-gated flows | Strong for canonical artifact ownership, normalization, and evidence discipline |
| Reliability | Good enough for fallback and experiments, but more layout-sensitive and runtime-heavy | Better for standard fetch cases because request/parse flows are simpler and more deterministic |
| Auditability | Better than a black-box macro because it can emit HAR, screenshots, histories, downloads, and rerun traces | Better for canonical hashes, coverage labels, parse provenance, and downstream evidence contracts |
| Maintenance burden | Saves some browser engineering, but adds browser runtime, model, extension, and optional vendor/cloud complexity | More up-front work, but cleaner ownership and less architectural mismatch |
| Anti-bot / browser complexity | Strong advantage, especially if Browser Use Cloud is evaluated | Requires Keystone to build or buy comparable browser fallback later |
| Product risk | Higher if made canonical because retrieval starts depending on agent/browser behavior and possibly vendor stealth infrastructure | Lower on the canonical path because architecture stays governed and typed |

## Net Fit

Browser Use is now a stronger answer to this question than first pass suggested:

"How do we acquire some of the pages a normal governed fetch lane will miss, and how do we benchmark that browser escalation?"

It is still a bad answer to this question:

"What should Keystone's canonical retrieval architecture be?"

## Fit Summary

- As a replacement for canonical retrieval: not a fit
- As a supplement for hard acquisition cases: yes
- As a benchmark/control arm: more valuable than first pass captured
- As a way to avoid building governed fetch, parse, and citation contracts: no

## Recommendation Signal

If Keystone uses Browser Use at all, the fit is:

- `FALLBACK_ONLY` for production architecture
- strong secondary value as `BENCHMARK_OR_CONTROL_ARM_ONLY`
- system-owned only
- downstream-normalized into Keystone artifacts only

Anything broader would blur discovery, fetch, parse, and citation seams that Keystone is explicitly trying to harden.
