# Small LLM Compatibility Fixes (e.g., Qwen2.5:3b)

This document summarizes the fixes applied to make the coding agent work better with small language models like Qwen2.5:3b.

## Summary of Changes

### 1. Model Configuration (`coding_agent/config/model_config.py`)

**Added sampling parameters for better control:**
- `temperature: float = 0.2` - Lower temperature for more deterministic output (range 0-2)
- `top_p: float = 0.9` - Nucleus sampling parameter (range 0-1)

These parameters help small models produce more consistent and reliable outputs, especially for structured tasks like tool calling and JSON generation.

**Usage:**
```python
config = ModelConfig(
    model_name="qwen2.5:3b",
    temperature=0.2,  # Low for deterministic output
    top_p=0.9
)
```

### 2. LLM Client (`coding_agent/llm/client.py`)

**Updated payload building to include sampling parameters:**
```python
payload = {
    "model": self.config.model_name,
    "messages": [...],
    "max_tokens": self.config.max_tokens,
    "stream": stream,
    "temperature": self.config.temperature,  # NEW
    "top_p": self.config.top_p,              # NEW
}
```

**Existing robust tool call parsing already handles:**
- Markdown code blocks with/without language tags
- Plain JSON objects
- Triple-quoted strings (common small model mistake)
- Unescaped newlines in string values

### 3. Plan Generation (`coding_agent/core/planner.py`)

**Simplified prompts for small models:**
- Shorter, more direct instructions
- Concrete JSON format examples
- Clear rules instead of abstract guidance
- Removed verbose explanations

**Before:** 200+ word prompt with abstract instructions
**After:** ~80 word prompt with concrete example

### 4. Hierarchical Plan Generation (`coding_agent/core/enhanced_planner.py`)

**Similar simplifications:**
- Reduced complexity from nested structures to flat phases
- Limited to 2-4 phases maximum
- Simplified dependency handling (empty by default)
- Clear formatting rules

## Best Practices for Small LLMs

### Recommended Settings

```bash
# Environment variables for Qwen2.5:3b
export LLM_MODEL="qwen2.5:3b"
export LLM_BASE_URL="http://localhost:11434/v1"
export LLM_API_KEY="ollama"
```

### Temperature Guidelines

- **0.0-0.3**: Code generation, tool calls, JSON output (deterministic)
- **0.3-0.5**: Planning, analysis (balanced)
- **0.5-0.7**: Creative tasks, brainstorming
- **0.7+**: Not recommended for small models

### Prompt Engineering Tips

1. **Be explicit about format**: Show exact JSON structure expected
2. **Use few-shot examples**: Include 1-2 concrete examples
3. **Keep instructions short**: Under 100 words when possible
4. **Avoid ambiguity**: Use "must" instead of "should"
5. **Limit options**: Don't ask for too many alternatives

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Malformed JSON | Lower temperature (0.1-0.2) |
| Missing tool calls | Explicit examples in prompt |
| Verbose responses | Add "Return ONLY..." instruction |
| Incorrect format | Show exact format in prompt |
| Hallucinated tools | List available tools explicitly |

## Testing

Run the test suite to verify compatibility:

```bash
python test_small_llm.py
```

All existing tests should pass:

```bash
pytest tests/ -x
```

## Future Improvements

Consider these additional optimizations:

1. **Function calling fine-tuning**: If using a custom model
2. **Prompt caching**: Reduce token usage for repeated patterns
3. **Output validation**: Stricter JSON schema validation
4. **Fallback strategies**: Graceful degradation on parse failures
5. **Model-specific presets**: Pre-configured settings per model

