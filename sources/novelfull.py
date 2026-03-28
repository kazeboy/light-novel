from typing import List
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from models.schemas import Novel, ChapterRef, ChapterContent
from sources.base import BaseSource
from services.downloader import fetch_page
import re
from urllib.parse import urljoin, urlparse, urlunparse
import atexit


class NovelFullSource(BaseSource):
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        atexit.register(self.close)

    def _ensure_context(self):
        if self._context is not None:
            return self._context

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._context = self._browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        return self._context

    def _fetch_html_persistent(self, url: str, wait_selector: str | None = None) -> str:
        context = self._ensure_context()
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=5000)
                except Exception:
                    pass
            else:
                page.wait_for_timeout(800)
            return page.content()
        finally:
            page.close()

    def _fetch_html_once(self, url: str, wait_selector: str | None = None) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1440, "height": 900},
                locale="en-US",
            )
            page = context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                if wait_selector:
                    try:
                        page.wait_for_selector(wait_selector, timeout=5000)
                    except Exception:
                        pass
                else:
                    page.wait_for_timeout(800)
                return page.content()
            finally:
                context.close()
                browser.close()

    def close(self):
        if self._context is not None:
            self._context.close()
            self._context = None
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def matches(self, url: str) -> bool:
        return "novelfull.com" in url

    def _normalize_chapter_url(self, base_url: str, href: str) -> str:
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        normalized_path = parsed.path.rstrip("/") or "/"
        return urlunparse((parsed.scheme, parsed.netloc, normalized_path, "", "", ""))

    def get_novel_metadata(self, url: str) -> Novel:
        html = self._fetch_html_once(url, "h3.title")

        soup = BeautifulSoup(html, "lxml")

        title = "Unknown Title"
        author = None
        description = None
        cover_url = None

        title_tag = soup.select_one("h3.title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        author_tag = soup.select_one("a[href*='/author/']")
        if author_tag:
            author = author_tag.get_text(strip=True)

        desc_tag = soup.select_one("#tab-description")
        if desc_tag:
            description = desc_tag.get_text(" ", strip=True)

        cover_tag = soup.select_one(".book img")
        if cover_tag and cover_tag.get("src"):
            cover_url = cover_tag["src"]

        return Novel(
            title=title,
            author=author,
            description=description,
            cover_url=cover_url,
            chapters=[],
        )

    def get_chapter_list(self, url: str) -> List[ChapterRef]:
        chapter_refs = []
        seen_urls = set()
        seen_keys = set()

        html = self._fetch_html_persistent(url, "ul.list-chapter")
        soup = BeautifulSoup(html, "lxml")

        max_page = 1
        for a in soup.select('a[href*="?page="]'):
            href = a.get("href", "")
            match = re.search(r"[?&]page=(\d+)", href)
            if match:
                max_page = max(max_page, int(match.group(1)))

        for page_num in range(1, max_page + 1):
            page_url = url if page_num == 1 else f"{url}?page={page_num}"
            page_html = self._fetch_html_persistent(page_url, "ul.list-chapter")
            page_soup = BeautifulSoup(page_html, "lxml")

            for a in page_soup.select("ul.list-chapter li a"):
                title = a.get_text(strip=True)
                href = a.get("href")

                if not href or not title:
                    continue

                chapter_url = self._normalize_chapter_url(url, href)

                match = re.search(r"Chapter\s+(\d+(?:\.\d+)?)", title, re.IGNORECASE)
                if match:
                    chapter_number = float(match.group(1))
                else:
                    chapter_number = float(len(chapter_refs) + 1)

                title_key = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
                chapter_key = (chapter_number, title_key)

                if chapter_url in seen_urls or chapter_key in seen_keys:
                    continue

                seen_urls.add(chapter_url)
                seen_keys.add(chapter_key)

                chapter_refs.append(
                    ChapterRef(
                        title=title,
                        url=chapter_url,
                        chapter_number=chapter_number,
                    )
                )

        chapter_refs.sort(key=lambda ch: ch.chapter_number)
        return chapter_refs

    def get_chapter_content(self, chapter_url: str) -> ChapterContent:
        html = self._fetch_html_persistent(chapter_url, "#chapter-content")

        soup = BeautifulSoup(html, "lxml")

        title = "Unknown Chapter"
        title_tag = soup.select_one("a.chapter-title")
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            title_tag = soup.select_one("h3.chapter-title")
            if title_tag:
                title = title_tag.get_text(strip=True)

        content_tag = soup.select_one("#chapter-content")
        if not content_tag:
            content_tag = soup.select_one("div#chapter-content")

        if not content_tag:
            raise ValueError(
                f"Could not find chapter content on NovelFull page: {chapter_url}"
            )

        for bad in content_tag.select(
            "script, style, noscript, iframe, .ads, .chapter-notification, .chapter-notice, .notice, .report, img"
        ):
            bad.decompose()

        for centered in content_tag.select('div[align="center"], p[align="center"]'):
            centered.decompose()

        embedded_title = content_tag.select_one("h3.chapter-title, a.chapter-title")
        if embedded_title:
            embedded_title.decompose()

        for heading in content_tag.find_all(["h1", "h2", "h3", "h4"]):
            heading_text = heading.get_text(" ", strip=True)
            lowered_heading = heading_text.lower()
            if lowered_heading.startswith("chapter "):
                heading.decompose()

        for node in content_tag.find_all(["div", "p", "span"]):
            node_text = node.get_text(" ", strip=True)
            lowered = node_text.lower()
            if (
                "if you find any errors" in lowered
                or "report chapter" in lowered
                or "ads popup" in lowered
                or "ads redirect" in lowered
                or "broken links" in lowered
            ):
                node.decompose()
                continue

            if not node_text and not node.find(["br"]):
                node.decompose()

        raw_html = str(content_tag)
        text = content_tag.get_text("\n", strip=True)

        chapter_number = 0.0
        match = re.search(r"Chapter\s+(\d+(?:\.\d+)?)", title, re.IGNORECASE)
        if match:
            chapter_number = float(match.group(1))

        return ChapterContent(
            title=title,
            chapter_number=chapter_number,
            url=chapter_url,
            text=text,
            html=raw_html,
        )
