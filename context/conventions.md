# context/conventions.md
> Claude reads this before creating new files, functions, or classes.
> Consistency is the goal — if in doubt, match existing patterns.

---

## File & Folder Naming

| Type | Convention | Example |
|---|---|---|
| Python files | `snake_case` | `epub_builder.py`, `metadata_fetcher.py` |
| Folders | `snake_case` | `sources/`, `services/`, `models/` |
| Classes | `PascalCase` | `BaseSource`, `ChapterRef`, `NovelFullSource` |
| Functions | `snake_case` | `get_chapter_list()`, `apply_furigana()` |
| Constants (module-level) | `UPPER_SNAKE_CASE` | `KANJI_RE`, `JLPT_N5`, `KNOWN_KANJI_BY_MODE` |
| Local variables | `snake_case` | `chapter_index`, `source_url` |

---

## Docstrings

Every function must have a docstring. Format: one sentence describing **what it does** and **when it is called**.

```python
# ✅ Good
def load_meta(folder: str) -> dict:
    """
    Load the saved metadata dictionary from meta.json in a novel output folder.
    Used by the EPUB builder and rebuild flow as the local source of truth for book metadata.
    """

# ❌ Bad — missing docstring, or just restating the name
def load_meta(folder: str) -> dict:
    return json.load(...)
```

---

## Type Hints

Use type hints on all function parameters and return values. Import from `typing` for compatibility.

```python
# ✅ Good
from typing import List, Optional

def get_chapter_list(self, url: str) -> List[ChapterRef]:
    ...

def find_cover(meta: dict) -> Optional[str]:
    ...

# ❌ Bad — untyped
def get_chapter_list(self, url):
    ...
```

Use `@dataclass` for data models — see `models/schemas.py` as the reference pattern.

---

## Imports

Order: **stdlib → third-party → internal**. Blank line between each group.

```python
# ✅ Good
import os
import json
from typing import List, Optional

from bs4 import BeautifulSoup
from slugify import slugify

from models.schemas import Novel, ChapterRef
from services.normalizer import clean_html
```

---

## Source Pattern

Every new scraper must:
1. Live in `sources/<site_name>.py`
2. Extend `BaseSource` from `sources/base.py`
3. Implement all four abstract methods: `matches`, `get_novel_metadata`, `get_chapter_list`, `get_chapter_content`
4. Be added to the `SOURCES` list in `sources/registry.py`

```python
# ✅ Good — follows the pattern
from sources.base import BaseSource
from models.schemas import Novel, ChapterRef, ChapterContent

class NewSiteSource(BaseSource):
    def matches(self, url: str) -> bool:
        return "newsite.com" in url

    def get_novel_metadata(self, url: str) -> Novel:
        ...

    def get_chapter_list(self, url: str) -> List[ChapterRef]:
        ...

    def get_chapter_content(self, chapter_url: str) -> ChapterContent:
        ...
```

**Rule**: No scraping logic inside `services/`. No EPUB or file-writing logic inside `sources/`.

---

## Service Pattern

Services take data in and return data out — or persist it to disk. They do not scrape.

Functions should be small and focused (aim for under 50 lines). If a function is doing multiple distinct things, split it.

```python
# ✅ Good — one responsibility
def build_cover_page(lang: str = "en") -> epub.EpubHtml:
    """
    Build a dedicated XHTML cover page for the EPUB using the embedded cover image.
    Used by the EPUB builder so readers open on a real cover page instead of metadata only.
    """
    ...
```

---

## Error Handling

This is a CLI tool. Broad `try/except` with `print()` is acceptable for now.

```python
# ✅ Current pattern
try:
    chapter = source.get_chapter_content(ch.url)
    ...
except Exception as e:
    print(f"Failed chapter {i}: {ch.title}")
    print(f"Error: {e}")
    failed_count += 1
```

When the AI layer is added, failures in `services/ai.py` should return `None` gracefully — never crash the main pipeline over an optional enrichment step.

---

## Furigana Modes — Always Use String Names

The 7 furigana mode values are strings. Never use integer indexes in code.

```python
# ✅ Good
furigana_mode = "n3"
apply_furigana(text, "all")

# ❌ Bad
apply_furigana(text, 3)
```

Valid values: `"none"`, `"all"`, `"n4"`, `"n3"`, `"n2"`, `"n1"`, `"rare"`

---

## config.py

`config.py` is currently a placeholder. Any future configurable values (API keys, default paths, feature flags) go here. Import from `config` rather than hardcoding values in service files.

---

## Testing

No test suite currently. When tests are added:
- Co-locate with source files as `test_<module>.py`
- Use `pytest`
- Do not mock the file system — use temporary directories

---

## Git & Commits

Conventional commits preferred:

```
feat: add novelfull source with Playwright support
fix: handle missing cover URL in metadata fetcher
refactor: extract chapter ordering into services/ordering.py
docs: update CLAUDE.md with AI layer plan
chore: add novelfull to .claudeignore
```

---

*Last updated: 2026-04-11*
