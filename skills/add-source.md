# skill: add-source
> Reusable Claude procedure for adding a new novel scraper source.
> Usage: "Execute the add-source skill for [site name / URL]"

---

## Role
You are a Python developer working on the light-novel scraper pipeline.
Before writing any code, read `context/conventions.md` and `context/architecture.md`.

## Input
A target website URL or site name to support. Example: "Add support for wuxiaworld.com"

## Steps

1. **Identify the site structure** — Inspect the URL pattern, chapter list page, and chapter content page HTML. Note whether JavaScript rendering is required (use Playwright) or plain HTML (use requests + BeautifulSoup).

2. **Create the source file** — Create `sources/<site_slug>.py`. The class name should be `<SiteName>Source` (PascalCase). Extend `BaseSource` and implement all four abstract methods:
   - `matches(url: str) -> bool` — return `True` if the domain/pattern matches
   - `get_novel_metadata(url: str) -> Novel` — return title, author, description, cover_url, and initial chapter list
   - `get_chapter_list(url: str) -> List[ChapterRef]` — return all chapters with title, url, and chapter_number
   - `get_chapter_content(chapter_url: str) -> ChapterContent` — return cleaned title, text, html, url, chapter_number

3. **Use the normalizer** — Pass raw HTML through `services/normalizer.py → clean_html()` before storing in `ChapterContent.html`. Do not invent your own HTML cleaning.

4. **Handle Playwright if needed** — If the site uses JavaScript, use Playwright's persistent browser context (follow the pattern in `sources/novelfull.py`). If requests + BeautifulSoup is sufficient, follow `sources/shmtranslations.py`.

5. **Register the source** — Add an instance of the new class to the `SOURCES` list in `sources/registry.py`. Order matters — more specific patterns should come before more general ones.

6. **Docstring every method** — One-liner: what it does + when it's called.

7. **Test manually** — Run `python lngrab.py` with a URL from the new site. Verify: metadata looks correct, chapter list is complete, at least one chapter downloads cleanly with readable text and HTML.

## Constraints
- No scraping logic inside `services/` — scrapers live in `sources/` only
- No EPUB or file-writing logic inside `sources/` — that lives in `services/`
- Add appropriate delays between requests (`time.sleep()`) to avoid hammering the server
- Handle missing/optional fields gracefully — `Optional[str]` fields in `Novel` and `ChapterContent` may be `None`
- If the site is metadata-only (like `novelupdates.py`), clearly document that in the class docstring

## Output Format
1. The new `sources/<site_slug>.py` file
2. The updated `sources/registry.py` (with the new source added to `SOURCES`)
3. A brief note on any site-specific quirks (login required, rate limiting, special encoding, etc.)
