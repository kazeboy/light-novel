import sys
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
            fetched_metadata = None
    else:
        nu_result = None
        fetched_metadata = None
        print("No NovelUpdates matches found.")

    print("Fetching chapter list...")
    chapters = source.get_chapter_list(url)
    print(f"Total chapters found: {len(chapters)}")

    if not chapters:
        print("No chapters found.")
        return

    folder = create_novel_folder(novel.title)
    print(f"Saving to folder: {folder}")

    meta = {
        "title": novel.title,
        "source_url": url,
        "total_chapters": len(chapters),
    }

    if fetched_metadata:
        meta.update({k: v for k, v in fetched_metadata.items() if v})

        if fetched_metadata.get("cover_url"):
            try:
                cover_path = download_cover(folder, fetched_metadata["cover_url"])
                meta["cover_path"] = cover_path
                print(f"Cover downloaded to: {cover_path}")
            except Exception as e:
                print(f"Could not download cover: {e}")

    save_meta(folder, meta)

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