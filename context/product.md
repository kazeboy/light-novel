# context/product.md
> Claude reads this to understand the "why" behind features — not just what to build, but who for.
> Helps avoid technically correct but product-wrong decisions.

---

## What This Project Is

**Name:** light-novel (lngrab)
**One-liner:** A personal CLI tool that scrapes web novels, builds EPUB/AZW3 ebooks, and adds Japanese JLPT study features for offline reading on Mac and Kindle.
**Status:** Active development — personal use, real production use for reading

---

## The Problem It Solves

Online light novel and web novel sites are ad-heavy, require constant internet, and don't support Kindle. Reading Japanese raw novels online doesn't allow for study-optimized formatting. This tool downloads novels to a local archive and produces clean ebooks with optional furigana for graded Japanese reading practice — no internet required after the initial download.

---

## Target Users

**Primary user:** Kazeboy — reading Japanese and English web novels offline on Mac (Apple Books) and Kindle. Also using it as a Japanese study aid by reading novels with JLPT-filtered furigana to learn kanji in context.

**Secondary users:** None — this is a personal tool, not designed for multi-user use.

---

## Core Features (MVP — all implemented)

1. **Multi-source scraping** — fetches from English translation sites (shmtranslations, novelfull) and Japanese raw novel sites (syosetu), with Playwright for JS-protected pages
2. **Metadata enrichment** — pulls rich metadata (author, genre, rating, cover, alternate title) from NovelUpdates with MangaUpdates as fallback
3. **EPUB/AZW3 output** — generates a properly structured ebook with cover, info page, and table of contents, then converts to AZW3 for Kindle
4. **JLPT furigana modes** — 7 modes for annotating Japanese kanji with reading aids based on JLPT level, so the same novel can be rebuilt for different study levels without re-downloading
5. **JSON archive** — chapters are saved locally before EPUB building, making downloads resumable and allowing full rebuild without re-scraping

---

## Planned Features (Roadmap)

These are confirmed future directions — build with these in mind:

1. **AI chapter summaries** — attach a brief summary to each chapter JSON; show in the ebook info section or as a sidebar. Lives in `services/ai.py`.
2. **AI translation pipeline** — translate Japanese chapters to English (or a study-mode hybrid). Would add a `translation` field to chapter JSON.
3. **Vocabulary extraction** — extract unknown vocabulary per chapter based on JLPT level. Potential study export (Anki-compatible).
4. **Proper CLI** — convert `lngrab.py` into a proper `lngrab` command using `argparse` or `click`, removing the interactive prompts.
5. **Send-to-Kindle automation** — email AZW3 to Kindle automatically after conversion.

---

## Out of Scope (Do Not Build Unless Explicitly Asked)

- Web UI or GUI
- Multi-user support
- Cloud sync or hosted storage
- Manga support (images only — no text to process)
- Native mobile app
- Admin dashboard

---

## Success Metrics

"Working well" means: a novel URL goes in → a clean, readable EPUB and AZW3 come out, with correct metadata and cover, in under a few minutes for a 100-chapter novel. Japanese novels additionally work with any of the 7 furigana modes without needing to re-download.

---

## Product Decisions & Rationale

| Decision | Rationale | Date |
|---|---|---|
| JSON files for chapter archive, not a database | Portable, zero-setup, easy to inspect and repair manually | Project start |
| URL slug as folder/filename (not the title) | Avoids Japanese character encoding issues on macOS filesystem | Project start |
| Calibre CLI for AZW3 conversion | Battle-tested, avoids reimplementing Kindle format | Project start |
| JLPT kanji data from KanjiTools project | Authoritative, community-maintained lists | Project start |
| 7 furigana modes as strings (not integers) | Readable in code and in JSON; safe to extend | Project start |
| Rebuild EPUB without re-downloading | Core UX requirement — changing furigana level should be fast | Project start |
| AI layer in services/ai.py (planned) | Keep AI calls isolated; never block the main pipeline on API failures | 2026-04-11 |

---

*Last updated: 2026-04-11*
