from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChapterRef:
    title: str
    url: str
    chapter_number: Optional[float] = None


@dataclass
class ChapterContent:
    title: str
    text: str
    html: str
    url: str
    chapter_number: Optional[float] = None


@dataclass
class Novel:
    title: str
    author: Optional[str]
    description: Optional[str]
    cover_url: Optional[str]
    chapters: List[ChapterRef]