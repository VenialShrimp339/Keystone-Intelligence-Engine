"""Observation Library — cross-run persistence of evaluation outcomes.

First slice: ``ObservationStore`` persists per-task evaluation outcomes
so future runs can detect recurring failure and success patterns.
"""

from keystone.observation.store import ObservationStore

__all__ = ["ObservationStore"]
