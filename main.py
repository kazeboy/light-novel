import sys
import os
import json
from slugify import slugify
from sources.registry import get_source_for_url
from services.downloader import (
    create_novel_folder,
    save_meta,
    save_chapter,
    chapter_file_exists,
    download_cover,
)
from services.epub_builder import build_epub_from_json, convert_epub_to_azw3
from services.metadata_fetcher import (
    derive_search_title,
    fetch_metadata_with_fallbacks,
)
from urllib.parse import urlparse


def parse_chapter_range(range_input: str, total_chapters: int):
    """
    Parse user input such as `50`, `15-55`, `500-`, or `-100` into a start/end chapter index range.
    Used by main() when the user chooses a custom download range.
    """
    range_input = range_input.strip()

    if not range_input:
        return 1, total_chapters

    if "-" not in range_input:
        end = min(int(range_input), total_chapters)
        return 1, end

    start_str, end_str = range_input.split("-", 1)

    start = int(start_str) if start_str else 1
    end = int(end_str) if end_str else total_chapters

    start = max(1, start)
    end = min(total_chapters, end)

    if start > end:
        start, end = end, start

    return start, end


def get_novel_folder_path(novel_title: str) -> str:
    """
    Build the output folder path from a novel title using a slugified name.
    Kept as a helper for title-based folder paths when needed elsewhere in the project.
    """
    return os.path.join("output", slugify(novel_title))


def get_novel_folder_path_from_url(url: str) -> str:
    """
    Build the expected output folder path directly from the source URL slug.
    Used to detect existing novels before fetching source metadata again.
    """
    parsed = urlparse(url)
    slug = parsed.path.rstrip("/").split("/")[-1]
    if slug.endswith(".html"):
        slug = slug[:-5]
    return os.path.join("output", slugify(slug))


