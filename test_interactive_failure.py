#!/usr/bin/env python3
"""Test script demonstrating the interactive failure handling feature."""

from coding_agent.core import EnhancedPlanner, HierarchicalPlan, PlanStatus
from coding_agent.core.enhanced_planner import PlanItem as HierarchicalPlanItem
from coding_agent.config import ModelConfig


def test_auto_retry_mode():
    """Test auto-retry mode (non-interactive)."""
    print("\n" + "="*60)
    print("TEST 1: Auto-Retry Mode (non-interactive)")
    print("="*60)
    
    plan = HierarchicalPlan(title='Auto-Retry Test Plan')
    plan.add_item(HierarchicalPlanItem(id='task1', description='Task 1 - Will fail then retry', level=0))
    plan.add_item(HierarchicalPlanItem(id='task2', description='Task 2 - Always succeeds', level=0))
    
    # Track number of failures for task1
    fail_count = [0]
    
    def test_executor(item):
        if item.id == 'task1' and fail_count[0] < 1:
            fail_count[0] += 1
            return False, f'Simulated transient failure (attempt {fail_count[0]})'
        return True, f'Completed {item.description}'
    
    model_config = ModelConfig()
    planner = EnhancedPlanner(model_config)
    
    success, message = planner.execute_plan(
        plan, 
        test_executor, 
        interactive_on_failure=False
    )
    
    print(f"\nResult: Success={success}, Message='{message}'")
    print(f"Task1 status: {plan.get_item('task1').status}")
    print(f"Task2 status: {plan.get_item('task2').status}")
    
    assert success == True, "Plan should succeed after retry"
    assert plan.get_item('task1').status == PlanStatus.COMPLETED
    print("\n✓ Auto-retry mode works correctly!")


def test_persistent_failure_mode():
    """Test what happens when a task persistently fails."""
    print("\n" + "="*60)
    print("TEST 2: Persistent Failure Mode")
    print("="*60)
    
    plan = HierarchicalPlan(title='Persistent Failure Test Plan')
    plan.add_item(HierarchicalPlanItem(id='task1', description='Task 1 - Will always fail', level=0))
    plan.add_item(HierarchicalPlanItem(id='task2', description='Task 2 - Always succeeds', level=0))
    
    def test_executor(item):
        if item.id == 'task1':
            return False, 'Persistent failure - cannot recover'
        return True, f'Completed {item.description}'
    
    model_config = ModelConfig()
    planner = EnhancedPlanner(model_config)
    
    success, message = planner.execute_plan(
        plan, 
        test_executor, 
        interactive_on_failure=False
    )
    
    print(f"\nResult: Success={success}, Message='{message}'")
    print(f"Task1 status: {plan.get_item('task1').status}")
    print(f"Task2 status: {plan.get_item('task2').status}")
    
    # Show final plan summary
    print("\nFinal Plan Status:")
    print(planner.get_plan_summary(plan))
    
    assert success == False, "Plan should fail due to persistent failure"
    assert plan.get_item('task1').status == PlanStatus.FAILED
    print("\n✓ Persistent failure handling works correctly!")


def test_skip_functionality():
    """Test that tasks can be skipped."""
    print("\n" + "="*60)
    print("TEST 3: Skip Functionality")
    print("="*60)
    
    plan = HierarchicalPlan(title='Skip Test Plan')
    plan.add_item(HierarchicalPlanItem(id='task1', description='Task 1', level=0))
    plan.add_item(HierarchicalPlanItem(id='task2', description='Task 2', level=0))
    
    # Manually mark task1 as skipped
    task1 = plan.get_item('task1')
    task1.status = PlanStatus.SKIPPED
    
    def test_executor(item):
        return True, f'Completed {item.description}'
    
    model_config = ModelConfig()
    planner = EnhancedPlanner(model_config)
    
    success, message = planner.execute_plan(
        plan, 
        test_executor, 
        interactive_on_failure=False
    )
    
    print(f"\nResult: Success={success}, Message='{message}'")
    print(f"Task1 status: {plan.get_item('task1').status}")
    print(f"Task2 status: {plan.get_item('task2').status}")
    
    assert success == True, "Plan should succeed even with skipped task"
    assert plan.get_item('task1').status == PlanStatus.SKIPPED
    print("\n✓ Skip functionality works correctly!")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print(" ENHANCED PLANNER - INTERACTIVE FAILURE HANDLING TESTS")
    print("="*70)
    
    try:
        test_auto_retry_mode()
        test_persistent_failure_mode()
        test_skip_functionality()
        
        print("\n" + "="*70)
        print(" All tests passed successfully!")
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        raise


if __name__ == "__main__":
    main()
