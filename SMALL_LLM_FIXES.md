# Small LLM Compatibility Fixes (e.g., Qwen2.5:3b)

This document summarizes the fixes applied to make the coding agent work better w/ small language models like Qwen2.5:3b.

## Summary of Changes

### 1. Model config (`coding_agent/config/model_config.py`)

**Added sampling params for better control:**
- `temperature: float 0.2` - Lower temperature for more deterministic output (range 0-2)
- `top_p: float 0.9` - Nucleus sampling parameter (range 0-1)

These params help small models produce more consistent and reliable outputs, esp for structured tasks like tool calling and JSON gen.

**Usage:**
```
config ModelConfig(
 model_name"qwen2.5:3b",
 temperature0.2, # Low for deterministic output
 top_p0.9
)
```

### 2. LLM Client (`coding_agent/llm/client.py`)

**Updated payload building to include sampling params:**
```
payload {
 "model": self.config.model_name,
 "msgs": [...],
 "max_tokens": self.config.max_tokens,
 "stream": stream,
 "temperature": self.config.temperature, # NEW
 "top_p": self.config.top_p, # NEW
}
```

**Existing strong tool call parsing already handles:**
- Markdown code blocks w//w/o language tags
- Plain JSON objects
- Triple-quoted strings (common small model mistake)
- Unescaped newlines in string values

### 3. Plan gen (`coding_agent/core/planner.py`)

**Simplified prompts for small models:**
- Shorter, more direct instructions
- Concrete JSON format exs
- Clear rules instead of abstract guidance
- Removed verbose explanations

**b4:** 200 word prompt w/ abstract instructions
**After:** 80 word prompt w/ concrete ex

### 4. Hierarchical Plan gen (`coding_agent/core/enhanced_planner.py`)

**Similar simplifications:**
- Reduced complexity from nested structures to flat phases
- Limited to 2-4 phases max
- Simplified dependency handling (empty by def)
- Clear formatting rules

## Best Practices for Small LLMs

### Recommended Settings

```
# env vars for Qwen2.5:3b
export LLM_MODEL"qwen2.5:3b"
export LLM_BASE_URL"http://localhost:11434/v1"
export LLM_API_KEY"ollama"
```

### Temperature Guidelines

- **0.0-0.3**: Code gen, tool calls, JSON output (deterministic)
- **0.3-0.5**: Planning, analysis (balanced)
- **0.5-0.7**: Creative tasks, brainstorming
- **0.7**: Not recommended for small models

### Prompt Engineering Tips

1. **Be explicit about format**: Show exact JSON structure expected
2. **Use few-shot exs**: Include 1-2 concrete exs
3. **Keep instructions short**: Under 100 words when possible
4. **Avoid ambiguity**: Use "must" instead of "should"
5. **Limit options**: Don't ask for too many alternatives

### Common Issues Solutions

| Issue | Solution |
| Malformed JSON | Lower temperature (0.1-0.2) |
| Missing tool calls | Explicit exs in prompt |
| Verbose resps | Add "Return ONLY..." instruction |
| Incorrect format | Show exact format in prompt |
| Hallucinated tools | List available tools explicitly |

## Testing

Run the test suite to verify compatibility:

```
python test_small_llm.py
```

All existing tests should pass:

```
pytest tests/ -x
```

## Future Improvements

Consider these addl optimizations:

1. **func calling fine-tuning**: If using a custom model
2. **Prompt caching**: Reduce token usage for repeated patterns
3. **Output validation**: Stricter JSON schema validation
4. **Fallback strategies**: Graceful degradation on parse failures
5. **Model-specific presets**: Pre-configured settings per model

