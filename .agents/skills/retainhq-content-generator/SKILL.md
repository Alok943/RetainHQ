---
name: retainhq-content-generator
description: >-
  Generates and curates JSON lesson content for RetainHQ roadmaps. Follows strict validation rules, auto-fixes errors, and manages the TODO list automatically.
---

# RetainHQ Content Generator

## Overview
This skill fully automates the creation of educational lesson content for RetainHQ. It reads the strict prompt guidelines, leverages the JSON schema, generates high-quality content (including required challenge blocks), validates the output using the project's validator, and ticks off completion in the TODO list.

## Workflow

When asked to generate content for a roadmap (e.g., `python-swe`), follow these steps precisely:

### 1. Read Constraints
- Use `view_file` to read `content/PROMPT.md` to understand the writing style, voice, and quality bar (e.g. use of aha moments, code walkthroughs).
- Use `view_file` to read `content/schema.json` to understand the exact structure the output must conform to. Pay special attention to the `challenge` block requirement enforced by the validation script.

### 2. Identify Pending Topics
- Use `view_file` to read `content/_TODO.md`. Identify the next incomplete topic `[ ]` that needs generating.
- If the roadmap TODO is not in `_TODO.md`, look at `backend/seed_{roadmap}.py` to find the `NODES` list.

### 3. Generate Content
- Generate the lesson content for the topic.
- You must create ONE JSON file per topic.
- Ensure all required fields from the schema are present, particularly the `challenge` block which must have `title`, `prompt`, and `solution`.
- Use `write_to_file` to save the file to `content/roadmaps/{roadmap}/{slug}.json`. 

### 4. Validation
- Use `run_command` to execute `python content/validate.py`.
- **Auto-Correction Loop:** If validation fails, carefully read the error output. Fix the exact fields in the JSON using `replace_file_content` or `multi_replace_file_content` and re-run `validate.py`. Repeat this up to 3 times. If it still fails, stop and ask the user for guidance.

### 5. Mark as Complete
- Once validation passes cleanly, use `replace_file_content` to mark the topic as complete `[x]` in `content/_TODO.md`.
- Report success to the user.

## Common Mistakes
- **Missing Challenge Block**: `schema.json` might not mark it as root-level required, but `validate.py` will fail if it's missing.
- **Bad Slugs in Prerequisites/Unlocks**: Ensure any slugs referenced in `prerequisites` and `unlocks` match exactly the filenames of other topics in the roadmap.
- **Skipping Validation**: Do not consider a topic finished until `python content/validate.py` outputs `All content valid. [OK]`.
