import sys
import os
import json
from slugify import slugify
from sources.registry import get_source_for_url
from services.downloader import create_novel_folder, save_meta, save_chapter, chapter_file_exists, download_cover
from services.epub_builder import build_epub_from_json, convert_epub_to_azw3
from services.metadata_fetcher import derive_search_title, resolve_metadata, search_novelupdates_results, choose_novelupdates_result, fetch_novelupdates_metadata

def parse_chapter_range(range_input: str, total_chapters: int):
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
    return os.path.join("output", slugify(novel_title))


def get_existing_novel_info(folder: str) -> dict:
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
    meta = existing_info.get("meta") or {}
    print("\nExisting novel detected")
    print(f"Title: {meta.get('title', 'Unknown')}" )
    print(f"Author: {meta.get('author', 'Unknown')}" )
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
    url = input("Novel URL: ").strip()

    if not url:
       print("No URL provided.")
       return
    source = get_source_for_url(url)

    if source is None:
        print(f"Unknown source: {url}")
        return

    print(f"Source detected: {source.__class__.__name__}")

    print("Fetching novel metadata...")
    novel = source.get_novel_metadata(url)
    print(f"Title: {novel.title}")
    folder = get_novel_folder_path(novel.title)
    existing_info = get_existing_novel_info(folder)
    action = None

    if existing_info["exists"]:
        action = choose_existing_novel_action(existing_info)
        if action == "4":
            print("Cancelled.")
            return

    fetched_metadata = None

    if not existing_info["exists"]:
        search_title = derive_search_title(novel.title, url)
        print(f"Search title: {search_title}")
        resolved_metadata = resolve_metadata(search_title)
        print(f"Metadata title: {resolved_metadata['title']}")
        nu_results = search_novelupdates_results(search_title)
        print(f"NovelUpdates results found: {len(nu_results)}")

        if nu_results:
            nu_result = choose_novelupdates_result(nu_results)
            print(f"NovelUpdates chosen result: {nu_result}")

            if nu_result:
                fetched_metadata = fetch_novelupdates_metadata(nu_result)
                print(f"Fetched title: {fetched_metadata['title']}")
                print(f"Fetched author: {fetched_metadata['author']}")
                print(f"Fetched cover URL: {fetched_metadata['cover_url']}")
        else:
            print("No NovelUpdates matches found.")
    else:
        print("Skipping metadata fetch because this novel already exists locally.")

    print("Fetching chapter list...")
    chapters = source.get_chapter_list(url)
    print(f"Total chapters found: {len(chapters)}")

    if not chapters and action != "3":
        print("No chapters found.")
        return

    folder = create_novel_folder(novel.title)
    print(f"Saving to folder: {folder}")

    meta = {
        "title": novel.title,
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
            start_ch = existing_max + 1 if existing_max < len(chapters) else len(chapters) + 1
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