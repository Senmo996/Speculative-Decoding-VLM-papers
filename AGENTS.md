# Repository Guidelines

## Project Structure & Module Organization

This repository tracks arXiv papers about speculative decoding for multimodal and vision-language models. The project is intentionally small:

- `main.py` contains the arXiv query, filtering logic, and README update routine.
- `README.md` is the generated paper index. Keep the `<!-- PAPERS_START -->` and `<!-- PAPERS_END -->` markers intact.
- `.github/workflows/daily_update.yml` runs the updater on a schedule and commits README changes.

There are currently no dedicated `tests/`, package modules, or static assets. If the automation grows, place tests under `tests/` and split reusable code into small Python modules.

## Build, Test, and Development Commands

- `python main.py` runs the updater locally and edits `README.md` if new matching papers are found.
- `python -m py_compile main.py` checks the script for syntax errors without running the arXiv request.
- `git diff README.md` reviews generated table changes before committing.

The script uses only Python standard library modules, so no dependency installation is required for normal use. GitHub Actions currently runs Python 3.9.

## Coding Style & Naming Conventions

Use Python 3 style with 4-space indentation. Keep constants in uppercase, such as `MUST_INCLUDE`, `ANY_INCLUDE`, and `README_FILE`. Use `snake_case` for functions and local variables. Prefer small functions that isolate one responsibility: query construction, filtering, parsing, and file updates.

Read and write text files with explicit UTF-8 encoding. Preserve Markdown table formatting and escape table-breaking characters in paper titles.

## Testing Guidelines

No formal test suite exists yet. For small edits, run `python -m py_compile main.py` and inspect `git diff README.md` after `python main.py`.

When adding tests, use `pytest` with files named `tests/test_*.py`. Prioritize coverage for `check_logic_strictly()`, duplicate arXiv ID handling, and README marker replacement.

## Commit & Pull Request Guidelines

Recent history uses automated paper-list commits like `Update papers list [skip ci]` and an occasional conventional style such as `ci(workflow): ...`. Use clear, scoped commit messages; reserve `[skip ci]` for generated paper-list updates.

Pull requests should explain the behavior change, list local verification commands, and include a README diff when paper table output changes. Link related issues when available.

## Security & Configuration Tips

Do not add secrets or tokens; the updater only needs public arXiv access and repository write permission in GitHub Actions. Keep scheduled workflow changes explicit, including the intended UTC cron timing.
