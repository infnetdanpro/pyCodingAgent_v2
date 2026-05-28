# Skills and Rules

This dir contains skills and rules that the coding agent will load and use as context when assisting w/ dev tasks.

## How to Add Skills/Rules

1. mk a new Markdown file (`.md`) in this dir or in the `rules/` or `.agent/` dirs
2. Write your guidelines, best practices, or rules in Markdown format
3. The agent will auto load these files on startup

## Supported dirs

The agent scans for skill/rule files in:
- `skills/` - General skills and best practices
- `rules/` - Project-specific rules and conventions
- `.agent/` - Agent-specific config and rules

## ex Files

- `python_best_practices.md` - Python coding standards
- `security_rules.md` - sec guidelines
- `api_conventions.md` - API design patterns

## File Naming

Files w/ keywords like "skill", "rule", "guide", "standard", "practice", or "convention" in their names will be auto detected.
