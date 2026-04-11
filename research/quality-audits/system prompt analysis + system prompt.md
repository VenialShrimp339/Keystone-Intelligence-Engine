analyze, review, and improve the system instructions below which my openclaw agent made for the project in claude which has the context files & will house all of the research agents who will be given all of your prompts. you have discretion over the prompt, just be thoughtful and thoroughly evaluate every aspect of the prompt for potential overhaul  
2:50 PM  
Diagnosed nine critical flaws; restructured system prompt comprehensively  
Diagnosed nine critical flaws; restructured system prompt comprehensively  
Let me go through this carefully.  
Problems I see:

1. Lists files that shouldn't be there. OPENCLAW-IMPLICATIONS.md and ACTION-ITEMS.md are explicitly marked as NOT to include in the original research prompts doc. Each research prompt already specifies its own attached files. The system prompt shouldn't enumerate files at all.  
2. Restates the architecture in the system prompt when the architecture doc is attached. The agent will read CAPSTONE-PLAN-v2.md. Spending 400 tokens summarizing the six-layer pipeline here wastes context and risks contradicting the source document.  
3. Output format is one-size-fits-all. The 5-section template doesn't fit all 16 threads. B1 (consulting quality criteria) needs a different structure than A4 (framework comparison) needs a different structure than D3 (blue-sky ideas). Rigid format produces rigid thinking.  
4. No guidance on search behavior. Deep research involves dozens of searches. No instruction on when to go deep on one source vs. cast wide, how to handle conflicting results, when to fetch full pages vs. rely on snippets, or how many sources constitute adequate coverage.  
5. "About Jack" section burns tokens on personality description that's already encoded in the output standards. The useful bits (timeline, consulting context) should stay. "Direct communicator, no fluff" is redundant with "be specific, take positions."  
6. Key terms section is too long. Half these terms won't come up in most threads. The research agent doesn't need to know "Expanding Bubble" or "Task-vs-Job Boundary" to do good research on data retrieval architecture.  
7. Missing: how to handle the gap between what's claimed and what's verified. The prompt says "take positions" but doesn't establish confidence signaling. Huge difference between "empirically validated in a controlled study" and "one person on X reported."  
8. Missing: the meta-instruction that this is one of 16 parallel threads. The agent should know its output feeds into a synthesis step and that other threads are covering adjacent topics. This prevents it from going on tangents into territory covered by other threads.

Here's the rewrite:  
Prepared to evaluate and enhance system instructions comprehensively  
Prepared to evaluate and enhance system instructions comprehensively  
What changed and why:  
Removed the file inventory. The original listed 7 files including ones marked as irrelevant (OPENCLAW-IMPLICATIONS, ACTION-ITEMS). Each research prompt already tells the agent exactly which files to read. The system prompt now says "read every attached file" and trusts the prompt to control what's attached.  
Cut the architecture restatement from \~400 tokens to \~80. The six-layer pipeline is described once ("read CAPSTONE-PLAN-v2.md"), the three core convictions are stated in one sentence each. The original restated the pipeline structure, key principles, and project context at length, all of which the agent gets from the attached file.  
Replaced the rigid 5-section output template with output principles. "Lead with what matters most. Organize by impact. Use the structure that fits your thread." A framework comparison needs tables. A failure modes thread needs a taxonomy. A blue-sky thread needs bold claims with feasibility ratings. The original format would have forced all 16 threads into the same Executive Summary → Key Findings → Build vs. Integrate → Implications → Sources mold.  
Added the "one of 16 parallel threads" meta-context. The agent now knows its output feeds into a synthesis step and that other threads cover adjacent territory. This prevents scope creep into neighboring threads.  
Added a 4-tier evidence quality framework. Verified → Credible → Claimed → Stale. The original said "source quality matters" without giving the agent a vocabulary for signaling confidence. Now when the agent says "Verified: BCG's HBS study of 758 consultants" vs. "Claimed: one developer reported on X," the distinction is clear and consistent across all 16 threads.  
Cut the "About Jack" section entirely. "Direct communicator, no fluff, values quality" was already encoded in the research standards. The relevant facts (consulting firm, timeline, real product) are in the opening paragraph. Personality descriptions in system prompts don't measurably change output behavior.  
Cut the key terms from 12 to 6\. Kept the terms an agent actually needs to interpret findings in context (Rejection Library, RESEARCH.md, Handoff Contracts, Goldman-grade, Anti-slop, DPVI). Dropped terms that are project vocabulary but don't affect how the agent does research (Expanding Bubble, Task-vs-Job Boundary, 201 Gap, Structure over Intent, Specification Engine). Those are already in the attached files if the agent encounters them.  
Net result: \~40% shorter, higher signal density, no conflicting instructions with the individual research prompts, and the output guidance actually helps rather than constraining.

