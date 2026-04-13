# CLAUDE.md
> Keep this file under 200 lines. It's loaded on every message — only put essentials here.
> Detailed context is imported below and loaded automatically at session start.

---

## Core Identity

**Project:** light-novel — Python CLI tool that scrapes web novels and builds EPUB/AZW3 ebooks with Japanese JLPT study support
**Stack:** Python 3.10+ · BeautifulSoup4 · Playwright · EbookLib · Janome · Calibre CLI
**Owner:** Kazeboy

---

## Imported Context

@context/architecture.md
@context/conventions.md
@context/product.md

---

## Non-Negotiables

- Never modify: `data/jlpt_kanji/` — these are authoritative reference files, not generated
- Never modify: `output/`, `temp/` — generated content, not source code
- Always: read `context/architecture.md` before touching pipeline logic, scrapers, or data flow
- Always: read `context/conventions.md` before creating new files or functions
- Always: plan first on any task involving more than 1 file

---

## Quick Reference

### Data Flow
JSON archive in `output/<source-slug>/chapters/` is the local source of truth. The pipeline always reads from here when building EPUB — never re-scrapes unless explicitly asked.

### Sources
All scrapers live in `sources/` and extend `BaseSource` (sources/base.py). Every new source must be registered in `sources/registry.py` to be discoverable. Do not add scraping logic inside `services/`.

### Furigana / JLPT
7 string modes: `none`, `all`, `n4`, `n3`, `n2`, `n1`, `rare`. Always pass mode as a string — never use integer indexes. Logic lives in `services/furigana.py`. JLPT kanji data is in `data/jlpt_kanji/` (read-only).

### AI Layer (planned)
AI features (chapter summaries, translation) are on the roadmap. Any AI/LLM service code belongs in `services/ai.py`. Read `context/architecture.md` for the planned integration points before starting any AI work.

### File Naming
`snake_case` for files and folders, `PascalCase` for classes, `UPPER_SNAKE_CASE` for module-level constants.

---

## Hard Rules

1. One file, one responsibility — `sources/` fetch, `services/` transform, never mix
2. Plan before build — propose approach before writing code on any multi-file task
3. Explicit over implicit — name things clearly, no magic constants
4. No premature abstraction — duplicate until a pattern proves itself, then extract
5. Docstring every function — one-liner that describes what it does and when it's called
6. If unsure, ask — especially before touching the EPUB builder or furigana pipeline

---

## Off-Limits

- `data/jlpt_kanji/*.txt` — authoritative JLPT kanji lists, sourced from KanjiTools project
- `output/` — generated ebook files
- `temp/` — scratch files
- `.venv/` — Python environment

---

## Available Skills

Invoke with `/skill-name` or describe the task and Claude will load the right one:

- `/add-source` — scaffold a new novel scraper source
- `/debug-scraper` — diagnose and fix scraping failures
- `/add-jlpt-feature` — extend Japanese language and JLPT study features

---

*Last updated: 2026-04-13*
