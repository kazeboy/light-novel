# context/architecture.md
> Claude reads this when working on pipeline logic, scraper sources, data flow, or AI integration.
> Keep accurate — an outdated architecture doc is worse than none.

---

## Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | Python 3.10+ | Type hints used on function signatures |
| Web Scraping | BeautifulSoup4 + lxml | Standard HTML parsing |
| Browser Automation | Playwright | For JavaScript-heavy / protected sites |
| HTTP | requests | For non-JS sites, with retry and delay logic |
| Ebook Generation | EbookLib | EPUB construction |
| Ebook Conversion | Calibre CLI (`ebook-convert`) | AZW3 output — external dependency |
| Japanese NLP | Janome | Morphological analysis for furigana |
| Terminal UI | rich | Output formatting (may expand) |
| Data Storage | JSON files on disk | No database — JSON archive is the source of truth |
| AI Layer | Planned — see below | `services/ai.py` (not yet implemented) |

---

## How Data Flows

```
Novel URL (user input)
        │
        ▼
sources/registry.py → matches URL to the correct BaseSource implementation
        │
        ▼
source.get_novel_metadata()     → Novel dataclass (title, author, cover_url, chapters)
source.get_chapter_list()       → List[ChapterRef]
        │
        ▼
services/metadata_fetcher.py    → NovelUpdates → MangaUpdates fallback (enriches metadata)
services/downloader.py          → downloads cover image
        │
        ▼
output/<source-slug>/
├── meta.json                   ← enriched metadata (local source of truth)
├── cover.jpg
└── chapters/
    ├── 0001.json               ← one file per chapter (index, title, text, html, url)
    └── ...
        │
        ▼
services/epub_builder.py        → reads JSON archive, builds EPUB
services/furigana.py            → optional: adds ruby/furigana markup to Japanese text
        │
        ▼
<source-slug>.epub
        │
        ▼
Calibre CLI (ebook-convert)     → <source-slug>.azw3
```

---

## Source Layer (`sources/`)

All scrapers extend `sources/base.py → BaseSource` (ABC) and must implement:

| Method | Purpose |
|---|---|
| `matches(url)` | Returns `True` if this source handles the given URL |
| `get_novel_metadata(url)` | Returns a `Novel` dataclass |
| `get_chapter_list(url)` | Returns `List[ChapterRef]` |
| `get_chapter_content(chapter_url)` | Returns a `ChapterContent` dataclass |

`sources/registry.py` holds a `SOURCES: List[BaseSource]` list. The first source whose `matches()` returns `True` wins. Order matters.

---

## Service Layer (`services/`)

Services transform and persist data. They never scrape. Key services:

| File | Responsibility |
|---|---|
| `downloader.py` | Saves meta/chapters to disk, downloads cover, handles retries |
| `normalizer.py` | Cleans raw HTML from scrapers |
| `epub_builder.py` | Builds EPUB from local JSON archive |
| `furigana.py` | Applies furigana ruby tags based on JLPT mode |
| `metadata_fetcher.py` | Fetches enriched metadata from NovelUpdates / MangaUpdates |
| `ordering.py` | Deduplicates and sorts chapter lists |

---

## Data Models (`models/schemas.py`)

Three `@dataclass` models used throughout the pipeline:

- `ChapterRef` — lightweight reference (title, url, chapter_number)
- `ChapterContent` — full chapter (title, text, html, url, chapter_number)
- `Novel` — novel metadata + chapter list (title, author, description, cover_url, chapters)

---

## Furigana / JLPT System

`services/furigana.py` processes Japanese text using Janome tokenizer.

| Mode string | Meaning |
|---|---|
| `none` | No furigana |
| `all` | Furigana on all kanji |
| `n4` | Furigana on kanji above JLPT N5 (i.e. N4 and harder) |
| `n3` | Furigana on kanji above JLPT N4 |
| `n2` | Furigana on kanji above JLPT N3 |
| `n1` | Furigana on kanji above JLPT N2 |
| `rare` | Furigana only on non-JLPT kanji |

Kanji reference data lives in `data/jlpt_kanji/n1.txt` through `n5.txt` — sourced from the KanjiTools project. Never auto-modify these files.

---

## Planned AI Layer

AI capabilities are on the roadmap. When implementing, follow these conventions:

- All AI/LLM calls go in **`services/ai.py`** — keep AI logic isolated from scraping and EPUB building
- Likely use cases: chapter summaries (attach to chapter JSON), translation pipeline (new field in ChapterContent), vocabulary extraction (new JLPT study mode)
- API key configuration should live in `config.py` (currently a placeholder)
- Use an environment variable (`ANTHROPIC_API_KEY` or similar) — never hardcode keys
- Return `None` on API failure — don't crash the pipeline over an optional AI step

---

## External Services & APIs

| Service | Purpose | Notes |
|---|---|---|
| NovelUpdates | Primary metadata source | Scraped (no official API) |
| MangaUpdates | Fallback metadata source | Scraped (no official API) |
| Calibre CLI | EPUB → AZW3 conversion | Must be installed locally |
| AI provider (planned) | Chapter summaries / translation | `services/ai.py` |

---

## Key Design Decisions

- **JSON archive as source-of-truth**: chapters are saved as individual JSON files before EPUB building. This allows rebuild without re-scraping and makes the pipeline resumable at any step.
- **URL-slug for folder names**: avoids filesystem and encoding issues with Japanese/special titles. The title lives inside the ebook metadata, not the filename.
- **Calibre for AZW3**: battle-tested conversion tool, avoids reimplementing Kindle format support.
- **No database**: this is a personal CLI tool — flat JSON files are portable, zero-setup, and easy to inspect.

---

## Off-Limits (Never Touch Without Explicit Instruction)

- `data/jlpt_kanji/*.txt` — authoritative JLPT kanji lists
- `output/` — generated ebook files
- `config.py` — currently a placeholder; don't add logic without discussion

---

*Last updated: 2026-04-11*
