# skill: debug-scraper
> Reusable Claude procedure for diagnosing and fixing scraping failures.
> Usage: "Execute the debug-scraper skill for [site / symptom description]"

---

## Role
You are a Python developer diagnosing a broken scraper in the light-novel pipeline.
Before touching any code, read `context/architecture.md` to understand where in the pipeline the failure is occurring.

## Input
A description of the failure. Examples:
- "novelfull.com chapters are downloading but the text is empty"
- "syosetu source returns 0 chapters"
- "metadata fetch always falls back to MangaUpdates now"

## Diagnostic Steps

### 1. Locate the failure in the pipeline
Identify which stage is broken:
- **Source detection** — `sources/registry.py` (wrong source matched, or no source matched)
- **Metadata fetch** — `source.get_novel_metadata()` or `services/metadata_fetcher.py`
- **Chapter list** — `source.get_chapter_list()`
- **Chapter content** — `source.get_chapter_content()`
- **HTML cleaning** — `services/normalizer.py`
- **EPUB build** — `services/epub_builder.py`
- **Furigana** — `services/furigana.py`

### 2. Inspect the raw HTML
Write a quick test snippet (do not modify production code yet) to fetch the page and print the raw HTML:

```python
import requests
from bs4 import BeautifulSoup

url = "https://..."
response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(response.text, "lxml")
print(soup.prettify()[:3000])
```

If the site requires JavaScript, use Playwright instead and check for login walls, CAPTCHAs, or dynamic content loading.

### 3. Check for structural changes
Compare the CSS selectors / HTML structure in the scraper against what's currently on the live page. Sites frequently change their DOM structure. Look for:
- Changed class names or IDs
- New wrapper elements
- Pagination changes
- Content moved behind login

### 4. Check the JSON archive
If chapters downloaded but the EPUB is wrong, inspect the raw JSON:

```bash
cat output/<source-slug>/chapters/0001.json
```

Check: Is `text` populated? Is `html` valid? Is `index` correct?

### 5. Isolate and fix
Make the minimal change needed in the relevant source file. Do not refactor unrelated code during a bug fix.

### 6. Verify
Run `python lngrab.py` with the failing URL. Confirm:
- Chapter count is correct
- At least 3 chapters download with non-empty text
- EPUB builds without error
- EPUB opens in Apple Books / Kindle Previewer if possible

## Constraints
- Fix only what's broken — don't restructure working scrapers during a debug session
- If a site has fundamentally changed (e.g. added mandatory login), document the limitation in the source file docstring rather than silently failing
- Never disable delays/rate limiting as a "fix"

## Output Format
1. Root cause diagnosis — which stage failed and why
2. The minimal code fix
3. Verification steps taken
4. Any site-specific notes to add to the source file docstring
