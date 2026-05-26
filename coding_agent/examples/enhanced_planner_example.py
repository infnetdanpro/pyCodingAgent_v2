"""Example usage of the Enhanced Planner with hierarchical planning, dependency tracking, and rollback support."""

import logging
from pathlib import Path
from datetime import datetime

from coding_agent.config import ModelConfig
from coding_agent.core import (
    EnhancedPlanner,
    HierarchicalPlan,
    HierarchicalPlanItem as PlanItem,
    PlanStatus,
    DependencyType,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_hierarchical_plan():
    """Demonstrate creating and executing a hierarchical plan manually."""
    
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Hierarchical Plan")
    print("="*60)
    
    # Create a hierarchical plan manually
    plan = HierarchicalPlan(title="Build Python Package")
    
    # Phase 1: Setup (Level 0)
    setup_phase = PlanItem(
        id="phase_1",
        description="Phase 1: Project Setup",
        level=0
    )
    plan.add_item(setup_phase)
    
    # Setup steps (Level 1)
    plan.add_item(PlanItem(
        id="phase_1_step_1",
        description="Create project directory structure",
        level=1,
        parent_id="phase_1",
        estimated_duration=60
    ))
    
    plan.add_item(PlanItem(
        id="phase_1_step_2",
        description="Initialize git repository",
        level=1,
        parent_id="phase_1",
        dependencies=["phase_1_step_1"],
        estimated_duration=30
    ))
    
    # Phase 2: Development (Level 0)
    dev_phase = PlanItem(
        id="phase_2",
        description="Phase 2: Development",
        level=0
    )
    plan.add_item(dev_phase)
    
    # Development steps (Level 1)
    plan.add_item(PlanItem(
        id="phase_2_step_1",
        description="Create main module file",
        level=1,
        parent_id="phase_2",
        dependencies=["phase_1_step_2"],
        estimated_duration=120
    ))
    
    plan.add_item(PlanItem(
        id="phase_2_step_2",
        description="Create test file",
        level=1,
        parent_id="phase_2",
        dependencies=["phase_2_step_1"],
        estimated_duration=90
    ))
    
    # Phase 3: Documentation (Level 0)
    docs_phase = PlanItem(
        id="phase_3",
        description="Phase 3: Documentation",
        level=0
    )
    plan.add_item(docs_phase)
    
    plan.add_item(PlanItem(
        id="phase_3_step_1",
        description="Write README.md",
        level=1,
        parent_id="phase_3",
        dependencies=["phase_2_step_1"],
        estimated_duration=60
    ))
    
    # Display plan structure
    print(f"\nPlan: {plan.title}")
    print(f"Total items: {len(plan.items)}")
    print(f"Root items: {plan.root_items}")
    
    # Show hierarchy
    print("\nHierarchy:")
    for root_id in plan.root_items:
        root_item = plan.get_item(root_id)
        if root_item:
            print(f"  {root_item.description}")
            for child_id in root_item.children:
                child = plan.get_item(child_id)
                if child:
                    deps = f" (depends on: {', '.join(child.dependencies)})" if child.dependencies else ""
                    print(f"    └─ {child.description}{deps}")
    
    return plan


def example_plan_execution_simulation():
    """Simulate plan execution with checkpoints and retry logic."""
    
    print("\n" + "="*60)
    print("EXAMPLE 2: Plan Execution Simulation")
    print("="*60)
    
    plan = example_basic_hierarchical_plan()
    
    # Simulate an executor function
    execution_log = []
    
    def mock_executor(item: PlanItem) -> tuple[bool, str]:
        """Mock executor that simulates success/failure."""
        logger.info(f"Executing: {item.description}")
        execution_log.append({
            "id": item.id,
            "description": item.description,
            "started_at": datetime.now().isoformat()
        })
        
        # Simulate occasional failure for demonstration
        if item.id == "phase_2_step_2" and item.retry_count == 0:
            return False, "Simulated failure - will retry"
        
        return True, f"Completed {item.description}"
    
    # Create planner and execute
    model_config = ModelConfig()  # Uses defaults
    planner = EnhancedPlanner(model_config)
    
    # Set up progress callback
    def on_item_completed(item: PlanItem):
        progress = plan.get_progress_percentage()
        print(f"  ✓ {item.description[:40]}... ({progress:.1f}% complete)")
    
    planner.set_execution_callback(on_item_completed)
    
    print("\nExecuting plan...")
    success, message = planner.execute_plan(plan, mock_executor, create_checkpoints=True)
    
    print(f"\nExecution {'succeeded' if success else 'failed'}: {message}")
    print(f"Checkpoints created: {len(plan.checkpoints)}")
    
    # Show final status
    print("\n" + planner.get_plan_summary(plan))
    
    return plan, planner


def example_rollback():
    """Demonstrate rollback functionality."""
    
    print("\n" + "="*60)
    print("EXAMPLE 3: Rollback to Checkpoint")
    print("="*60)
    
    plan, planner = example_plan_execution_simulation()
    
    if plan.checkpoints:
        # Get the second-to-last checkpoint
        checkpoint = plan.checkpoints[-2] if len(plan.checkpoints) > 1 else plan.checkpoints[0]
        
        print(f"\nRolling back to checkpoint: {checkpoint.id}")
        print(f"Checkpoint description: {checkpoint.description}")
        
        success = planner.rollback_to_checkpoint(plan, checkpoint.id)
        
        if success:
            print("Rollback successful!")
            print("\nStatus after rollback:")
            print(planner.get_plan_summary(plan))
        else:
            print("Rollback failed!")
    
    return plan


def example_save_load_plan():
    """Demonstrate saving and loading plans."""
    
    print("\n" + "="*60)
    print("EXAMPLE 4: Save and Load Plan")
    print("="*60)
    
    plan = example_basic_hierarchical_plan()
    
    # Save plan
    plan_path = Path("/tmp/example_plan.json")
    model_config = ModelConfig()
    planner = EnhancedPlanner(model_config)
    
    print(f"\nSaving plan to: {plan_path}")
    planner.save_plan(plan, plan_path)
    
    # Load plan
    print(f"Loading plan from: {plan_path}")
    loaded_plan = planner.load_plan(plan_path)
    
    if loaded_plan:
        print(f"\nLoaded plan: {loaded_plan.title}")
        print(f"Items: {len(loaded_plan.items)}")
        print(f"Checkpoints: {len(loaded_plan.checkpoints)}")
        
        # Verify it matches
        assert loaded_plan.title == plan.title
        assert len(loaded_plan.items) == len(plan.items)
        print("\n✓ Plan loaded successfully and matches original!")
    
    return loaded_plan


def example_dependency_resolution():
    """Demonstrate dependency resolution and parallel execution detection."""
    
    print("\n" + "="*60)
    print("EXAMPLE 5: Dependency Resolution")
    print("="*60)
    
    plan = HierarchicalPlan(title="Dependency Resolution Demo")
    
    # Create items with various dependencies
    plan.add_item(PlanItem(
        id="task_a",
        description="Task A (no dependencies)",
        level=0
    ))
    
    plan.add_item(PlanItem(
        id="task_b",
        description="Task B (no dependencies)",
        level=0
    ))
    
    plan.add_item(PlanItem(
        id="task_c",
        description="Task C (depends on A)",
        level=0,
        dependencies=["task_a"]
    ))
    
    plan.add_item(PlanItem(
        id="task_d",
        description="Task D (depends on A and B)",
        level=0,
        dependencies=["task_a", "task_b"]
    ))
    
    plan.add_item(PlanItem(
        id="task_e",
        description="Task E (depends on C and D)",
        level=0,
        dependencies=["task_c", "task_d"]
    ))
    
    print(f"\nPlan: {plan.title}")
    print(f"Total tasks: {len(plan.items)}")
    
    # Show which tasks can execute initially
    executable = plan.get_executable_items()
    print(f"\nInitially executable tasks ({len(executable)}):")
    for item in executable:
        print(f"  • {item.description}")
    
    # Simulate completing task A
    task_a = plan.get_item("task_a")
    if task_a:
        task_a.mark_completed("Done")
    
    # Now check what's executable
    executable = plan.get_executable_items()
    print(f"\nAfter completing Task A, executable tasks ({len(executable)}):")
    for item in executable:
        print(f"  • {item.description}")
    
    # Complete task B
    task_b = plan.get_item("task_b")
    if task_b:
        task_b.mark_completed("Done")
    
    # Now check what's executable
    executable = plan.get_executable_items()
    print(f"\nAfter completing Task B, executable tasks ({len(executable)}):")
    for item in executable:
        print(f"  • {item.description}")
    
    print("\nThis demonstrates how dependencies control execution order!")
    
    return plan


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print(" ENHANCED PLANNER EXAMPLES")
    print(" Demonstrating hierarchical planning, dependencies, and rollback")
    print("="*70)
    
    try:
        # Run examples
        example_basic_hierarchical_plan()
        example_plan_execution_simulation()
        example_rollback()
        example_save_load_plan()
        example_dependency_resolution()
        
        print("\n" + "="*70)
        print(" All examples completed successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
