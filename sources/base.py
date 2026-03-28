from abc import ABC, abstractmethod
from typing import List
from models.schemas import Novel, ChapterRef, ChapterContent


class BaseSource(ABC):
    """
    Abstract base class for all novel source scrapers.
    Each website (NovelFull, SHMTranslations, etc.) implements this interface so the main
    application can interact with different sources in a consistent way.
    """

    @abstractmethod
    def matches(self, url: str) -> bool:
        """
        Return True if this source can handle the given URL.
        Used by the source registry to select the correct scraper for a URL.
        """
        pass

    @abstractmethod
    def get_novel_metadata(self, url: str) -> Novel:
        """
        Fetch basic novel metadata such as title, author, description, cover, and chapter list.
        Called at the start of the process before downloading chapters.
        """
        pass

    @abstractmethod
    def get_chapter_list(self, url: str) -> List[ChapterRef]:
        """
        Return a list of ChapterRef objects for all chapters available on the site.
        Used to determine which chapters need to be downloaded.
        """
        pass

    @abstractmethod
    def get_chapter_content(self, chapter_url: str) -> ChapterContent:
        """
        Download and return the full content of a single chapter.
        Used by the downloader when fetching chapters.
        """
        pass
