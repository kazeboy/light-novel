from typing import List
from urllib.parse import urlparse, parse_qs, urljoin
import re

from bs4 import BeautifulSoup

from models.schemas import Novel, ChapterRef, ChapterContent
from sources.base import BaseSource
from services.downloader import fetch_page
from services.normalizer import clean_chapter_html


class SyosetuSource(BaseSource):
    """
    Source scraper for Syosetu / Narou web novel pages (`ncode.syosetu.com`).
    Used by the source registry when a user provides a direct Japanese web novel URL.
    """

    def matches(self, url: str) -> bool:
        """
        Return True when the given URL belongs to Syosetu / Narou.
        Used by the source registry to route `ncode.syosetu.com` links to this scraper.
        """
        return "ncode.syosetu.com" in url

    def _build_index_page_url(self, url: str, page_num: int) -> str:
        """
        Build the paginated index URL for a Syosetu series page.
        Page 1 is the base URL, while later pages use `?p=N`.
        """
        base = url.split("?", 1)[0].rstrip("/") + "/"
        if page_num == 1:
            return base
        return f"{base}?p={page_num}"

    def _extract_chapter_number(
        self, href: str, fallback_index: int | None = None
    ) -> float | None:
        """
        Extract the chapter number from a Syosetu chapter URL such as `/n3289ds/12/`.
        Falls back to the running index if needed.
        """
        match = re.search(r"/(\d+)/?$", href)
        if match:
            return float(match.group(1))
        if fallback_index is not None:
            return float(fallback_index)
        return None

    def get_novel_metadata(self, url: str) -> Novel:
        """
        Fetch the basic novel metadata from a Syosetu series page.
        Called early in the workflow before metadata enrichment and chapter downloading.
        """
        html = fetch_page(url)
        soup = BeautifulSoup(html, "lxml")

        title_tag = soup.find("h1")
        title = title_tag.get_text(" ", strip=True) if title_tag else "Unknown Title"

        author_tag = soup.select_one("a[href*='mypage.syosetu.com']")
        author = author_tag.get_text(" ", strip=True) if author_tag else None

        description = None
        description_container = soup.select_one("#novel_ex")
        if description_container:
            description = description_container.get_text("\n", strip=True)
        else:
            page_text = soup.get_text("\n", strip=True)
            if "●あらすじ" in page_text:
                description = (
                    page_text.split("●あらすじ", 1)[1]
                    .strip()
                    .split("最初へ", 1)[0]
                    .strip()
                )

        return Novel(
            title=title,
            author=author,
            description=description,
            cover_url=None,
            chapters=[],
        )

    def get_chapter_list(self, url: str) -> List[ChapterRef]:
        """
        Fetch and deduplicate the full chapter list from a Syosetu series page, including paginated index pages.
        Used by main.py to determine available chapters and decide which ones to download.
        """
        first_html = fetch_page(url)
        first_soup = BeautifulSoup(first_html, "lxml")

        max_page = 1
        for a in first_soup.find_all("a", href=True):
            href = a["href"]
            if "?p=" in href:
                parsed = urlparse(href)
                page_value = parse_qs(parsed.query).get("p")
                if page_value and page_value[0].isdigit():
                    max_page = max(max_page, int(page_value[0]))

        chapter_refs: List[ChapterRef] = []
        seen_urls = set()

        for page_num in range(1, max_page + 1):
            page_url = self._build_index_page_url(url, page_num)
            html = first_html if page_num == 1 else fetch_page(page_url)
            soup = first_soup if page_num == 1 else BeautifulSoup(html, "lxml")

            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                title = a.get_text(" ", strip=True)

                if not href or not title:
                    continue

                absolute_url = urljoin(url, href)
                parsed = urlparse(absolute_url)
                path_parts = [part for part in parsed.path.split("/") if part]

                # Expected chapter path format: /<series-code>/<chapter-number>/
                if len(path_parts) != 2:
                    continue

                _series_code, chapter_part = path_parts
                if not chapter_part.isdigit():
                    continue

                if absolute_url in seen_urls:
                    continue
                seen_urls.add(absolute_url)

                chapter_number = self._extract_chapter_number(
                    absolute_url, len(chapter_refs) + 1
                )
                chapter_refs.append(
                    ChapterRef(
                        title=title,
                        url=absolute_url,
                        chapter_number=chapter_number,
                    )
                )

        chapter_refs.sort(key=lambda ch: (ch.chapter_number or 0))
        return chapter_refs

    def get_chapter_content(self, chapter_url: str) -> ChapterContent:
        """
        Fetch and clean the full content of a single Syosetu chapter page.
        Used by the downloader loop before saving chapter JSON and rebuilding ebooks.
        """
        html = fetch_page(chapter_url)
        soup = BeautifulSoup(html, "lxml")

        title_tag = (
            soup.select_one(".p-novel__title")
            or soup.select_one(".novel_subtitle")
            or soup.find("h1")
        )
        title = title_tag.get_text(" ", strip=True) if title_tag else "Unknown Chapter"

        content_container = (
            soup.select_one("#novel_honbun")
            or soup.select_one(".p-novel__body")
            or soup.select_one(".js-novel-text")
        )

        if content_container is None:
            raise ValueError(
                f"Could not find chapter content container for {chapter_url}"
            )

        clean_html, clean_text = clean_chapter_html(content_container)
        chapter_number = self._extract_chapter_number(chapter_url)

        return ChapterContent(
            title=title,
            text=clean_text,
            html=clean_html,
            url=chapter_url,
            chapter_number=chapter_number,
        )
