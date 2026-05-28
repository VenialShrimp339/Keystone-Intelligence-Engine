# Surprise Register

## 1. The strongest issue-tree move is narrative, not taxonomic

Minto's SCQA frame looks like a writing device, but for issue trees its deeper value is forcing the tree to answer a question that has a history. This prevents the model from producing a plausible framework detached from the client's actual decision state.

Skill implication: require a compressed problem story before tree generation.

## 2. MECE needs a source logic

The book makes MECE concrete by tying sibling groups to sequence, structure, or class. Many consulting frameworks treat MECE as a surface property. Minto turns it into a generative and diagnostic tool: if the grouping has no source logic, the tree is probably wrong.

Skill implication: every sibling group should carry a `branch_logic` field.

## 3. "Issue" is narrower than normal consulting usage

Minto's insistence that an issue should be a yes/no question is valuable for LLM evaluation. It gives graders an objective way to distinguish a real issue tree from a list of concerns.

Skill implication: the skill should convert concerns into yes/no issues before research planning.

## 4. Diagnostic frameworks are not solution trees

The distinction is easy to miss and highly useful. Diagnostic frameworks model the current system to explain R1. Logic trees enumerate possible interventions to reach R2. LLMs often collapse these into one blended tree.

Skill implication: require the model to label each tree as diagnostic, solution-generation, recommendation, or implementation.

## 5. The parent node is the hidden quality test

Weak trees often have decent leaves but bad parent summaries. Minto's critique of intellectually empty labels exposes a grading signal: the parent must state the insight implied by the child group.

Skill implication: evaluate parent-node specificity and overclaim separately from leaf coverage.

## 6. Alternatives are often mishandled

The book argues that alternatives should be treated as live only when the reader already recognizes them. Inventing straw alternatives creates a poor recommendation tree. The reason to choose an option must be that it solves the problem under the criteria, not merely that other options are bad.

Skill implication: the skill should ask whether alternatives are known, generated for completeness, or straw options. The tree shape changes accordingly.

## 7. The fastest research plan comes from elimination

A diagnostic tree is useful because it tells the analyst what evidence would remove entire branches. This connects Minto to modern decision science, active learning, and debugging: prioritize tests by discriminating power, cost, and ability to change the answer.

Skill implication: the pruned tree should show retained tests and deferred tests with pruning rationale.

## 8. R2 can be the missing variable

One of the seven problem states is knowing something is wrong without knowing what better result to aim for. Many issue-tree prompts hide this problem. A tree that races to root causes before defining R2 may be solving the wrong problem.

Skill implication: detect underspecified desired outcomes and create an objective-definition branch before diagnosis.

## 9. Visualization is a reasoning primitive

Minto repeatedly treats diagrams, process maps, financial trees, and physical structures as ways to make reasoning possible, not as presentation decoration. The model should be asked to "see" the system before naming branches.

Skill implication: include a compact system sketch or driver map for ambiguous operational problems.

## 10. Induction is where LLMs are most likely to fake insight

The book's warning about over-inference from grouped items directly maps to LLM behavior. A model often places related-sounding facts under a polished parent that says more than the facts prove.

Skill implication: require bottom-up parent validation: "Do these children prove exactly this parent, no more and no less?"
