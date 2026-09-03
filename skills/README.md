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

---

## LLM Skills для малых моделей (Qwen 3B)

В этой папке реализованы 8 специализированных скиллов для эффективной работы с малыми LLM:

| № | Скилл | Файл | Назначение |
|---|-------|------|------------|
| 1 | **Chain-of-Thought** | `01_chain_of_thought.md` | Пошаговое мышление для сложных задач |
| 2 | **Context Optimization** | `02_context_optimization.md` | Приоритизация информации в ограниченном контексте |
| 3 | **Format Enforcement** | `03_format_enforcement.md` | Жёсткие шаблоны ответов |
| 4 | **Iterative Clarification** | `04_iterative_clarification.md` | Стратегия уточняющих вопросов |
| 5 | **Self-Correction** | `05_self_correction.md` | Чеклист самопроверки перед ответом |
| 6 | **Example-Driven** | `06_example_driven.md` | Обучение на примерах (Few-Shot) |
| 7 | **Task Decomposition** | `07_task_decomposition.md` | Декомпозиция сложных задач |
| 8 | **Knowledge Boundaries** | `08_knowledge_boundaries.md` | Декларация ограничений и уверенности |

### Ключевые принципы для малых LLM

- **Явная структура** вместо свободных рассуждений
- **Пошаговая декомпозиция** сложных задач
- **Конкретные примеры** кода и данных
- **Регулярная самопроверка** перед финальным ответом
- **Ограничение сложности** на один ответ

### Комбинирование скиллов

Для максимальной эффективности комбинируйте скиллы:

```
Сложная задача = Task Decomposition + Chain-of-Thought + Self-Correction
Код = Example-Driven + Format Enforcement + Self-Correction
Неоднозначный запрос = Iterative Clarification + Context Optimization
Фактологический вопрос = Knowledge Boundaries + Self-Correction
```

### Быстрый старт

1. Выберите скилл по типу задачи
2. Скопируйте шаблон промпта из файла
3. Адаптируйте под вашу задачу
4. При необходимости комбинируйте с другими скиллами
