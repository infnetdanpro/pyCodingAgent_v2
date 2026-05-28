# Skills and Rules Feature

This feature allows you to add custom skills, rules, and guidelines as Markdown files that will be automatically loaded by the coding agent and passed to the LLM as context before starting a session.

## How It Works

1. **File Discovery**: The agent scans for `.md` files in designated directories:
   - `skills/` - General skills and best practices
   - `rules/` - Project-specific rules and conventions
   - `.agent/` - Agent-specific configuration and rules

2. **Automatic Loading**: When the agent starts with `prepare_context=True`, it:
   - Finds all skill/rule Markdown files
   - Loads their content
   - Formats them into a structured context section
   - Appends this to the session context sent to the LLM

3. **Context Integration**: The skills context is added after the standard session context (which includes environment info, project files, dependencies, etc.) and before the first user query.

## Directory Structure

```
/workspace
├── skills/
│   ├── python_best_practices.md
│   └── testing_guidelines.md
├── rules/
│   ├── security_rules.md
│   └── api_conventions.md
└── .agent/
    └── custom_instructions.md
```

## Creating Skill/Rule Files

### Example: `skills/python_best_practices.md`

```markdown
# Python Best Practices

## Code Style
- Always use 4 spaces for indentation
- Follow PEP 8 naming conventions
- Use type hints for all function parameters

## Error Handling
- Never use bare except clauses
- Always log errors with appropriate context
- Use specific exception types
```

### Example: `rules/security_rules.md`

```markdown
# Security Rules

## Authentication
- Never hardcode credentials or API keys
- Use environment variables for sensitive configuration

## Data Validation
- Validate all user inputs before processing
- Use parameterized queries to prevent SQL injection
```

## File Naming Conventions

Files are automatically detected if they contain keywords like:
- `skill`
- `rule`
- `guide`
- `standard`
- `practice`
- `convention`

README files in skill directories are automatically excluded.

## Programmatic Usage

### Using the SkillsLoader directly:

```python
from coding_agent.core.skills_loader import SkillsLoader

loader = SkillsLoader(workspace_dir="/path/to/project")

# Find all skill files
files = loader.find_skill_files()

# Load all skills
skills = loader.load_all_skills()

# Get formatted context for LLM
context = loader.get_skills_context()
print(context)
```

### Using the convenience function:

```python
from coding_agent.core.skills_loader import load_skills_context

context = load_skills_context(workspace_dir="/path/to/project")
if context:
    print("Skills context loaded successfully")
```

## Integration with CodingAgent

The skills loading is automatically integrated into the `CodingAgent`:

```python
from coding_agent.core import CodingAgent
from coding_agent.config import Settings, ModelConfig

settings = Settings(workspace_dir="/path/to/project")
model_config = ModelConfig()

# Skills are automatically loaded when prepare_context=True (default)
agent = CodingAgent(settings=settings, model_config=model_config, prepare_context=True)

# The skills context is now part of the conversation context
context = agent.get_context()
```

## Testing

Run the test suite:

```bash
pytest test_skills_loader.py -v
```

## Benefits

1. **Customization**: Tailor the agent's behavior to your team's coding standards
2. **Consistency**: Ensure the agent follows your project's specific conventions
3. **Security**: Enforce security best practices automatically
4. **Documentation**: Keep guidelines in version-controlled Markdown files
5. **Flexibility**: Easy to update and maintain without code changes

## Troubleshooting

### Skills not loading?

1. Check that files are in the correct directories (`skills/`, `rules/`, or `.agent/`)
2. Ensure files have `.md` extension
3. Verify file names contain relevant keywords
4. Check logs for any loading errors

### Too much context?

- Remove or rename unnecessary skill files
- Consolidate related rules into fewer files
- Consider using more specific keywords in file names
