import sys
from sources.registry import get_source_for_url
from services.downloader import create_novel_folder, save_meta, save_chapter, download_cover, chapter_file_exists
from services.epub_builder import build_epub, build_epub_from_json, convert_epub_to_azw3
from sources.novelupdates import NovelUpdatesSource


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <novel_url>")
        return

    url = sys.argv[1]
    source = get_source_for_url(url)

    if source is None:
        print(f"Unknown source: {url}")
        return

    print(f"Source detected: {source.__class__.__name__}")

    print("Fetching novel metadata...")
    novel = source.get_novel_metadata(url)
    print(f"Title: {novel.title}")

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
        "author": "Kinosuke Naito",
        "description": "A man is reincarnated into another world and begins a slow farming life while building a village and community.",
    }
    # Try to fetch metadata from NovelUpdates
    nu = NovelUpdatesSource()
    nu_url = input("Enter NovelUpdates URL (or press Enter to skip): ").strip()

    if nu_url:
        try:
            nu_meta = nu.get_novel_metadata(nu_url)
            meta["author"] = nu_meta.author
            meta["description"] = nu_meta.description

            if nu_meta.cover_url:
                cover_path = download_cover(folder, nu_meta.cover_url)
                meta["cover_path"] = cover_path
            print("NovelUpdates metadata added.")
        except Exception as e:
            print(f"Could not fetch NovelUpdates metadata: {e}")
            print("Continuing without external metadata.")
    save_meta(folder, meta)

    download_limit_input = input("Download how many chapters? Press Enter for all: ").strip()

    if download_limit_input:
       download_limit = min(int(download_limit_input), len(chapters))
    else:
       download_limit = len(chapters)

    print(f"Preparing to process {download_limit} chapters...")

    downloaded_count = 0
    skipped_count = 0
    failed_count = 0

    for i, ch in enumerate(chapters[:download_limit], start=1):
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