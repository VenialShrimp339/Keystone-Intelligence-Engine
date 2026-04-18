"""L4 Evaluator Stack for the Keystone Intelligence Engine.

The Evaluator is the most important component in the system:
evaluation quality bounds output quality. Three-layer stack
(Phase 1): deterministic verification, citation gate, rubric scoring.
"""

from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.layer1_deterministic import Layer1Evaluator
from keystone.evaluator.layer2_citation_gate import (
    DOIVerifier,
    HTTPDOIVerifier,
    Layer2CitationGate,
)
from keystone.evaluator.layer3_rubric import Layer3RubricScorer, weighted_geometric_mean
from keystone.evaluator.layer4_trajectory import Layer4Evaluator, ProcessContext
from keystone.evaluator.layer5_ensemble import EnsembleL3Evaluator
from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.evaluator.rubric_config import (
    ENGAGEMENT_PROFILE_MAP,
    STRATEGIC_WEIGHT_OVERRIDES,
    TIER_1_DIMENSIONS,
    TIER_1_FLOOR_THRESHOLDS,
    TIER_2_DIMENSIONS,
    EvaluationProfile,
    get_profile_weights,
)
from keystone.evaluator.sprint_contract import SprintContractGenerator
from keystone.evaluator.three_pass import ThreePassEvaluator

__all__ = [
    "DOIVerifier",
    "ENGAGEMENT_PROFILE_MAP",
    "EnsembleL3Evaluator",
    "EvaluationProfile",
    "Evaluator",
    "HTTPDOIVerifier",
    "LLMCallable",
    "Layer1Evaluator",
    "Layer2CitationGate",
    "Layer3RubricScorer",
    "Layer4Evaluator",
    "ProcessContext",
    "STRATEGIC_WEIGHT_OVERRIDES",
    "SprintContractGenerator",
    "TIER_1_DIMENSIONS",
    "TIER_1_FLOOR_THRESHOLDS",
    "TIER_2_DIMENSIONS",
    "ThreePassEvaluator",
    "get_profile_weights",
    "retry_llm_call",
    "weighted_geometric_mean",
]
