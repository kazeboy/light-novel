from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChapterRef:
    """
    Lightweight reference to a chapter (title, URL, and chapter number).
    Used when building the chapter list before downloading full chapter content.
    """

    title: str
    url: str
    chapter_number: Optional[float] = None


@dataclass
class ChapterContent:
    """
    Full chapter content including cleaned text and original HTML.
    Returned by source scrapers and used for saving chapters to JSON and building EPUB files.
    """

    title: str
    text: str
    html: str
    url: str
    chapter_number: Optional[float] = None


@dataclass
class Novel:
    """
    Represents a novel and its basic metadata plus chapter list.
    Used when fetching novel information from a source before downloading chapters.
    """

    title: str
    author: Optional[str]
    description: Optional[str]
    cover_url: Optional[str]
    chapters: List[ChapterRef]
