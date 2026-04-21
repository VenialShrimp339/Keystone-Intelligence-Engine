---
model: claude-opus-4-6
tuned: "2026-04"
---
You are generating a research task decomposition (research-tasks.json) from a prioritized MECE issue tree. Each leaf node becomes one or more discrete research tasks assigned to specialized agents.

## Input

**Research Question:** {{question}}
**Engagement Type:** {{engagement_type}}
**Engagement ID:** {{engagement_id}}
**Client ID:** {{client_id}}
**Day-1 Hypothesis:** {{day_1_hypothesis}}

### Prioritized Issue Tree
{{issue_tree}}

### Priority Scores
{{priorities}}

## Task Generation Rules

For each leaf node in the issue tree, create a ResearchTask:

1. **ID format:** `task_NNN` (e.g., task_001, task_002). Sequential, zero-padded to 3 digits.

2. **Category:** One of: market_sizing, competitive_landscape, financial_analysis, technology_assessment, regulatory, strategic_positioning. Use the category that best matches the leaf node's analytical domain.

3. **Type:** `estimative` for forward-looking probabilistic tasks, `current` for situation updates and factual mapping.

4. **Anti-confirmatory framing:** MANDATORY on every task. Must use evaluative language: "Evaluate whether..., including evidence both for and against." Must NOT start with "find evidence for", "prove that", "confirm that", or "show that".

5. **Dependencies:** Reference other task IDs that must complete before this task can start. Must form a DAG (no cycles). Root tasks have empty dependencies `[]`.

6. **End product:** Specific output format. Examples: "comparison table with 8+ competitors", "sensitivity analysis with +/-20% assumption variation", "regulatory timeline by jurisdiction".

7. **Assigned tools:** 3-5 MCP tools per task. Choose ONLY from this exact list: exa_search, brave_search, edgar_filings, fred_data, finnhub_market, paper_search, doi_verify. Do NOT use any tool names not in this list.

8. **Decision usefulness:** 1-5 scale. Client-facing tasks must be >= 3.

9. **Priority:** Integer rank (1 = highest) based on the priority scores.

## Output Format

Respond with ONLY a JSON object:

```json
{
  "decomposition_rationale": "Why the tasks were structured this way",
  "tasks": [
    {
      "id": "task_001",
      "category": "market_sizing",
      "type": "estimative",
      "target_decision_usefulness": 4,
      "description": "What this task investigates",
      "required_sources": ["industry_reports", "financial_data"],
      "acceptance_criteria": ["Criterion 1", "Criterion 2"],
      "deliverable_destination": "Section 2: Market Landscape",
      "priority": 1,
      "anti_confirmatory_framing": "Evaluate whether..., including evidence both for and against",
      "assigned_tools": ["exa_search", "brave_search", "edgar_filings"],
      "assigned_model": "standard",
      "end_product": "Specific deliverable format",
      "dependencies": [],
      "issue_tree_branch_id": "branch_1.1",
      "custom_category": null
    }
  ]
}
```