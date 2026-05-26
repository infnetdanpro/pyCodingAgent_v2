"""Enhanced planning module with hierarchical planning, dependency tracking, and rollback support."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from pathlib import Path
import json
import hashlib

from ..config import ModelConfig
from ..llm import LLMClient, Message, Role

logger = logging.getLogger(__name__)


class PlanStatus(Enum):
    """Status of a plan item."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class DependencyType(Enum):
    """Types of dependencies between plan items."""
    SEQUENTIAL = "sequential"  # Must complete in order
    PARALLEL = "parallel"  # Can run simultaneously
    CONDITIONAL = "conditional"  # Depends on condition being met


@dataclass
class Checkpoint:
    """Represents a checkpoint for rollback functionality."""
    
    id: str
    timestamp: datetime
    state_snapshot: dict
    description: str
    plan_item_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert checkpoint to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "state_snapshot": self.state_snapshot,
            "description": self.description,
            "plan_item_id": self.plan_item_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        """Create checkpoint from dictionary."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            state_snapshot=data["state_snapshot"],
            description=data["description"],
            plan_item_id=data.get("plan_item_id")
        )


@dataclass
class PlanItem:
    """Represents a single item in a hierarchical plan with dependencies."""
    
    id: str
    description: str
    level: int = 0  # Hierarchy level (0 = top-level)
    parent_id: Optional[str] = None
    children: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    dependency_type: DependencyType = DependencyType.SEQUENTIAL
    status: PlanStatus = PlanStatus.PENDING
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    result: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict = field(default_factory=dict)
    estimated_duration: Optional[float] = None  # in seconds
    actual_duration: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Generate ID if not provided."""
        if not self.id:
            self.id = hashlib.md5(self.description.encode()).hexdigest()[:8]
    
    def can_execute(self, completed_items: set[str]) -> bool:
        """Check if all dependencies are satisfied.
        
        Args:
            completed_items: Set of completed item IDs.
            
        Returns:
            True if all dependencies are met.
        """
        if self.status != PlanStatus.PENDING:
            return False
        
        # Check all dependencies are completed
        for dep_id in self.dependencies:
            if dep_id not in completed_items:
                return False
        
        return True
    
    def mark_started(self) -> None:
        """Mark item as started."""
        self.status = PlanStatus.IN_PROGRESS
        self.started_at = datetime.now()
    
    def mark_completed(self, result: Optional[str] = None) -> None:
        """Mark item as completed."""
        self.status = PlanStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        if self.started_at:
            self.actual_duration = (self.completed_at - self.started_at).total_seconds()
    
    def mark_failed(self, error: str) -> None:
        """Mark item as failed."""
        self.status = PlanStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()
        if self.started_at:
            self.actual_duration = (self.completed_at - self.started_at).total_seconds()
    
    def should_retry(self) -> bool:
        """Check if item should be retried."""
        return self.retry_count < self.max_retries
    
    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retry_count += 1
        self.status = PlanStatus.PENDING
        self.error = None
        self.started_at = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "level": self.level,
            "parent_id": self.parent_id,
            "children": self.children,
            "dependencies": self.dependencies,
            "dependency_type": self.dependency_type.value,
            "status": self.status.value,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PlanItem":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            level=data.get("level", 0),
            parent_id=data.get("parent_id"),
            children=data.get("children", []),
            dependencies=data.get("dependencies", []),
            dependency_type=DependencyType(data.get("dependency_type", "sequential")),
            status=PlanStatus(data.get("status", "pending")),
            tool_name=data.get("tool_name"),
            tool_args=data.get("tool_args"),
            result=data.get("result"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
            estimated_duration=data.get("estimated_duration"),
            actual_duration=data.get("actual_duration"),
        )


