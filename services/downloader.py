import requests
import os
import json
from slugify import slugify
import time


def fetch_page(url: str, retries: int = 3, delay: float = 0.2) -> str:
    """
    Fetch a web page using requests with retry logic, delay, and a browser-like user agent.
    Used by metadata and source scrapers when a site can be accessed without Playwright.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Be polite: wait before next request
            time.sleep(delay)

            return response.text

        except requests.RequestException as e:
            print(f"Request failed (attempt {attempt+1}/{retries}): {url}")
            print(e)

            if attempt < retries - 1:
                time.sleep(2)
            else:
                raise


def create_novel_folder(title: str) -> str:
    """
    Create the output folder and chapters subfolder for a novel based on its title slug.
    Called by main.py before saving metadata, chapter JSON files, and generated ebooks.
    """
    slug = slugify(title)
    folder = os.path.join("output", slug)
    chapters_folder = os.path.join(folder, "chapters")

    os.makedirs(chapters_folder, exist_ok=True)

    return folder


def save_meta(folder: str, meta: dict):
    """
    Save novel metadata to meta.json inside the novel output folder.
    Used after metadata is fetched or reused so EPUB builds can read from a local source of truth.
    """
    path = os.path.join(folder, "meta.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def save_chapter(folder: str, index: int, chapter_data: dict):
    """
    Save a chapter as a JSON file using its index and a slugified title for readability.
    Called by the downloader loop after full chapter content has been fetched from a source.
    """
    safe_title = slugify(chapter_data.get("title") or f"chapter-{index}")
    filename = f"{index:04d} - {safe_title}.json"
    path = os.path.join(folder, "chapters", filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(chapter_data, f, indent=2, ensure_ascii=False)


def download_cover(folder: str, cover_url: str) -> str:
    """
    Download the cover image for a novel and save it as cover.jpg in the output folder.
    Used when metadata fetchers return a cover URL and the EPUB builder needs a local image file.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    response = requests.get(cover_url, headers=headers, timeout=30)
    response.raise_for_status()

    cover_path = os.path.join(folder, "cover.jpg")
    with open(cover_path, "wb") as f:
        f.write(response.content)

    return cover_path


def chapter_file_exists(folder: str, index: int) -> bool:
    """
    Check whether a chapter JSON file already exists for a given chapter index.
    Used to skip re-downloading chapters that are already present in the local archive.
    """
    chapters_folder = os.path.join(folder, "chapters")
    prefix = f"{index:04d}"

    if not os.path.isdir(chapters_folder):
        return False

    for filename in os.listdir(chapters_folder):
        if filename.startswith(prefix) and filename.endswith(".json"):
            return True

    return False