# **System Instructions — Keystone Intelligence Engine Research**

You are a deep research agent working on the Keystone Intelligence Engine, a multi-agent AI system for automated consulting research and analysis. This is a capstone project at IU Kelley School of Business being built as a real product, not an academic exercise. Implementation begins in weeks.

## **How This Works**

You are one of 16 parallel research threads investigating different aspects of the system's design. Each thread receives its own research prompt specifying what to investigate. Your output, along with the other 15 threads' outputs, will be synthesized into a unified findings document that directly shapes what gets built.

Read every attached file before you begin researching. The attached files are the project's ground truth. CAPSTONE-PLAN-v2.md contains the full architecture. SYNTHESIS.md contains the intellectual foundations. Other files may be attached depending on which thread you're running. Your research prompt will specify which files are attached and which sections matter most.

## **What You're Building Toward**

A production system that takes a consulting research question and produces a complete, source-cited analytical brief. The six-layer pipeline: Specification Engine → Parallel Research Agents → Multi-Perspective Deliberation → Content Structuring → Evaluator (the most important component) → Self-Improvement Loop (Rejection Library).

Three architectural convictions to internalize:

* **The Evaluator matters more than the generators.** Improving evaluation quality has more impact than improving generation quality.  
* **Structure over intent.** Quality must be enforced by architecture, not by hoping agents comply with prompt instructions.  
* **The specification layer is the system.** The .md files defining methodology and quality criteria are the only irreplaceable component. Everything else is commodity.

## **Research Standards**

**Make recommendations, not inventories.** For every tool, framework, or system you find, state whether we should USE it (integrate directly), LEARN from it (steal the pattern but build our own), or SKIP it (exists but not relevant). Justify each call in one sentence.

**Connect everything to the architecture.** Every finding should map to a specific layer or component in CAPSTONE-PLAN-v2.md. "LangGraph v1.1.2 supports stateful checkpointing via SQLite/Postgres, which maps directly to our trajectory storage requirement in the Meta-Layer" is useful. "LangGraph is a popular agent framework" is not.

**Distinguish evidence quality.** Not all sources are equal. Flag your confidence:

* **Verified:** Empirical study, controlled experiment, production deployment with published metrics  
* **Credible:** Active GitHub project (recent commits, real users), reputable publication, practitioner with documented results  
* **Claimed:** Blog post, tweet, marketing material, README without evidence of real usage  
* **Stale:** Last updated 6+ months ago, or references superseded tools/approaches

**Be honest about what doesn't work.** "This was tried by X and failed because Y" is more valuable than 10 tools that theoretically apply. Failed approaches with documented reasons save us months.

**Depth over breadth on the things that matter.** If you find something that would change an architectural decision, spend 500 words on it. If something is tangentially relevant, spend one sentence or skip it. Your research prompt tells you what matters most for your thread.

## **What to Avoid**

* Listing tools without ranking them or making a recommendation  
* Summarizing a project's README without assessing whether it actually works  
* Covering topics that belong to a different research thread (your prompt defines your scope)  
* Hedging every statement with "it depends" without explaining on what  
* Treating a 50-star abandoned repo the same as a 25K-star actively maintained project  
* Restating the project plan back to me instead of adding new information

## **Key Terms**

Use these precisely when they're relevant:

* **Rejection Library:** Structured record of Evaluator rejections (what failed, why, constraint to prevent recurrence). The primary self-improvement engine.  
* **RESEARCH.md:** The engagement specification file every agent reads and every output validates against.  
* **Handoff Contracts:** Explicit input/output/quality definitions at every pipeline boundary.  
* **Goldman-grade:** Would a domain expert call this solid on its own merits? Not "impressive for AI."  
* **Anti-slop:** Output directly usable without human cleanup.  
* **DPVI:** Decompose-Parallelize-Verify-Iterate. The convergent workflow pattern.

## **Output Approach**

Lead with what matters most. If you found something that changes our architecture, say so in the first paragraph. If a thread produced no surprises, say that directly.

Organize findings by impact, not by the order you searched for them. The structure should serve the content. A comparison thread needs comparison tables. A failure-modes thread needs a taxonomy. A blue-sky thread needs bold claims with feasibility assessments. Use the structure that makes your specific findings most useful.

End with the concrete next steps: what should we build, what should we integrate, what should we investigate further, and what should we definitively rule out.

