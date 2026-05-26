"""Core module for the coding agent."""

from .agent import CodingAgent
from .context import ConversationContext
from .planner import Plan, PlanItem, PlanMode
from .enhanced_planner import (
    EnhancedPlanner,
    HierarchicalPlan,
    PlanItem as HierarchicalPlanItem,
    PlanStatus,
    DependencyType,
    Checkpoint,
)
from .vulnerability_remediator import (
    VulnerabilityRemediator,
    VulnerabilityFinding,
    RemediationPlan,
    RemediationPlanItem,
)

__all__ = [
    "CodingAgent",
    "ConversationContext",
    "Plan",
    "PlanItem",
    "PlanMode",
    "EnhancedPlanner",
    "HierarchicalPlan",
    "HierarchicalPlanItem",
    "PlanStatus",
    "DependencyType",
    "Checkpoint",
    "VulnerabilityRemediator",
    "VulnerabilityFinding",
    "RemediationPlan",
    "RemediationPlanItem",
]
