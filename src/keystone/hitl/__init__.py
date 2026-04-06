"""Human-in-the-Loop review gate infrastructure.

Implements the two mandatory human review gates (Jack's Directive 7):
1. Post-Specification: after issue tree + agent configs, before research
2. Post-Deliberation: after confidence map, before content generation

Phase 1: PostgreSQL state machine with REST API.
Phase 2: Maps to Temporal Signals with no agent code changes.
"""
