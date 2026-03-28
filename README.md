# Light Novel Downloader & Ebook Builder

## Status

This project is under active development and is primarily designed for personal use and learning purposes.  
Features and supported sites may change over time.

A Python tool that downloads web novels and light novels from online translation sites, cleans the content, and builds EPUB and Kindle (AZW3) ebooks automatically.

This project is designed as a learning project, but it is structured like a real content pipeline.

## Features

Current features:

- Detect supported source websites
- Fetch novel metadata (title, author, description, alternative titles, genre, rating, year, status, country of origin) with fallback from NovelUpdates to MangaUpdates
- Download cover image
- Fetch chapter lists (with duplicate chapter detection and removal)
- Download chapters using persistent browser sessions when needed (Playwright for protected sites)
- Clean HTML content
- Save chapters as JSON as a local archive (source of truth)
- Skip already downloaded chapters
- Build EPUB from the local JSON archive
- Embed cover and full metadata into EPUB (including custom info page)
- Convert EPUB to AZW3 for Kindle
- Japanese text processing with optional furigana
- JLPT-based kanji filtering (N5 → N1 and non-JLPT kanji modes)
- Rebuild EPUB/AZW3 with different furigana levels without re-downloading chapters
- Resume downloads safely
- Retry failed requests
- Add delays between requests to avoid hammering websites

## Project Structure

```
light-novel/
├── main.py                 # Main program
├── config.py               # Configuration placeholder
├── README.md
├── .gitignore
├── data/
│   └── jlpt_kanji/         # JLPT kanji lists (N5–N1)
├── models/                 # Data models
│   └── schemas.py
├── sources/                # Website scrapers
│   ├── base.py
│   ├── registry.py
│   ├── shmtranslations.py
│   ├── syosetu.py
│   ├── novelupdates.py
│   └── mangaupdates.py
├── services/               # Core services
│   ├── downloader.py
│   ├── normalizer.py
│   ├── epub_builder.py
│   ├── ordering.py
│   ├── furigana.py         # Furigana generator and JLPT kanji filtering
│   └── metadata_fetcher.py
├── output/                 # Downloaded novels
│   └── <source-slug>/      # Folder name based on source URL
│       ├── meta.json
│       ├── cover.jpg
│       ├── chapters/
│       │   ├── 0001.json
│       │   ├── 0002.json
│       │   └── ...
│       ├── <source-slug>.epub
│       └── <source-slug>.azw3
└── temp/                   # Temporary files
```

## How It Works

```
Pipeline:

Website → Scraper / Browser (Playwright when needed) → Cleaner → JSON Archive
                                                              ↓
                                                Metadata (NovelUpdates → MangaUpdates fallback)
                                                              ↓
                                                         Cover Download
                                                              ↓
                                              EPUB Builder → Furigana Processor (optional)
                                                              ↓
                                                         AZW3 (Kindle)
```

When working with Japanese novels, the EPUB builder can optionally add furigana (reading aid) above kanji. Furigana can be generated for all kanji or filtered based on JLPT levels (for example, only show furigana for kanji above JLPT N3). This allows the same novel to be rebuilt multiple times for different reading levels without re-downloading chapters.

### Metadata Fetching

Metadata is fetched using a fallback system:

1. The tool first searches NovelUpdates and lets the user select a result.
2. If NovelUpdates is skipped or no result is found, it automatically searches MangaUpdates.
3. The first successful metadata source is used.
4. Metadata includes title, author, description, alternative titles, genre, year, status, and cover image when available.
5. The folder name and file names are based on the source URL slug, not the novel title, to avoid filesystem and encoding issues.

This fallback system improves metadata reliability and cover availability across different novels.

## Requirements

- Python 3.10+
- Calibre, for EPUB to AZW3 conversion
- Python packages:
  - requests
  - beautifulsoup4
  - lxml
  - ebooklib
  - python-slugify
  - playwright
  - janome

Install Python packages with:

    pip install requests beautifulsoup4 lxml ebooklib python-slugify playwright janome

Check Calibre CLI with:

    ebook-convert --version

If needed on macOS, add Calibre to PATH with:

    export PATH="$PATH:/Applications/calibre.app/Contents/MacOS"

Install Playwright browsers with:

    playwright install

## Usage

Run the tool with:

    python lngrab.py

You will then be prompted to enter the novel URL and chapter range interactively.

Example:

    python lngrab.py

Already downloaded chapters are skipped automatically.

### Furigana and JLPT Mode (Japanese Novels)

When building EPUB files for Japanese novels, the tool can generate furigana automatically.

You will be prompted to choose a furigana mode:

1. No furigana
2. Furigana for all kanji
3. Furigana above JLPT N5
4. Furigana above JLPT N4
5. Furigana above JLPT N3
6. Furigana above JLPT N2
7. Furigana for non-JLPT kanji only

This allows you to create graded reading material depending on your Japanese level.

## Output

For each novel, the script creates:

    output/<source-slug>/
    ├── meta.json          # Title, author, description, cover path, etc.
    ├── cover.jpg
    ├── chapters/          # Raw cleaned chapter archive
    ├── <source-slug>.epub
    └── <source-slug>.azw3

The folder name is based on the source website URL (slug), and the EPUB/AZW3 filenames are also based on the same slug for consistency and filesystem-safe naming. The official book title and other metadata are embedded inside the EPUB/AZW3 metadata instead.

## Japanese Text Support

This project supports Japanese web novels (for example from syosetu.com).

To ensure Japanese characters display correctly on macOS Books and Kindle:

- All JSON files are saved using UTF-8 encoding.
- EPUB files are generated with UTF-8 HTML and `<html lang="ja">` when the source is Japanese.
- The folder name and EPUB filename are based on the source URL slug instead of the Japanese title to avoid encoding and filesystem issues.
- The original Japanese title and author are stored in metadata and embedded into the EPUB file.

This allows reading Japanese novels directly on Kindle or Apple Books while keeping proper metadata and cover images.

JLPT kanji lists are used to control furigana display. The kanji lists are sourced from the Kanji Tools project: https://github.com/kanjitools/kanji

## Supported Sources

Current support:

- shmtranslations.com (chapter source)
- novelfull.com (chapter source - Playwright)
- syosetu.com (Japanese raw novels)
- novelupdates.com (primary metadata source)
- mangaupdates.com (fallback metadata source)

The system is designed so new sources can be added easily via the source registry and scraper interface.

## Future Improvements

Planned ideas:

- Turn the project into a proper CLI tool (`lngrab` command)
- Better metadata and cover download
- Additional novel sites
- GUI interface
- Send-to-Kindle automation
- AI chapter summaries
- Translation pipeline
- Web interface for library management

## Disclaimer

This project is for personal use and educational purposes.
Please support original authors and translators by visiting their websites.

## Author

Personal learning project by Rooz.

## Architecture Diagram

Below is a high-level overview of how the system works internally.

![Architecture Diagram](docs/architecture.png)

This diagram shows the flow from source websites → scrapers → cleaning → JSON archive → EPUB/AZW3 builder.
