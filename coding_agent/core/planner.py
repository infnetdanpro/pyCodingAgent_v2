"""Plan mode implementation for the coding agent."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from ..llm import LLMClient, Message, Role
from ..config import ModelConfig

logger = logging.getLogger(__name__)


@dataclass
class PlanItem:
    """Represents a single item in a plan."""
    
    description: str
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    completed: bool = False
    enabled: bool = True
    
    def __str__(self) -> str:
        status = "✓" if self.completed else ("☐" if self.enabled else "☒")
        return f"[{status}] {self.description}"


@dataclass
class Plan:
    """Represents a complete plan with multiple items."""
    
    title: str
    items: list[PlanItem] = field(default_factory=list)
    
    def add_item(self, description: str, tool_name: Optional[str] = None, 
                 tool_args: Optional[dict] = None) -> None:
        """Add a plan item."""
        self.items.append(PlanItem(
            description=description,
            tool_name=tool_name,
            tool_args=tool_args
        ))
    
    def get_enabled_items(self) -> list[PlanItem]:
        """Get only enabled items."""
        return [item for item in self.items if item.enabled]
    
    def __str__(self) -> str:
        lines = [f"Plan: {self.title}", ""]
        for i, item in enumerate(self.items, 1):
            status = "✓" if item.completed else ("☐" if item.enabled else "☒")
            lines.append(f"  {i}. [{status}] {item.description}")
        return "\n".join(lines)


class PlanMode:
    """Handles plan mode functionality for the agent.
    
    In plan mode, the agent generates a plan first, allows user to review
    and modify it, then executes the approved plan.
    """
    
    def __init__(self, model_config: ModelConfig) -> None:
        """Initialize plan mode.
        
        Args:
            model_config: LLM model configuration.
        """
        self._client = LLMClient(model_config)
        self._current_plan: Optional[Plan] = None
    
    def generate_plan(self, user_request: str, system_prompt: str, 
                      available_tools: list[dict]) -> Plan:
        """Generate a plan based on user request.
        
        Args:
            user_request: The user's original request.
            system_prompt: System prompt for context.
            available_tools: List of available tool schemas.
        
        Returns:
            Generated plan.
        """
        logger.info(f"Generating plan for request: {user_request[:50]}...")
        
        # For small models, use simpler prompts with explicit formatting instructions
        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=f"""You are creating a step-by-step plan.

Task: {user_request}

Available tools: {[t['function']['name'] for t in available_tools]}

Create a simple JSON plan with this exact format:
{{
    "title": "Short title",
    "steps": [
        {{"description": "What to do", "tool": "tool_name or null"}},
        {{"description": "Next step", "tool": "tool_name or null"}}
    ]
}}

Rules:
- Keep steps short and clear
- Use null for steps without tools
- Return ONLY the JSON, no other text""")
        ]
        
        try:
            logger.info("Waiting for LLM to generate plan...")
            content, _ = self._client.chat(messages, tools=None)
            logger.info(f"Plan generation complete (response length: {len(content)})")
            
            # Parse the plan from response
            import json
            # Try to extract JSON from the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                plan_data = json.loads(content[start_idx:end_idx])
                
                plan = Plan(title=plan_data.get("title", "Execution Plan"))
                for step in plan_data.get("steps", []):
                    plan.add_item(
                        description=step.get("description", "Unknown step"),
                        tool_name=step.get("tool")
                    )
                
                self._current_plan = plan
                logger.info(f"Plan parsed successfully: {len(plan.items)} steps")
                return plan
            else:
                # Fallback: create a simple plan from the text
                logger.warning("Could not parse JSON from plan response, using fallback")
                plan = Plan(title="Execution Plan")
                plan.add_item(description=content[:200])
                self._current_plan = plan
                return plan
                
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            plan = Plan(title="Execution Plan")
            plan.add_item(description=f"Error generating plan: {e}")
            self._current_plan = plan
            return plan
    
    def get_current_plan(self) -> Optional[Plan]:
        """Get the current plan.
        
        Returns:
            Current plan or None if no plan exists.
        """
        return self._current_plan
    
    def update_plan_item(self, index: int, enabled: bool) -> bool:
        """Update a plan item's enabled status.
        
        Args:
            index: Index of the item to update (0-based).
            enabled: Whether the item should be enabled.
        
        Returns:
            True if successful, False otherwise.
        """
        if not self._current_plan:
            return False
        
        if 0 <= index < len(self._current_plan.items):
            self._current_plan.items[index].enabled = enabled
            return True
        return False
    
    def toggle_plan_item(self, index: int) -> bool:
        """Toggle a plan item's enabled status.
        
        Args:
            index: Index of the item to toggle (0-based).
        
        Returns:
            New enabled status.
        """
        if not self._current_plan:
            return False
        
        if 0 <= index < len(self._current_plan.items):
            self._current_plan.items[index].enabled = not self._current_plan.items[index].enabled
            return self._current_plan.items[index].enabled
        return False
    
    def clear_plan(self) -> None:
        """Clear the current plan."""
        self._current_plan = None
