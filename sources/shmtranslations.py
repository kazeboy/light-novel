from sources.base import BaseSource
from models.schemas import Novel, ChapterRef, ChapterContent
from typing import List
from services.downloader import fetch_page
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from services.normalizer import clean_chapter_html
import re


class ShmTranslationsSource(BaseSource):
    def matches(self, url: str) -> bool:
        return "shmtranslations.com" in url

    def get_novel_metadata(self, url: str) -> Novel:
        html = fetch_page(url)
        soup = BeautifulSoup(html, "lxml")

        title_tag = soup.find("h1")
        title = title_tag.text.strip() if title_tag else "Unknown Title"

        return Novel(
            title=title,
            author=None,
            description=None,
            cover_url=None,
            chapters=[]
        )

    def get_chapter_list(self, url: str) -> List[ChapterRef]:
        html = fetch_page(url)
        soup = BeautifulSoup(html, "lxml")

        chapter_links = []

        # SHM uses article list links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.text.strip()

            absolute_url = urljoin(url, href)

            if "chapter" in absolute_url.lower() and text:
                chapter_number = self._extract_chapter_number(text)
                chapter_links.append(
                    ChapterRef(
                        title=text,
                        url=absolute_url,
                        chapter_number=chapter_number
                    )
                )

        # Remove duplicates
        unique = {c.url: c for c in chapter_links}
        chapters = list(unique.values())

        # Sort chapters
        chapters.sort(key=lambda x: (x.chapter_number or 0))

        return chapters

    def get_chapter_content(self, chapter_url: str) -> ChapterContent:
        html = fetch_page(chapter_url)
        soup = BeautifulSoup(html, "lxml")

        title_tag = soup.find("h1")
        title = title_tag.get_text(" ", strip=True) if title_tag else "Unknown Chapter"

        content_container = (
            soup.select_one("article")
            or soup.select_one(".entry-content")
            or soup.select_one(".post-content")
            or soup.select_one(".td-post-content")
            or soup.select_one("main")
        )

        if content_container is None:
            raise ValueError(f"Could not find chapter content container for {chapter_url}")

        clean_html, clean_text = clean_chapter_html(content_container)

        chapter_number = self._extract_chapter_number(title)

        return ChapterContent(
            title=title,
            text=clean_text,
            html=clean_html,
            url=chapter_url,
            chapter_number=chapter_number,
        )

    def _extract_chapter_number(self, text: str):
        match = re.search(r"(\d+(\.\d+)?)", text)
        if match:
            return float(match.group(1))
        return None