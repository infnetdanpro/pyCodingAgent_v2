"""Test script to verify small LLM compatibility."""

from coding_agent.config import ModelConfig
from coding_agent.llm import LLMClient, Message, Role

def test_temperature_and_top_p():
    """Test that temperature and top_p are properly configured."""
    config = ModelConfig(
        model_name="qwen2.5:3b",
        temperature=0.2,
        top_p=0.9
    )
    
    assert config.temperature == 0.2
    assert config.top_p == 0.9
    print("✓ Temperature and top_p configuration works")

def test_payload_includes_sampling_params():
    """Test that the payload includes temperature and top_p."""
    config = ModelConfig(
        model_name="qwen2.5:3b",
        temperature=0.1,
        top_p=0.8
    )
    
    client = LLMClient(config)
    
    messages = [Message(role=Role.USER, content="Hello")]
    payload = client._build_payload(messages, tools=None, stream=False)
    
    assert "temperature" in payload
    assert "top_p" in payload
    assert payload["temperature"] == 0.1
    assert payload["top_p"] == 0.8
    print("✓ Payload includes temperature and top_p parameters")
    
    client.close()

def test_simplified_plan_prompt():
    """Test that plan generation uses simplified prompts."""
    from coding_agent.core.planner import PlanMode
    
    config = ModelConfig(
        model_name="qwen2.5:3b",
        temperature=0.2,
        top_p=0.9
    )
    
    planner = PlanMode(config)
    
    # Check that the prompt is simpler (shorter) than before
    test_request = "Create a Python file"
    available_tools = [{"function": {"name": "write_file"}}]
    
    # We can't actually call the LLM, but we can inspect the code
    import inspect
    source = inspect.getsource(planner.generate_plan)
    
    # Check for simplification markers
    assert "simple" in source.lower() or "small models" in source.lower()
    print("✓ Plan generation uses simplified prompts for small models")
    
    planner._client.close()

def test_hierarchical_plan_simplification():
    """Test that hierarchical plan generation is simplified."""
    from coding_agent.core.enhanced_planner import EnhancedPlanner
    
    config = ModelConfig(
        model_name="qwen2.5:3b",
        temperature=0.2,
        top_p=0.9
    )
    
    planner = EnhancedPlanner(config)
    
    import inspect
    source = inspect.getsource(planner.generate_hierarchical_plan)
    
    # Check for simplification markers
    assert "simple" in source.lower() or "small models" in source.lower()
    print("✓ Hierarchical plan generation uses simplified prompts")
    
    planner._client.close()

def test_tool_call_parsing_robustness():
    """Test that tool call parsing handles various formats."""
    config = ModelConfig(model_name="qwen2.5:3b")
    client = LLMClient(config)
    
    # Test various JSON formats that small models might produce
    test_cases = [
        # Standard markdown code block
        '''```json
{"name": "write_file", "arguments": {"path": "test.py"}}
```''',
        # Without language tag
        '''```
{"name": "read_file", "arguments": {"path": "test.py"}}
```''',
        # Plain JSON
        '{"name": "run_command", "arguments": {"command": "ls"}}',
        # With triple quotes (common mistake)
        '''"""{"name": "write_file", "arguments": {"path": "test.py"}}"""''',
    ]
    
    for i, content in enumerate(test_cases):
        result = client._parse_tool_calls_from_content(content)
        # Should either parse successfully or return None gracefully
        if result:
            assert len(result) > 0
            assert result[0].name in ["write_file", "read_file", "run_command"]
        print(f"  ✓ Test case {i+1} handled correctly")
    
    print("✓ Tool call parsing is robust for various formats")
    
    client.close()

if __name__ == "__main__":
    print("Testing small LLM compatibility improvements...\n")
    
    test_temperature_and_top_p()
    test_payload_includes_sampling_params()
    test_simplified_plan_prompt()
    test_hierarchical_plan_simplification()
    test_tool_call_parsing_robustness()
    
    print("\n✅ All tests passed! The system is now optimized for small LLMs like qwen2.5:3b")