def get_existing_novel_info(folder: str) -> dict:
    """
    Inspect an existing novel folder and return stored metadata plus chapter index statistics.
    Used by main() to decide whether a novel already exists locally and what actions are available.
    """
    info = {
        "exists": False,
        "meta": None,
        "chapter_count": 0,
        "min_index": None,
        "max_index": None,
    }

    if not os.path.isdir(folder):
        return info

    info["exists"] = True

    meta_path = os.path.join(folder, "meta.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            info["meta"] = json.load(f)

    chapters_folder = os.path.join(folder, "chapters")
    if os.path.isdir(chapters_folder):
        indexes = []
        for filename in os.listdir(chapters_folder):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(chapters_folder, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "index" in data and isinstance(data["index"], int):
                    indexes.append(data["index"])
            except Exception:
                continue

        if indexes:
            info["chapter_count"] = len(indexes)
            info["min_index"] = min(indexes)
            info["max_index"] = max(indexes)

    return info


def choose_existing_novel_action(existing_info: dict) -> str:
    """
    Display the existing-novel action menu and return the user's choice.
    Used when a local archive already exists so the user can update, rebuild, or cancel.
    """
    meta = existing_info.get("meta") or {}
    print("\nExisting novel detected")
    print(f"Title: {meta.get('title', 'Unknown')}")
    print(f"Author: {meta.get('author', 'Unknown')}")
    print(f"Saved chapters: {existing_info.get('chapter_count', 0)}")

    min_index = existing_info.get("min_index")
    max_index = existing_info.get("max_index")
    if min_index is not None and max_index is not None:
        print(f"Chapter range in archive: {min_index} to {max_index}")

    print("\nChoose an action:")
    print("  1. Download missing/new chapters")
    print("  2. Download a custom range")
    print("  3. Rebuild EPUB/AZW3 only")
    print("  4. Cancel")

    while True:
        choice = input("Action: ").strip()
        if choice in {"1", "2", "3", "4"}:
            return choice
        print("Invalid choice. Enter 1, 2, 3, or 4.")


def main():
    """
    Orchestrate the full novel workflow from URL input to metadata enrichment, chapter download, EPUB build, and AZW3 conversion.
    This is the main entry point used by lngrab.py when the application is run interactively.
    """
    url = input("Novel URL: ").strip()

    if not url:
        print("No URL provided.")
        return
    source = get_source_for_url(url)

    if source is None:
        print(f"Unknown source: {url}")
        return

    print(f"Source detected: {source.__class__.__name__}")

    folder = get_novel_folder_path_from_url(url)
    existing_info = get_existing_novel_info(folder)
    action = None
    novel = None
    fetched_metadata = None

    if existing_info["exists"]:
        print(
            "Skipping source metadata fetch because this novel already exists locally."
        )
        existing_meta = existing_info.get("meta") or {}
        existing_title = existing_meta.get("title", "Unknown Title")
        print(f"Title: {existing_title}")
        action = choose_existing_novel_action(existing_info)
        if action == "4":
            print("Cancelled.")
            return
        novel_title = existing_title
    else:
        print("Fetching novel metadata...")
        novel = source.get_novel_metadata(url)
        print(f"Title: {novel.title}")
        novel_title = novel.title

        search_title = derive_search_title(novel.title, url)
        print(f"Search title: {search_title}")
        fetched_metadata = fetch_metadata_with_fallbacks(search_title)
        print(f"Metadata source: {fetched_metadata.get('metadata_source')}")
        if fetched_metadata.get("title"):
            print(f"Fetched title: {fetched_metadata['title']}")
        if fetched_metadata.get("author"):
            print(f"Fetched author: {fetched_metadata['author']}")
        if fetched_metadata.get("cover_url"):
            print(f"Fetched cover URL: {fetched_metadata['cover_url']}")

    chapters = []
    if action != "3":
        print("Fetching chapter list...")
        chapters = source.get_chapter_list(url)
        print(f"Total chapters found: {len(chapters)}")

        if not chapters:
            print("No chapters found.")
            return
    else:
        print("Skipping chapter list fetch (rebuild only mode).")

    folder = create_novel_folder(novel_title)
    print(f"Saving to folder: {folder}")

    meta = {
        "title": novel_title,
        "source_url": url,
        "total_chapters": len(chapters),
    }

    if existing_info["exists"] and existing_info.get("meta"):
        meta.update({k: v for k, v in existing_info["meta"].items() if v})
    elif fetched_metadata:
        meta.update({k: v for k, v in fetched_metadata.items() if v})

        if fetched_metadata.get("cover_url"):
            try:
                cover_path = download_cover(folder, fetched_metadata["cover_url"])
                meta["cover_path"] = cover_path
                print(f"Cover downloaded to: {cover_path}")
            except Exception as e:
                print(f"Could not download cover: {e}")

    save_meta(folder, meta)

    if action == "3":
        print("Skipping chapter download and rebuilding outputs only.")
        chapters = []
        start_ch = None
        end_ch = None
    else:
        if action == "1":
            existing_max = existing_info.get("max_index") or 0
            start_ch = (
                existing_max + 1 if existing_max < len(chapters) else len(chapters) + 1
            )
            end_ch = len(chapters)
            print(f"Processing missing/new chapters from {start_ch} to {end_ch}...")
        else:
            range_input = input(
                "Enter chapter range:\n"
                "  Press Enter = all chapters\n"
                "  50 = chapters 1 to 50\n"
                "  15-55 = chapters 15 to 55\n"
                "  500- = chapter 500 to end\n"
                "  -100 = start to chapter 100\n"
                "Range: "
            )
            start_ch, end_ch = parse_chapter_range(range_input, len(chapters))
            print(f"Processing chapters {start_ch} to {end_ch}...")

    downloaded_count = 0
    skipped_count = 0
    failed_count = 0

    for i, ch in enumerate(chapters, start=1):
        if start_ch is None or end_ch is None:
            continue
        if i < start_ch or i > end_ch:
            continue

        if chapter_file_exists(folder, i):
            print(f"Skipping chapter {i}: already exists")
            skipped_count += 1
            continue

        print(f"Downloading chapter {i}: {ch.title}")

        try:
            chapter = source.get_chapter_content(ch.url)

            chapter_data = {
                "index": i,
                "chapter_number": chapter.chapter_number,
                "title": chapter.title,
                "source_url": chapter.url,
                "text": chapter.text,
                "html": chapter.html,
            }

            save_chapter(folder, i, chapter_data)
            downloaded_count += 1

        except Exception as e:
            print(f"Failed chapter {i}: {ch.title}")
            print(f"Error: {e}")
            failed_count += 1

    print("\nDownload summary:")
    print(f"Downloaded: {downloaded_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Failed: {failed_count}")

    print("Building EPUB...")
    epub_path = build_epub_from_json(folder)
    print(f"EPUB created: {epub_path}")
    print("Converting EPUB to AZW3...")
    try:
        azw3_path = convert_epub_to_azw3(epub_path)
        print(f"AZW3 created: {azw3_path}")
    except Exception as e:
        print(f"Could not create AZW3: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
