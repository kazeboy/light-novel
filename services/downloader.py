import requests
import os
import json
from slugify import slugify
import time


def fetch_page(url: str, retries: int = 3, delay: float = 2.0) -> str:
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
    slug = slugify(title)
    folder = os.path.join("output", slug)
    chapters_folder = os.path.join(folder, "chapters")

    os.makedirs(chapters_folder, exist_ok=True)

    return folder


def save_meta(folder: str, meta: dict):
    path = os.path.join(folder, "meta.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def save_chapter(folder: str, index: int, chapter_data: dict):
    filename = f"{index:04d}.json"
    path = os.path.join(folder, "chapters", filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(chapter_data, f, indent=2, ensure_ascii=False)

def download_cover(folder: str, cover_url: str) -> str:
    import requests

    response = requests.get(cover_url, timeout=30)
    response.raise_for_status()

    cover_path = os.path.join(folder, "cover.jpg")
    with open(cover_path, "wb") as f:
        f.write(response.content)

    return cover_path

def chapter_file_exists(folder: str, index: int) -> bool:
    filename = f"{index:04d}.json"
    path = os.path.join(folder, "chapters", filename)
    return os.path.exists(path)