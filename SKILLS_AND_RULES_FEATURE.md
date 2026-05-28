# Skills and Rules Feature

This feature allows you to add custom skills, rules, and guidelines as Markdown files that will be auto loaded by the coding agent and passed to the LLM as context b4 starting a session.

## How It Works

1. **File Discovery**: The agent scans for `.md` files in designated dirs:
 - `skills/` - General skills and best practices
 - `rules/` - Project-specific rules and conventions
 - `.agent/` - Agent-specific config and rules

2. **auto Loading**: When the agent starts w/ `prepare_contextTrue`, it:
 - Finds all skill/rule Markdown files
 - Loads their content
 - Formats them into a structured context section
 - Appends this to the session context sent to the LLM

3. **Context Integration**: The skills context is added after the standard session context (which includes env info, project files, deps, etc.) and b4 the 1st user query.

## dir Structure

```
/workspace
 skills/
 python_best_practices.md
 testing_guidelines.md
 rules/
 security_rules.md
 api_conventions.md
 .agent/
 custom_instructions.md
```

## Creating Skill/Rule Files

### ex: `skills/python_best_practices.md`

```
# Python Best Practices

## Code Style
- Always use 4 spaces for indentation
- Follow PEP 8 naming conventions
- Use type hints for all func params

## Error Handling
- Never use bare except clauses
- Always log errors w/ appropriate context
- Use specific exception types
```

### ex: `rules/security_rules.md`

```
# sec Rules

## auth
- Never hardcode creds or API keys
- Use env vars for sensitive config

## Data Validation
- Validate all user inputs b4 processing
- Use parameterized queries to prevent SQL injection
```

## File Naming Conventions

Files are auto detected if they contain keywords like:
- `skill`
- `rule`
- `guide`
- `standard`
- `practice`
- `convention`

README files in skill dirs are auto excluded.

## Programmatic Usage

### Using the SkillsLoader directly:

```
from coding_agent.core.skills_loader import SkillsLoader

loader SkillsLoader(workspace_dir"/path/to/project")

# Find all skill files
files loader.find_skill_files()

# Load all skills
skills loader.load_all_skills()

# Get formatted context for LLM
context loader.get_skills_context()
print(context)
```

### Using the convenience func:

```
from coding_agent.core.skills_loader import load_skills_context

context load_skills_context(workspace_dir"/path/to/project")
if context:
 print("Skills context loaded succ")
```

## Integration w/ CodingAgent

The skills loading is auto integrated into the `CodingAgent`:

```
from coding_agent.core import CodingAgent
from coding_agent.config import Settings, ModelConfig

settings Settings(workspace_dir"/path/to/project")
model_config ModelConfig()

# Skills are auto loaded when prepare_contextTrue (def)
agent CodingAgent(settingssettings, model_configmodel_config, prepare_contextTrue)

# The skills context is now part of the conversation context
context agent.get_context()
```

## Testing

Run the test suite:

```
pytest test_skills_loader.py -v
```

## Benefits

1. **Customization**: Tailor the agent's behavior to your team's coding standards
2. **Consistency**: Ensure the agent follows your project's specific conventions
3. **sec**: Enforce sec best practices auto
4. **Documentation**: Keep guidelines in ver-controlled Markdown files
5. **Flexibility**: Easy to update and maintain w/o code changes

## Troubleshooting

### Skills not loading?

1. Check that files are in the correct dirs (`skills/`, `rules/`, or `.agent/`)
2. Ensure files have `.md` extension
3. Verify file names contain relevant keywords
4. Check logs for any loading errors

### Too much context?

- Remove or rename unnecessary skill files
- Consolidate related rules into fewer files
- Consider using more specific keywords in file names
