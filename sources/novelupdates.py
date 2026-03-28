from sources.base import BaseSource
from models.schemas import Novel, ChapterRef, ChapterContent
from typing import List
from services.downloader import fetch_page
from bs4 import BeautifulSoup


class NovelUpdatesSource(BaseSource):
    """
    Source scraper for NovelUpdates series pages.
    Used mainly for metadata extraction when a user provides a NovelUpdates URL directly.
    """

    def matches(self, url: str) -> bool:
        """
        Return True when the given URL belongs to NovelUpdates.
        Used by the source registry to route novelupdates.com links to this scraper.
        """
        return "novelupdates.com" in url

    def get_novel_metadata(self, url: str) -> Novel:
        """
        Fetch basic metadata from a NovelUpdates series page such as title, author, description, and cover.
        Used when a NovelUpdates URL is provided directly or as a metadata source.
        """
        html = fetch_page(url)
        soup = BeautifulSoup(html, "lxml")

        title_tag = soup.find("div", class_="seriestitlenu")
        title = title_tag.text.strip() if title_tag else "Unknown Title"

        author = None
        description = None
        cover_url = None

        # Author
        author_tag = soup.find("div", id="showauthors")
        if author_tag:
            author = author_tag.text.strip()

        # Description
        desc_tag = soup.find("div", id="editdescription")
        if desc_tag:
            description = desc_tag.text.strip()

        # Cover
        cover_tag = soup.find("img", class_="seriesimg")
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
        """
        Chapter list scraping is not implemented for NovelUpdates because this source is used for metadata only.
        Left unimplemented intentionally.
        """
        raise NotImplementedError()

    def get_chapter_content(self, chapter_url: str) -> ChapterContent:
        """
        Chapter content scraping is not implemented for NovelUpdates because this source is used for metadata only.
        Left unimplemented intentionally.
        """
        raise NotImplementedError()
