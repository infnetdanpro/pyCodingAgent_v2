# Skills and Rules

This directory contains skills and rules that the coding agent will load and use as context when assisting with development tasks.

## How to Add Skills/Rules

1. Create a new Markdown file (`.md`) in this directory or in the `rules/` or `.agent/` directories
2. Write your guidelines, best practices, or rules in Markdown format
3. The agent will automatically load these files on startup

## Supported Directories

The agent scans for skill/rule files in:
- `skills/` - General skills and best practices
- `rules/` - Project-specific rules and conventions  
- `.agent/` - Agent-specific configuration and rules

## Example Files

- `python_best_practices.md` - Python coding standards
- `security_rules.md` - Security guidelines
- `api_conventions.md` - API design patterns

## File Naming

Files with keywords like "skill", "rule", "guide", "standard", "practice", or "convention" in their names will be automatically detected.