@dataclass
class HierarchicalPlan:
    """Represents a hierarchical plan with multiple levels and dependencies."""
    
    title: str
    items: dict[str, PlanItem] = field(default_factory=dict)
    root_items: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def add_item(self, item: PlanItem) -> None:
        """Add a plan item."""
        self.items[item.id] = item
        if item.parent_id is None and item.id not in self.root_items:
            self.root_items.append(item.id)
        elif item.parent_id:
            parent = self.items.get(item.parent_id)
            if parent and item.id not in parent.children:
                parent.children.append(item.id)
        self.updated_at = datetime.now()
    
    def get_item(self, item_id: str) -> Optional[PlanItem]:
        """Get a plan item by ID."""
        return self.items.get(item_id)
    
    def get_executable_items(self) -> list[PlanItem]:
        """Get items that are ready to execute (all dependencies met)."""
        completed_ids = {
            item_id for item_id, item in self.items.items()
            if item.status == PlanStatus.COMPLETED
        }
        
        executable = []
        for item in self.items.values():
            if item.can_execute(completed_ids):
                executable.append(item)
        
        return executable
    
    def get_pending_items(self) -> list[PlanItem]:
        """Get all pending items."""
        return [
            item for item in self.items.values()
            if item.status == PlanStatus.PENDING
        ]
    
    def get_completed_items(self) -> list[PlanItem]:
        """Get all completed items."""
        return [
            item for item in self.items.values()
            if item.status == PlanStatus.COMPLETED
        ]
    
    def get_failed_items(self) -> list[PlanItem]:
        """Get all failed items."""
        return [
            item for item in self.items.values()
            if item.status == PlanStatus.FAILED
        ]
    
    def is_complete(self) -> bool:
        """Check if all items are completed or skipped."""
        return all(
            item.status in (PlanStatus.COMPLETED, PlanStatus.SKIPPED)
            for item in self.items.values()
        )
    
    def has_failures(self) -> bool:
        """Check if any items have failed."""
        return any(item.status == PlanStatus.FAILED for item in self.items.values())
    
    def create_checkpoint(self, description: str, state_snapshot: dict, 
                         plan_item_id: Optional[str] = None) -> Checkpoint:
        """Create a checkpoint for potential rollback."""
        checkpoint = Checkpoint(
            id=hashlib.md5(f"{datetime.now().isoformat()}{description}".encode()).hexdigest()[:8],
            timestamp=datetime.now(),
            state_snapshot=state_snapshot,
            description=description,
            plan_item_id=plan_item_id
        )
        self.checkpoints.append(checkpoint)
        logger.info(f"Created checkpoint: {checkpoint.id} - {description}")
        return checkpoint
    
    def get_last_checkpoint(self, before_item_id: Optional[str] = None) -> Optional[Checkpoint]:
        """Get the last checkpoint, optionally before a specific item."""
        if not self.checkpoints:
            return None
        
        if before_item_id:
            relevant = [
                cp for cp in self.checkpoints
                if cp.plan_item_id != before_item_id
            ]
            return relevant[-1] if relevant else None
        
        return self.checkpoints[-1]
    
    def get_progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        if not self.items:
            return 0.0
        
        completed = len(self.get_completed_items())
        total = len(self.items)
        return (completed / total) * 100
    
    def get_estimated_remaining_time(self) -> float:
        """Estimate remaining time based on actual durations."""
        remaining = 0.0
        completed_durations = []
        
        for item in self.items.values():
            if item.actual_duration:
                completed_durations.append(item.actual_duration)
            elif item.status == PlanStatus.PENDING and item.estimated_duration:
                remaining += item.estimated_duration
        
        # Use average actual duration for items without estimates
        if completed_durations and remaining == 0:
            avg_duration = sum(completed_durations) / len(completed_durations)
            pending_count = len(self.get_pending_items())
            remaining = avg_duration * pending_count
        
        return remaining
    
    def to_dict(self) -> dict:
        """Serialize plan to dictionary."""
        return {
            "title": self.title,
            "items": {k: v.to_dict() for k, v in self.items.items()},
            "root_items": self.root_items,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "HierarchicalPlan":
        """Deserialize plan from dictionary."""
        plan = cls(
            title=data["title"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )
        
        # Restore items
        for item_id, item_data in data["items"].items():
            plan.items[item_id] = PlanItem.from_dict(item_data)
        
        plan.root_items = data.get("root_items", [])
        plan.checkpoints = [Checkpoint.from_dict(cp) for cp in data.get("checkpoints", [])]
        
        return plan


class EnhancedPlanner:
    """Advanced planner with hierarchical planning, dependency tracking, and rollback support."""
    
    def __init__(self, model_config: ModelConfig) -> None:
        """Initialize the enhanced planner.
        
        Args:
            model_config: LLM model configuration.
        """
        self._client = LLMClient(model_config)
        self._current_plan: Optional[HierarchicalPlan] = None
        self._execution_callback: Optional[Callable[[PlanItem], None]] = None
    
    def set_execution_callback(self, callback: Callable[[PlanItem], None]) -> None:
        """Set a callback to be called after each item execution.
        
        Args:
            callback: Function to call with executed plan item.
        """
        self._execution_callback = callback
    
    def generate_hierarchical_plan(
        self,
        user_request: str,
        system_prompt: str,
        available_tools: list[dict],
        max_depth: int = 3
    ) -> HierarchicalPlan:
        """Generate a hierarchical plan with multiple levels of detail.
        
        Args:
            user_request: The user's request.
            system_prompt: System prompt for context.
            available_tools: List of available tool schemas.
            max_depth: Maximum depth of hierarchy.
            
        Returns:
            Generated hierarchical plan.
        """
        logger.info(f"Generating hierarchical plan for: {user_request[:50]}...")
        
        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=f"""Analyze this complex task and create a hierarchical plan with multiple levels.

User Request: {user_request}

Available tools: {[t['function']['name'] for t in available_tools]}

Create a hierarchical plan breaking down the task into manageable steps.
Organize steps into phases/groups (top level) with detailed sub-steps.

Respond with a JSON object with this structure:
{{
    "title": "Plan title",
    "phases": [
        {{
            "name": "Phase 1 name",
            "steps": [
                {{"description": "Step description", "tool": "tool_name_or_null", "estimated_minutes": 5}},
                ...
            ]
        }},
        ...
    ],
    "dependencies": [
        {{"step": "step_description", "depends_on": ["other_step_description"]}}
    ]
}}

Consider:
- Group related steps into phases
- Identify dependencies between steps
- Estimate duration for each step
- Mark which steps can run in parallel

Return ONLY the JSON object.""")
        ]
        
        try:
            content, _ = self._client.chat(messages, tools=None)
            
            # Parse JSON response
            import json
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                plan_data = json.loads(content[start_idx:end_idx])
                return self._build_hierarchical_plan(plan_data, max_depth)
            else:
                logger.warning("Could not parse JSON, creating simple plan")
                return self._create_simple_plan(user_request)
                
        except Exception as e:
            logger.error(f"Failed to generate hierarchical plan: {e}")
            return self._create_simple_plan(user_request)
    
    def _build_hierarchical_plan(self, plan_data: dict, max_depth: int) -> HierarchicalPlan:
        """Build hierarchical plan structure from parsed data."""
        plan = HierarchicalPlan(title=plan_data.get("title", "Execution Plan"))
        
        # Build dependency map
        dep_map = {}
        for dep in plan_data.get("dependencies", []):
            step = dep.get("step")
            depends_on = dep.get("depends_on", [])
            dep_map[step] = depends_on
        
        # Create phase items (level 0)
        for phase_idx, phase in enumerate(plan_data.get("phases", [])):
            phase_id = f"phase_{phase_idx}"
            phase_item = PlanItem(
                id=phase_id,
                description=phase.get("name", f"Phase {phase_idx + 1}"),
                level=0
            )
            plan.add_item(phase_item)
            
            # Create step items (level 1)
            for step_idx, step in enumerate(phase.get("steps", [])):
                step_desc = step.get("description", f"Step {step_idx + 1}")
                step_id = f"{phase_id}_step_{step_idx}"
                
                # Find dependencies
                step_deps = []
                for desc, deps in dep_map.items():
                    if desc == step_desc:
                        # Find corresponding step IDs
                        for dep_desc in deps:
                            for other_phase_idx, other_phase in enumerate(plan_data.get("phases", [])):
                                for other_step_idx, other_step in enumerate(other_phase.get("steps", [])):
                                    if other_step.get("description") == dep_desc:
                                        step_deps.append(f"phase_{other_phase_idx}_step_{other_step_idx}")
                
                step_item = PlanItem(
                    id=step_id,
                    description=step_desc,
                    level=1,
                    parent_id=phase_id,
                    dependencies=step_deps,
                    tool_name=step.get("tool"),
                    estimated_duration=step.get("estimated_minutes", 5) * 60
                )
                plan.add_item(step_item)
        
        logger.info(f"Built hierarchical plan with {len(plan.items)} items")
        return plan
    
    def _create_simple_plan(self, user_request: str) -> HierarchicalPlan:
        """Create a simple flat plan as fallback."""
        plan = HierarchicalPlan(title="Execution Plan")
        plan.add_item(PlanItem(
            id="step_1",
            description=user_request[:100],
            level=0
        ))
        return plan
    
    def execute_plan(
        self,
        plan: HierarchicalPlan,
        executor: Callable[[PlanItem], tuple[bool, str]],
        create_checkpoints: bool = True
    ) -> tuple[bool, str]:
        """Execute a plan with dependency tracking and optional checkpoints.
        
        Args:
            plan: The plan to execute.
            executor: Function to execute individual items. Returns (success, result/error).
            create_checkpoints: Whether to create checkpoints for rollback.
            
        Returns:
            Tuple of (success, message).
        """
        self._current_plan = plan
        logger.info(f"Starting plan execution: {plan.title}")
        
        max_iterations = len(plan.items) * 3  # Allow for retries
        iteration = 0
        
        while not plan.is_complete() and iteration < max_iterations:
            iteration += 1
            executable_items = plan.get_executable_items()
            
            if not executable_items:
                if plan.get_pending_items():
                    # Deadlock detected - pending items but none executable
                    logger.error("Deadlock detected: pending items with unmet dependencies")
                    return False, "Deadlock: Cannot proceed due to unmet dependencies"
                break
            
            # Execute items (could be parallelized for PARALLEL dependency type)
            for item in executable_items:
                logger.info(f"Executing item {item.id}: {item.description[:50]}")
                
                # Create checkpoint before execution
                if create_checkpoints:
                    plan.create_checkpoint(
                        description=f"Before: {item.description[:50]}",
                        state_snapshot={"item_id": item.id, "status": item.status},
                        plan_item_id=item.id
                    )
                
                # Execute the item
                item.mark_started()
                success, result = executor(item)
                
                if success:
                    item.mark_completed(result)
                    logger.info(f"Item {item.id} completed successfully")
                else:
                    item.mark_failed(result)
                    logger.error(f"Item {item.id} failed: {result}")
                    
                    if item.should_retry():
                        logger.info(f"Retrying item {item.id} (attempt {item.retry_count + 1})")
                        item.increment_retry()
                        continue
                    else:
                        # Max retries reached
                        logger.error(f"Item {item.id} failed after {item.max_retries} retries")
                
                # Call execution callback
                if self._execution_callback:
                    self._execution_callback(item)
        
        # Check final status
        if plan.has_failures():
            failed = plan.get_failed_items()
            return False, f"Plan completed with {len(failed)} failures"
        
        return True, "Plan executed successfully"
    
    def rollback_to_checkpoint(
        self,
        plan: HierarchicalPlan,
        checkpoint_id: str
    ) -> bool:
        """Rollback plan state to a specific checkpoint.
        
        Args:
            plan: The plan to rollback.
            checkpoint_id: ID of checkpoint to rollback to.
            
        Returns:
            True if rollback successful.
        """
        checkpoint = None
        for cp in plan.checkpoints:
            if cp.id == checkpoint_id:
                checkpoint = cp
                break
        
        if not checkpoint:
            logger.error(f"Checkpoint {checkpoint_id} not found")
            return False
        
        logger.info(f"Rolling back to checkpoint {checkpoint_id}")
        
        # Rollback item states after the checkpoint
        for item in plan.items.values():
            if item.completed_at and item.completed_at > checkpoint.timestamp:
                item.status = PlanStatus.ROLLED_BACK
                item.result = None
                item.error = None
                item.completed_at = None
                item.started_at = None
                logger.info(f"Rolled back item {item.id}")
        
        return True
    
    def get_plan_summary(self, plan: HierarchicalPlan) -> str:
        """Generate a human-readable summary of plan status."""
        lines = [
            f"Plan: {plan.title}",
            f"Progress: {plan.get_progress_percentage():.1f}%",
            ""
        ]
        
        # Group by status
        by_status = {}
        for item in plan.items.values():
            status = item.status
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(item)
        
        # Sort by status value (enum order) instead of enum itself
        for status, items in sorted(by_status.items(), key=lambda x: x[0].value):
            if items:
                lines.append(f"\n{status.value.upper()} ({len(items)}):")
                for item in items:
                    indent = "  " * item.level
                    lines.append(f"{indent}- {item.description[:60]}")
                    if item.error:
                        lines.append(f"{indent}  Error: {item.error[:50]}")
        
        # Estimated remaining time
        remaining_time = plan.get_estimated_remaining_time()
        if remaining_time > 0:
            lines.append(f"\nEstimated time remaining: {remaining_time/60:.1f} minutes")
        
        return "\n".join(lines)
    
    def save_plan(self, plan: HierarchicalPlan, path: Path) -> None:
        """Save plan to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan.to_dict(), indent=2))
        logger.info(f"Saved plan to {path}")
    
    def load_plan(self, path: Path) -> Optional[HierarchicalPlan]:
        """Load plan from file."""
        if not path.exists():
            return None
        
        try:
            data = json.loads(path.read_text())
            plan = HierarchicalPlan.from_dict(data)
            logger.info(f"Loaded plan from {path}")
            return plan
        except Exception as e:
            logger.error(f"Failed to load plan: {e}")
            return None
