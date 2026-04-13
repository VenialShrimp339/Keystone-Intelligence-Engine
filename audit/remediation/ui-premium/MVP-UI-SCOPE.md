# MVP UI Scope

## Scope Decision

The UI workstream should define an eventual MVP UI, but runtime implementation remains blocked today.

This file answers:

- what the MVP UI should include
- what should wait for later
- what must explicitly wait for retrieval architecture lock

## Include In The Eventual MVP UI

### Analyst launch and planning

- chat-like research launcher
- file upload
- speech-to-text dictation
- plain-language depth control
- research-plan preview before execution

### Run visibility

- analysis history list
- stage timeline
- truthful run banners and degraded-state badges
- review-checkpoint cards

### Results and artifacts

- markdown brief as the primary deliverable surface
- evidence tab
- source tab
- outputs/workpapers tab
- artifact bundle browser for markdown and JSON outputs

### Truth and limits

- governed versus experimental labeling
- partial-evaluation labeling
- explicit source-limit and retrieval-limit language
- visible exclusions, gaps, and unresolved items

## Defer Until Later Product Depth

- multi-user review inbox as a fully separate product area
- meeting capture and persistent voice recording
- rich exports such as slides, PDF, DOCX, and spreadsheet packages
- collaborative editing
- bounded project/notebook workspaces
- cross-engagement history and memory browser
- design-system polish beyond what the backend truth can support

## Explicitly Wait Until Retrieval Architecture Locks

- final source-scope picker semantics
- fetched-document and anchored-passage viewer
- coverage metrics by source class
- query-result-fetch parse provenance graph
- unified governed-versus-bypass run history taxonomy
- any UI that implies governed full-document retrieval is already standard

## Explicitly Out Of MVP

- fake analyst swarm visualizations
- autonomous deep-research branding as the default path
- calibrated trust scores
- L2/L3 product surfaces as if they are active current-state deliverables
- Observation Library or self-improvement controls on the main analyst surface

## MVP Boundary Statement

The honest MVP UI is:

`analysis launcher + plan preview + run transparency + review checkpoints + markdown/evidence/source outputs + artifact browser`

It is not:

`a finished consultant platform with stable governed full-document retrieval, rich exports, polished reviewer collaboration, or cross-engagement institutional memory`
